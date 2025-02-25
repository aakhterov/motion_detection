from abc import ABC, abstractmethod

class IStreamer(ABC):
    """
    Interface to handle video files.
    TODO
    """

    @abstractmethod
    def process_url(self, video_url: str):
        raise NotImplementedError("Subclasses must implement process_url method")