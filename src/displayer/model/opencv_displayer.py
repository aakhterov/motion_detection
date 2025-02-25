import cv2
import pika
import json
import os
import logging
from collections import deque
import time


from src.config import Configuration
from src.displayer.interface.displayer import IDisplayer

DEFAULT_DETECTION_QUEUE = "detections"
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

class OpenCVDisplayer(IDisplayer):
    def __init__(self, configuration: Configuration):
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

    def play(self, buffer_size=10, fps=25):
        connection, detections_queue = self.__initialize_rabbitmq_connection(self.detections_queue_name)
        detections_queue.queue_declare(queue=self.detections_queue_name, durable=True)
        buffer = deque(maxlen=buffer_size)
        delay = 1 / fps
        next_frame_time = time.time()

        def callback(ch, method, properties, body):
            nonlocal next_frame_time

            message = json.loads(body)
            frame_path = message.get('frame_path')

            frame = cv2.imread(frame_path)
            if frame is None:
                logging.error(f"Could not open frame {frame_path}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            buffer.append(frame)

            if len(buffer) >= buffer_size:
                if time.time() >= next_frame_time:
                    frame_to_show = buffer.popleft()
                    cv2.imshow('Playback', frame_to_show)
                    next_frame_time += delay

                    # Allow time for frame display
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        detections_queue.stop_consuming()
                        return

            ch.basic_ack(delivery_tag=method.delivery_tag)

        detections_queue.basic_qos(prefetch_count=1)
        detections_queue.basic_consume(queue=self.detections_queue_name, on_message_callback=callback)

        print(f"Waiting for frames on {self.detections_queue_name}.")
        try:
            detections_queue.start_consuming()
        except KeyboardInterrupt:
            logging.info("Stopping video playback...")
        finally:
            connection.close()
            cv2.destroyAllWindows()




