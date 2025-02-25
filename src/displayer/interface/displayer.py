from abc import ABC, abstractmethod

class IDisplayer(ABC):
    """
    Interface to play a video and blur detections.
    TODO
    """

    @abstractmethod
    def play(self, buffer_size=10, fps=25):
        raise NotImplementedError("Subclasses must implement play method")