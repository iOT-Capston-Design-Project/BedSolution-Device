import time

class BoardData:
    def __init__(self, board: str, receive_time: time, data: dict):
        self.board = board
        self.receive_time = receive_time
        self.data = data

    def __str__(self):
        return f"BoardData(board={self.board}, receive_time={self.receive_time}, data={self.data})"