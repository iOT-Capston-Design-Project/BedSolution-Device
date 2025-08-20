from typing import List, Tuple
import numpy as np

class FrameBuffer:
    def __init__(self, max_size: int):
        self.maxSize = max(1, max_size)
        self.buf_head: List[np.ndarray] = []
        self.buf_body: List[np.ndarray] = []

    def push(self, head: np.ndarray, body: np.ndarray):
        self.buf_head.append(head)
        self.buf_body.append(body)
        if len(self.buf_head) > self.maxSize:
            self.buf_head.pop(0)
            self.buf_body.pop(0)

    def get_avg(self) -> Tuple[np.ndarray, np.ndarray]:
        H = np.mean(self.buf_head, axis=0)
        B = np.mean(self.buf_body, axis=0)
        return H, B