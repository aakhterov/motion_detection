# import os
# import logging
#
# from src.displayer.model.opencv_displayer import OpenCVDisplayer
# from src.config import Configuration
#
# logging.basicConfig(level=logging.INFO)
# configuration = Configuration(os.path.join(os.getcwd(), "config.json"))
#
# detector = OpenCVDisplayer(configuration)
# detector.play()

import os

from fastapi.responses import StreamingResponse
from fastapi import FastAPI

from src.config import Configuration
from src.displayer.model.opencv_displayer import OpenCVDisplayer

configuration = Configuration(os.path.join(os.getcwd(), "config.json"))
displayer = OpenCVDisplayer(configuration)

app = FastAPI()

@app.get("/video", response_class=StreamingResponse)
def video_stream():
    return StreamingResponse(displayer.play(), media_type='multipart/x-mixed-replace; boundary=frame')


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=True)