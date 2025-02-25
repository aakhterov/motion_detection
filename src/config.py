import json
from typing import Dict

from pydantic import BaseModel

class Configuration(BaseModel):
    """
    Configuration class that loads and stores settings from a JSON config file.

    Attributes:
        rabbitmq (Dict): Configuration settings for RabbitMQ
        root_folder (str): Root folder to store extracted images
    Args:
        path_to_config (str): Path to JSON configuration file
    """
    rabbitmq: Dict
    root_folder: str

    def __init__(self, path_to_config: str):
        with open(path_to_config, encoding="utf-8", mode="r") as f:
            data = json.load(f)
        super().__init__(**data)