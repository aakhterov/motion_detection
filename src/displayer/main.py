import logging

from src.displayer.model.opencv_displayer import OpenCVDisplayer
from src.config import Configuration

logging.basicConfig(level=logging.INFO)
configuration = Configuration("../../config.json")

detector = OpenCVDisplayer(configuration)
detector.play()



