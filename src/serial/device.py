import time

class Device:
    def __init__(self, device: str, port: str, receive_time: time, data):
        self.port = port
        self.receive_time = receive_time
        self.data = data