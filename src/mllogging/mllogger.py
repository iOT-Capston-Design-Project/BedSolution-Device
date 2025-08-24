import numpy as np
from mllogging.heatmap_log import HeatmapLog
from datetime import datetime
import csv
import os

class MLLogger:
    def __init__(self, log_file_path="heatmap_log.csv"):
        self.buffer = []
        self.log_file_path = log_file_path
    
    def log_heatmap(self, head: np.ndarray, body: np.ndarray):
        self.buffer.append(HeatmapLog(datetime.now(), head, body))

    def save(self):
        if not self.buffer:
            return None
        
        file_exists = os.path.exists(self.log_file_path)
        
        try:
            with open(self.log_file_path, 'w', newline='', encoding='utf-8') as csvfile:
                first_log = self.buffer[0]
                first_dict = first_log.to_dict()
                
                fieldnames = ['timestamp']
                head_size = len(first_dict['heatmap']['head'])

                for i in range(head_size):
                    fieldnames.append(f'head_{i}')
                
                body_size = len(first_dict['heatmap']['body'])
                for i in range(body_size):
                    fieldnames.append(f'body_{i}')
                
                if not file_exists:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                
                for heatmap_log in self.buffer:
                    log_dict = heatmap_log.to_dict()
                    row_data = {
                        'timestamp': log_dict['timestamp']
                    }
                    for i, value in enumerate(log_dict['heatmap']['head']):
                        row_data[f'head_{i}'] = value
                    for i, value in enumerate(log_dict['heatmap']['body']):
                        row_data[f'body_{i}'] = value
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(row_data)
            
            self.buffer.clear()
            return self.log_file_path
            
        except Exception as e:
            raise
    