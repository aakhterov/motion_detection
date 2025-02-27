import re
import os
from typing_extensions import Annotated
from fastapi import FastAPI, BackgroundTasks, status
from pydantic import BaseModel, AfterValidator

from src.streamer.controller.controller import Controller
from src.config import Configuration
from src.streamer.model.opencv_streamer import OpenCVStreamer

configuration = Configuration(os.path.join(os.getcwd(), "config.json"))
streamer = OpenCVStreamer(configuration)
controller = Controller(streamer)

app = FastAPI()

HTTPS_URL_PATTERN = re.compile("^https:\/\/\S+$")

def check_url(url: str) -> str:
    if not bool(HTTPS_URL_PATTERN.fullmatch(url)):
        raise ValueError(f"Invalid URL: {url}")
    return url

class SubmitData(BaseModel):
    video_url: Annotated[str, AfterValidator(check_url)]

def start_processing(video_url):
    controller.process_url(video_url)


@app.post("/submit", status_code=status.HTTP_202_ACCEPTED)
def submit_data(data: SubmitData, bg_task: BackgroundTasks):
    bg_task.add_task(start_processing, data.video_url)
    return "OK"