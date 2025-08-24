import numpy as np
from datetime import date

class HeatmapLog:
    def __init__(self, date: date, head: np.ndarray, body: np.ndarray):
        self.head = head
        self.body = body
        self.date = date

    def to_dict(self):
        result = {
            'timestamp': self.date.isoformat(),
            'heatmap': {
                'head': [],
                'body': [],
            }
        }
        # Head
        for row in range(self.head.shape[0]):
            for col in range(self.head.shape[1]):
                result['heatmap']['head'].append(self.head[row, col])
        # Body
        for row in range(self.body.shape[0]):
            for col in range(self.body.shape[1]):
                result['heatmap']['body'].append(self.body[row, col])
        return result