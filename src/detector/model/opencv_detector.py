import cv2
import pika
import json
import os
import logging

from src.config import Configuration
from src.detector.interface.detector import IDetector

DEFAULT_FRAMES_QUEUE = "frames"
DEFAULT_DETECTION_QUEUE = "detections"
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

class OpenCVDetector(IDetector):
    def __init__(self, configuration: Configuration):
        self.frames_queue_name = configuration.rabbitmq.get("frames_queue", DEFAULT_FRAMES_QUEUE)
        self.detections_queue_name = configuration.rabbitmq.get("detections_queue", DEFAULT_DETECTION_QUEUE)
        self.host = configuration.rabbitmq.get("host", "localhost")
        self.port = configuration.rabbitmq.get("port", 5672)

    def __initialize_rabbitmq_connection(self, queue: str):
        connection =  pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      port=self.port,
                                      heartbeat=0,
                                      credentials=pika.credentials.PlainCredentials(username=RABBITMQ_USER,
                                                                                    password=RABBITMQ_PASS))
        )
        channel = connection.channel()
        channel.queue_declare(queue=queue, durable=True)
        return connection, channel

    def process_images(self):
        connection, frames_queue = self.__initialize_rabbitmq_connection(self.frames_queue_name)
        _, detections_queue = self.__initialize_rabbitmq_connection(self.detections_queue_name)

        def callback(ch, method, properties, body):
            message = json.loads(body)
            frame_path = message.get('frame_path')
            frame_number = message.get('frame_number')

            current_frame = cv2.imread(frame_path)
            if current_frame is None:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                raise ValueError(f"Unable to read image {frame_path}")

            nonlocal previous_frame, previous_frame_path
            if previous_frame is not None:
                gray_a = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)
                gray_b = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
                diff_frame = cv2.absdiff(gray_a, gray_b)
                _, motion_frame = cv2.threshold(diff_frame, 25, 255, cv2.THRESH_BINARY)
                motion_intensity = cv2.countNonZero(motion_frame)
                motion_detected = motion_intensity > 500

                motion_data = {
                    'frame_number': frame_number,
                    'frame_path': frame_path,
                    'motion_detected': motion_detected,
                    'motion_intensity': motion_intensity
                }

                detections_queue.basic_publish(
                    exchange='',
                    routing_key=self.detections_queue_name,
                    body=json.dumps(motion_data),
                    properties=pika.BasicProperties(delivery_mode=2)
                )

            previous_frame = current_frame
            previous_frame_path = frame_path

            ch.basic_ack(delivery_tag=method.delivery_tag)

        previous_frame = None
        previous_frame_path = None

        frames_queue.basic_qos(prefetch_count=1)
        frames_queue.basic_consume(queue=self.frames_queue_name, on_message_callback=callback)

        logging.info(f"Waiting for messages in {self.frames_queue_name}.")
        try:
            frames_queue.start_consuming()
        except KeyboardInterrupt:
            logging.info("Stopping motion detection...")
        finally:
            connection.close()