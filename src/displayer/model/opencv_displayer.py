from time import sleep

import cv2
import pika
import json
import os
import logging
import time
import threading
from collections import deque
from datetime import datetime
from typing import List, Tuple, Generator

from pika.adapters.blocking_connection import BlockingChannel

from src.config import Configuration
from src.displayer.interface.displayer import IDisplayer

DEFAULT_DETECTION_QUEUE = "detections"
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

class OpenCVDisplayer(IDisplayer):
    """
    A class for displaying video frames with motion detection visualization using OpenCV.

    This class implements the IDisplayer interface and handles:
    - Connection to RabbitMQ for receiving frame messages
    - Display of video frames with motion detection boxes
    - Blurring of detected motion regions
    - Timestamp overlay on frames
    - Frame buffering for smooth playback

    Attributes:
        detections_queue_name (str): Name of the RabbitMQ queue for receiving frame messages
        host (str): Hostname of the RabbitMQ server
        port (int): Port number of the RabbitMQ server
    """

    def __init__(self, configuration: Configuration, buffer_size: int = 10, fps: int = 25):
        self.detections_queue_name = configuration.rabbitmq.get("detections_queue", DEFAULT_DETECTION_QUEUE)
        self.host = configuration.rabbitmq.get("host", "localhost")
        self.port = configuration.rabbitmq.get("port", 5672)
        self.buffer_size = buffer_size
        self.buffer = deque()
        self.delay = 1 / fps
        self.detections_queue = None

    def __initialize_rabbitmq_connection(self, queue: str) -> Tuple[pika.BlockingConnection, BlockingChannel]:
        """
        Initializes a connection to RabbitMQ and creates a channel.

        Args:
            queue (str): Name of the queue to declare

        Returns:
            Tuple[pika.BlockingConnection, BlockingChannel]: A tuple containing:
                - The BlockingConnection object for the RabbitMQ connection
                - The BlockingChannel object for communicating with RabbitMQ
        """
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

    def __callback(self, ch, method, properties, body):

        message = json.loads(body)
        frame_path = message.get('frame_path')
        motion_detected = message.get('motion_detected')
        contours = message.get('contours')

        frame = cv2.imread(frame_path)
        if frame is None:
            logging.error(f"Could not open frame {frame_path}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if motion_detected:
            for contour in contours:
                x, y, w, h = contour
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                frame = self.__blur_rectangle(frame, (x, y), (x + w, y + h))
        frame = self.__display_datetime(frame)

        self.buffer.append(frame)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __blur_rectangle(self, frame, top_left, bottom_right) -> List[List[int]]:
        """
        Applies Gaussian blur to a rectangular region of the input frame.

        Args:
            frame: Input image frame as numpy array
            top_left: Tuple of (x,y) coordinates for top left corner of rectangle
            bottom_right: Tuple of (x,y) coordinates for bottom right corner of rectangle

        Returns:
            frame: The input frame with the specified rectangular region blurred

        The method:
            1. Extracts the region of interest (ROI) from the frame using the coordinates
            2. Applies Gaussian blur with kernel size (21,21) to the ROI
            3. Places the blurred ROI back into the original frame
        """
        x1, y1 = top_left
        x2, y2 = bottom_right
        roi = frame[y1:y2, x1:x2]

        blurred_roi = cv2.GaussianBlur(roi, (21, 21), 0)

        frame[y1:y2, x1:x2] = blurred_roi

        return frame

    def __display_datetime(self, frame):
        """
        Adds a timestamp overlay to the video frame.

        Args:
            frame: The video frame (numpy array) to add the timestamp to

        Returns:
            The frame with timestamp text overlay added in white color at position (10,30)
            using OpenCV's putText function
        """
        text = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        return cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    def __consumer(self):
        connection, self.detections_queue = self.__initialize_rabbitmq_connection(self.detections_queue_name)
        self.detections_queue.queue_declare(queue=self.detections_queue_name, durable=True)
        self.detections_queue.basic_qos(prefetch_count=1)
        self.detections_queue.basic_consume(
            queue=self.detections_queue_name,
            on_message_callback=self.__callback
        )

        self.detections_queue.start_consuming()

        connection.close()

    def play(self) -> Generator[bytes, None, None]:
        # connection, self.detections_queue = self.__initialize_rabbitmq_connection(self.detections_queue_name)
        # self.detections_queue.queue_declare(queue=self.detections_queue_name, durable=True)
        # self.detections_queue.basic_qos(prefetch_count=1)
        # self.detections_queue.basic_consume(
        #     queue=self.detections_queue_name,
        #     on_message_callback=self.__callback
        # )
        # self.detections_queue.start_consuming()

        consumer_thread = threading.Thread(target=self.__consumer)
        consumer_thread.start()
        # consumer_thread.join()

        next_frame_time = time.time()
        sleep(3)
        while len(self.buffer) >= self.buffer_size:
            if time.time() >= next_frame_time:
                frame = self.buffer.popleft()
                if frame is None:
                    continue
                # _, jpeg_frame = cv2.imencode('.jpg', frame)
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n'
                next_frame_time += self.delay



    def stop(self):
        if self.detections_queue is not None:
            self.detections_queue.stop_consuming()

    # def process_image(self):
    #     connection, detections_queue = self.__initialize_rabbitmq_connection(self.detections_queue_name)
    #     detections_queue.queue_declare(queue=self.detections_queue_name, durable=True)
    #     # next_frame_time = time.time()
    #
    #     def callback(ch, method, properties, body):
    #         # nonlocal next_frame_time
    #
    #         message = json.loads(body)
    #         frame_path = message.get('frame_path')
    #         motion_detected = message.get('motion_detected')
    #         contours = message.get('contours')
    #
    #         frame = cv2.imread(frame_path)
    #         if frame is None:
    #             logging.error(f"Could not open frame {frame_path}")
    #             ch.basic_ack(delivery_tag=method.delivery_tag)
    #             return
    #
    #         if motion_detected:
    #             for contour in contours:
    #                 x, y, w, h = contour
    #                 cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #                 frame = self.__blur_rectangle(frame, (x, y), (x + w, y + h))
    #         frame = self.__display_datetime(frame)
    #
    #         self.buffer.append(frame)
    #
    #         # if len(buffer) >= buffer_size:
    #         #     if time.time() >= next_frame_time:
    #         #         frame_to_show = buffer.popleft()
    #         #         if motion_detected:
    #         #             for contour in contours:
    #         #                 x, y, w, h = contour
    #         #                 cv2.rectangle(frame_to_show, (x, y), (x + w, y + h), (0, 255, 0), 2)
    #         #                 frame_to_show = self.__blur_rectangle(frame_to_show, (x, y), (x + w, y + h))
    #         #         frame_to_show = self.__display_datetime(frame_to_show)
    #         #         cv2.imshow('Playback', frame_to_show)
    #         #
    #         #         next_frame_time += delay
    #         #
    #         #         if cv2.waitKey(1) & 0xFF == ord('q'):
    #         #             detections_queue.stop_consuming()
    #         #             return
    #
    #         ch.basic_ack(delivery_tag=method.delivery_tag)
    #
    #     detections_queue.basic_qos(prefetch_count=1)
    #     detections_queue.basic_consume(queue=self.detections_queue_name, on_message_callback=callback)
    #
    #     # logging.info(f"Waiting for frames on {self.detections_queue_name}.")
    #     # try:
    #     #     detections_queue.start_consuming()
    #     # except KeyboardInterrupt:
    #     #     logging.info("Stopping video playback...")
    #     # finally:
    #     #     connection.close()
    #     #     cv2.destroyAllWindows()


