import re

from src.streamer.interfaces.streamer import IStreamer

HTTPS_URL_PATTERN = re.compile("^https:\/\/\S+$") # e.g. https://drive.google.com/uc?export=download&id=1wIP-u-Cv5vqeNH9AXkrQbkrRc8NXe2XQ

class Controller:

    def __init__(self, model: IStreamer):
        self.model = model

    def __check_url(self, url: str) -> bool:
        return bool(HTTPS_URL_PATTERN.fullmatch(url))

    def process_url(self, url: str):
        if not self.__check_url(url):
            raise ValueError(f"Invalid URL: {url}")

        self.model.process_url(url)

