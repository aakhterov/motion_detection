from abc import ABC, abstractmethod

class IDisplayer(ABC):
    """
    Interface to play a video and blur detections.
    """

    @abstractmethod
    def play(self):
        raise NotImplementedError("Subclasses must implement play method")