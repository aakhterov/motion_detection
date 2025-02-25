#!/usr/bin/env python
import argparse
from src.streamer.controller.controller import Controller


class CLIInterface:

    def __init__(self, controller: Controller):
        self.controller = controller
        self.parser = argparse.ArgumentParser(description="GitHub Analyzer Command-Line Interface")
        self.parser.add_argument("-v", "--video", help="A video file URL")

    def run(self):
        args = self.parser.parse_args()

        try:
            print(f"The Video file is being processed: {args.video}")

            if args.video is not None:
                self.controller.process_url(args.video)

            print(f"Video processed: {args.video}")
        except Exception as e:
            print(f"ERROR: Error processing video file: {e}")


if __name__ == "__main__":

    from src.config import Configuration
    from src.streamer.model.opencv_streamer import OpenCVStreamer

    configuration = Configuration("config.json")
    streamer = OpenCVStreamer(configuration)
    controller  = Controller(streamer)

    cli = CLIInterface(controller)
    cli.run()




