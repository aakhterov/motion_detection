import re

from src.streamer.interfaces.streamer import IStreamer

HTTPS_URL_PATTERN = re.compile("^https:\/\/\S+$") # e.g. https://drive.google.com/uc?export=download&id=1wIP-u-Cv5vqeNH9AXkrQbkrRc8NXe2XQ

class Controller:
    """
    Controller class for handling URL processing.

    This class validates and processes HTTPS URLs by delegating to a model
    that implements the IStreamer interface.

    Attributes:
        model (IStreamer): The model instance used for processing URLs
    """

    def __init__(self, model: IStreamer):
        self.model = model

    def __check_url(self, url: str) -> bool:
        """
        Validates if the provided URL matches the HTTPS URL pattern.

        Args:
            url (str): The URL string to validate

        Returns:
            bool: True if URL matches HTTPS pattern, False otherwise
        """
        return bool(HTTPS_URL_PATTERN.fullmatch(url))

    def process_url(self, url: str):
        """
        Process a URL by validating it and passing it to the model for processing.

        Args:
            url (str): The URL to process. Must be a valid HTTPS URL.

        Raises:
            ValueError: If the URL is invalid or does not match the HTTPS pattern.
        """
        if not self.__check_url(url):
            raise ValueError(f"Invalid URL: {url}")

        self.model.process_url(url)
