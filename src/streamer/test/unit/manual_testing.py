import logging

from src.streamer.model.opencv_streamer import OpenCVStreamer
from src.config import Configuration

logging.basicConfig(level=logging.INFO)
configuration = Configuration("../../../../config.json")

streamer = OpenCVStreamer(configuration)
# URL = "example.mp4"
URL = "https://drive.google.com/uc?export=download&id=1wIP-u-Cv5vqeNH9AXkrQbkrRc8NXe2XQ"
streamer.process_url(video_url=URL)



