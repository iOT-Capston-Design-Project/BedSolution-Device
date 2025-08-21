from typing import Dict, List, Optional, Tuple
import numpy as np
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

from detection.config import DetectionConfig

class PressureHeatmap:
    def __init__(self, config: DetectionConfig):
        self.config = config

    def _rgb_hex(self, r,g,b): return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _colormap_rgb(self, x):
        t = 0.0 if self.config.value_max <= self.config.value_min else max(0,0, min(1.0, (x-self.config.value_min)/(self.config.value_max-self.config.value_min)))
        if t < 0.33:
            a = t/0.33; r,g,b = 0, int(255*a), 255 # Blue
        elif t < 0.66:
            a = (t-0.33)/0.33; r,g,b = 0, int(255*a), 255 # Yellow
        else:
            a = (t-0.66)/0.34; r,g,b = 255, int(255*(1-a)), 0 # Red
        return r,g,b

    def _boundary_mask(self, threshold: np.ndarray) -> np.ndarray:
        r,c = threshold.shape
        mask = np.zeros_like(threshold, dtype=bool)
        for i in range(r):
            for j in range(c):
                if not threshold[i, j]: continue
                for (y, x) in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]:
                    if y < 0 or y>=r or x<0 or x>=c or not threshold[y, x]:
                        mask[i,j] = True
                        break
        return mask
        
    def _overlay_heatmap(self, head, shoulder, hip, heels):
        ov = {}
        if head is not None:
            r,c,_ = head; ov[(int(round(r)), int(round(c)))] = ("H", "bold white")
        sr,sc,_ = shoulder; ov[(int(round(sr)), int(round(sc)))] = ("S", "bold white")
        hr,hc,_ = hip; ov[(int(round(hr)), int(round(hc)))] = ("P", "bold white")
        for r,c,_ in heels:
            ov[(int(round(r)), int(round(c)))] = ("L", "bold white")
        return ov

    def _merge_head_body(self, head: np.ndarray, body: np.ndarray, fill_value: float = 0.0) -> Tuple[np.ndarray, int]:
        if head.ndim != 2 or body.ndim != 2:
            raise ValueError("head와 body는 2차원 numpy 배열이어야 합니다.")

        head_rows, head_cols = head.shape
        body_rows, body_cols = body.shape

        merged_cols = max(head_cols, body_cols)

        # 필요한 경우 좌/우 패딩하여 열 수 정렬
        if head_cols < merged_cols:
            pad_width = ((0, 0), (0, merged_cols - head_cols))
            head_padded = np.pad(head, pad_width, mode='constant', constant_values=fill_value)
        else:
            head_padded = head

        if body_cols < merged_cols:
            pad_width = ((0, 0), (0, merged_cols - body_cols))
            body_padded = np.pad(body, pad_width, mode='constant', constant_values=fill_value)
        else:
            body_padded = body

        merged = np.vstack([head_padded, body_padded])
        return merged, head_rows
    
    def _adjust_overlays_with_row_offset(self, overlays: Dict[Tuple[int, int], Tuple[str, str]], row_offset: int) -> Dict[Tuple[int, int], Tuple[str, str]]:
        adjusted = {}
        for (r,c), (sym, fgstyle) in overlays.items():
            adjusted[(r+row_offset, c)] = (sym, fgstyle)
        return adjusted

    def _render(self, head: np.ndarray, body: np.ndarray, overlays: Dict[Tuple[int, int], Tuple[str, str]], threshold: float) -> Panel:
        merged, row_offset = self._merge_head_body(head, body)
        overlays = self._adjust_overlays_with_row_offset(overlays, row_offset)
        thr = (merged >= threshold)
        boundary = self._boundary_mask(thr)

        cell_w = 2
        table = Table.grid(padding=0)
        for r in range(merged.shape[0]):
            row_text = Text()
            for c in range(merged.shape[1]):
                val = float(merged[r,c])
                cr, cg, cb = self._colormap_rgb(val)
                bg = self._rgb_hex(cr, cg, cb)

                ch = " "*cell_w
                style = f"on {bg}"

                if boundary[r,c]:
                    ch = "▣" + (" "*(cell_w-1) if cell_w>1 else "")
                    style = f"white on {bg}"
                
                if (r, c) in overlays:
                    sym, fgstyle = overlays[(r,c)]
                    ch = sym + (" "*(cell_w-1) if cell_w>1 else "")
                    style = f"{fgstyle} on {bg}"

                row_text.append(Text(ch, style=style))

            table.add_row(row_text)
        return Panel(table, title="Heatmap", padding=(0, 0), box=box.SQUARE)

    # Draw heatmap to console
    def render(self,
               H: np.ndarray, B: np.ndarray,
               head: Optional[Tuple[float, float, float]], 
               shoulder: Tuple[float, float, float], 
               hip: Tuple[float, float, float], 
               heels: List[Tuple[float, float, float]],
               threshold: float) -> Panel:
        overlays = self._overlay_heatmap(head, shoulder, hip, heels)
        panel = self._render(H, B, overlays, threshold)
        return panel
        