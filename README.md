1. The system is made up of three components, called "Streamer", "Detector" and "Displayer". 
2. Video_url -> Streamer service -> RabbitMQ queue #1 -> Detector service -> RabbitMQ queue #2 -> Displayer service
3. A flow:
   - A Streamer service write images to the local folder and send paths to the RabbitMQ queue #1
   - A Detector service is a consumer for the RabbitMQ queue #1 and producer for the RabbitMQ queue #2
   - A Displayer service is a consumer for the RabbitMQ queue #2