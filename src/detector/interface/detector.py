from abc import ABC, abstractmethod

class IDetector(ABC):
    """
    Interface to detect motions.
    TODO
    """

    @abstractmethod
    def process_images(self):
        raise NotImplementedError("Subclasses must implement process_images method")