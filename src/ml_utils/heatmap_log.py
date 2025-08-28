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
        result['heatmap']['head'] = self.head.tolist()
        result['heatmap']['body'] = self.body.tolist()
        return result