import cv2
import os
import pika
import json
import logging
from uuid import uuid4

from src.config import Configuration
from src.streamer.interfaces.streamer import IStreamer

DEFAULT_QUEUE = "frames"
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

class OpenCVStreamer(IStreamer):

    def __init__(self, configuration: Configuration):
        self.root_folder = configuration.root_folder
        self.queue = configuration.rabbitmq.get("frames_queue", DEFAULT_QUEUE)
        self.host = configuration.rabbitmq.get("host", "localhost")
        self.port = configuration.rabbitmq.get("port", 5672)

    def __initialize_rabbitmq_connection(self):
        return pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host,
                                      port=self.port,
                                      heartbeat=0,
                                      credentials=pika.credentials.PlainCredentials(username=RABBITMQ_USER,
                                                                                    password=RABBITMQ_PASS))
        )

    def process_url(self, video_url: str):

        logging.info(f"Processing video from {video_url}")

        output_folder = os.path.join(self.root_folder, str(uuid4()))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        logging.info(f"Output folder: {output_folder}")

        video_capture = cv2.VideoCapture(video_url)
        if not video_capture.isOpened():
            # logging.error(f"Cannot open video from {video_url}")
            raise ValueError(f"Cannot open video from {video_url}")

        connection = self.__initialize_rabbitmq_connection()
        channel = connection.channel()
        channel.queue_declare(queue=self.queue, durable=True)

        frame_count = 0
        success = True
        while success:
            success, frame = video_capture.read()
            if success:
                frame_filename = f"frame_{frame_count:06d}.jpg"
                frame_path = os.path.join(output_folder, frame_filename)

                cv2.imwrite(frame_path, frame)

                message = {
                    'frame_number': frame_count,
                    'frame_path': frame_path,
                }
                channel.basic_publish(
                    exchange='',
                    routing_key=self.queue,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                    )
                )

                frame_count += 1

        video_capture.release()
        connection.close()

        logging.info(f"Extracted and sent {frame_count} frames to RabbitMQ.")
