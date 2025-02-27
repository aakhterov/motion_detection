import os
import logging

from src.detector.model.opencv_detector import OpenCVDetector
from src.config import Configuration

logging.basicConfig(level=logging.INFO)
configuration = Configuration(os.path.join(os.getcwd(), "config.json"))

detector = OpenCVDetector(configuration)
detector.process_images()