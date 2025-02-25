import cv2
import pika
import json
import os
import logging
import imutils

from src.config import Configuration
from src.detector.interface.detector import IDetector

DEFAULT_FRAMES_QUEUE = "frames"
DEFAULT_DETECTION_QUEUE = "detections"
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

class OpenCVDetector(IDetector):
    """
    Motion detector implementation using OpenCV and RabbitMQ.

    This class processes video frames from a RabbitMQ queue to detect motion by comparing
    consecutive frames using OpenCV image processing techniques. When motion is detected,
    the results are published to a separate RabbitMQ queue.

    Attributes:
        frames_queue_name (str): Name of the RabbitMQ queue for receiving frames
        detections_queue_name (str): Name of the RabbitMQ queue for publishing detections
        host (str): RabbitMQ server hostname
        port (int): RabbitMQ server port number

    The motion detection algorithm:
    - Converts frames to grayscale
    - Calculates absolute difference between consecutive frames
    - Applies thresholding and dilation
    - Finds and filters contours to identify motion regions
    """

    def __init__(self, configuration: Configuration):
        self.frames_queue_name = configuration.rabbitmq.get("frames_queue", DEFAULT_FRAMES_QUEUE)
        self.detections_queue_name = configuration.rabbitmq.get("detections_queue", DEFAULT_DETECTION_QUEUE)
        self.host = configuration.rabbitmq.get("host", "localhost")
        self.port = configuration.rabbitmq.get("port", 5672)

    def __initialize_rabbitmq_connection(self, queue: str):
        """
        Initialize a connection to RabbitMQ and create a channel.

        Args:
            queue (str): Name of the queue to declare

        Returns:
            tuple: (connection, channel) - The RabbitMQ connection and channel objects

        The connection is established using the configured host and port with the following settings:
        - Heartbeat disabled (set to 0)
        - Uses plain credentials from RABBITMQ_USER and RABBITMQ_PASS environment variables
        - Creates a durable queue with the specified name
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

    def process_images(self):
        """
        Process images from RabbitMQ queue for motion detection.

        This method:
        1. Establishes connections to RabbitMQ for frames and detections queues
        2. Sets up a callback to process incoming frame messages
        3. For each frame:
           - Reads the image from disk
           - Compares with previous frame to detect motion using OpenCV
           - Identifies motion contours above minimum size threshold
           - Publishes motion detection results to detections queue
        4. Handles graceful shutdown on keyboard interrupt

        The motion detection:
        - Converts frames to grayscale
        - Calculates absolute difference between consecutive frames
        - Applies thresholding and dilation
        - Finds and filters contours to identify motion regions

        Messages published to detection queue include:
        - Frame number and path
        - Boolean indicating if motion was detected
        - List of contour coordinates (x,y,w,h) for motion regions

        Raises:
            ValueError: If unable to read an image file
        """
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
                _, thresh = cv2.threshold(diff_frame, 25, 255, cv2.THRESH_BINARY)

                thresh = cv2.dilate(thresh, None, iterations=2)
                cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
                cnts = imutils.grab_contours(cnts)
                contours = []
                for c in cnts:
                    # if the contour is too small, ignore it
                    if cv2.contourArea(c) < 500:
                        continue
                    (x, y, w, h) = cv2.boundingRect(c)
                    contours.append((x, y, w, h))

                motion_data = {
                    'frame_number': frame_number,
                    'frame_path': frame_path,
                    'motion_detected': bool(contours),
                    'contours': contours
                }

                detections_queue.basic_publish(
                    exchange='',
                    routing_key=self.detections_queue_name,
                    body=json.dumps(motion_data),
                    properties=pika.BasicProperties(delivery_mode=2)
                )

            if os.path.split(frame_path)[1] == "frame_000000.jpg":
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