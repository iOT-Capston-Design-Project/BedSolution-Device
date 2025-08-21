from numpy.lib.stride_tricks import sliding_window_view
import numpy as np
from typing import Tuple, Dict, Optional, List
import math, time, csv
from dataclasses import asdict
from enum import Enum
from detection.config import DetectionConfig
from detection.frame_buffer import FrameBuffer

class TorsoParts(Enum):
    HEAD = 0
    SHOULDERS = 1   
    LEFT_ARM = 2
    RIGHT_ARM = 3
    HIPS = 4
    LEFT_LEG = 5
    RIGHT_LEG = 6

class Posture(Enum):
    SUPINE = 0 # 정자세
    LEFT_LATERAL = 1 # 좌측 측면
    RIGHT_LATERAL = 2 # 우측 측면
    PRONE = 3 # 엎드림

class Detection:
    def __init__(self, config: DetectionConfig):
        self.config = config
        self.frame_buffer = FrameBuffer(config.moving_avg_N)
        self._init_log()

    # ML학습용 로그 초기화 (헤더 포함)
    def _init_log(self):
        with open(self.config.log_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["ts", "threshold", "head_row", "head_col", "head_score", "shoulder_row", "shoulder_col", "shoulder_score", "hip_row", "hip_col", "hip_score", "heel_row", "heel_col", "heel_score"]+list(asdict(self.config).keys()))

    def _add_log(self):
        pass

    # 적응형 임계값
    def _adaptive_threshold(self, head: np.ndarray, body: np.ndarray) -> float:
        x = np.concatenate([head.flatten(), body.flatten()])
        x = x[np.isfinite(x)]
        x = np.clip(x, self.config.value_min, self.config.value_max)
        return float(np.percentile(x, self.config.percentile_p))

    # 2x2 블록 합
    def _sum2x2(self, x: np.ndarray) -> float:
        win = sliding_window_view(x, (2, 2))
        return win.sum(axis=(-1, -2))

    # 최대값 위치
    def _argmax2d(self, x: np.ndarray) -> Tuple[int, int]:
        idx = np.argmax(x)
        return divmod(idx, x.shape[1])

    # 블록 중심 좌표
    def _centroid_from_block(self, r: int, c: int) -> Tuple[float, float]:
        return (r + 0.5, c + 0.5)

    # 행과 열의 최대값 위치
    def _row_col_max(self, x: np.ndarray) -> Tuple[int, int]:
        r = int(np.argmax(x.sum(axis=1)))
        c = int(np.argmax(x.sum(axis=0)))
        return r, c

    # 몸통 부분 탐지
    def _detect_torso_parts(self, body: np.ndarray, threshold: float, min_activated: int = 3) -> Dict:
        sum = self._sum2x2(body)

         # TODO: 임계값을 이용 활성화된 셀 파악

        f_r, f_c = self._argmax2d(sum) # 2x2 블록 합의 최대값 위치
        r_max, c_max = self._row_col_max(body) # 행과 열의 최대값 위치

        # 포함 여부
        overlaps_row = (f_r == r_max)
        overlaps_col = (f_c == c_max)

        torso_h, torso_w = body.shape # 몸통 크기
        upper_th = math.floor((torso_h-1) * 0.5) # 상단 절반 경계
        block_center_r, block_center_c = self._centroid_from_block(f_r, f_c) # 최대값 블록 중심 좌표

        part = TorsoParts.SHOULDERS if block_center_r > upper_th else TorsoParts.HIPS
        # 부위 마스크
        mask = np.zeros_like(body, dtype=bool)
        mask[f_r:f_r+2, f_c:f_c+2] = True
        score = float(sum[f_r, f_c])
        return {
            "part_hint": part,
            "block_rc": (f_r, f_c),
            "center_rc": (block_center_r, block_center_c),
            "max_rc": (r_max, c_max),
            "overlaps": (overlaps_row, overlaps_col),
            "score": score,
            "mask": mask,
            "sum": sum,
        }

    # Return (row, col, score) if detected, None if not
    def _detect_head(self, head: np.ndarray, threshold: float) -> Optional[Tuple[int, int, int]]:
        x = head.copy()
        x[x < threshold] = 0.0
        if np.all(~np.isfinite(x)):
            return None
        r, c = self._argmax2d(x)
        return (r, c, float(x[r, c]))
    
    def _detect_heel(self, body: np.ndarray, threshold: float) -> List[Tuple[float, float, float]]:
        if self.config.heel_search_rows < 1: return []
        rows = slice(body.shape[0]-self.config.heel_search_rows, body.shape[0])
        mask = body[rows, :].copy()
        mask[mask < threshold] = 0.0

        # 열별 최댓값
        vals = mask.max(axis=0)
        rows_idx = mask.argmax(axis= 0)
        candidates = [(rows.start+int(rows_idx[c]), c, float(vals[c])) for c in range(mask.shape[1]) if vals[c] > 0.0]
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[:2]

    def _detect_posture(self, head: Optional[Tuple[float, float, float]], shoulder: Tuple[float, float, float], hip: Tuple[float, float, float], threshold: float) -> Posture:
        cols = []
        if head is not None: cols.append(head[1])
        cols.append(shoulder[1])
        cols.append(hip[1])
        if len(cols) >= 3:
            spread = (max(cols)-min(cols)) # 좌우 편차 계산
            if spread < self.config.upright_tolerance_cells:
                label = Posture.SUPINE
            else:
                delta = shoulder[1]-hip[1]
                label = Posture.LEFT_LATERAL if delta < 0 else Posture.RIGHT_LATERAL
        else:
            # No head
            delta = shoulder[1]-hip[1]
            label = Posture.LEFT_LATERAL if abs(delta) >= self.config.upright_tolerance_cells+1 and delta > 0 else \
                Posture.RIGHT_LATERAL if abs(delta) >= self.config.upright_tolerance_cells+1 and delta < 0 else Posture.SUPINE

        # 엎드림 탐지
        hip_mean = hip[2]
        if hip_mean < self.config.prone_ratio * threshold:
            label = Posture.PRONE

        return label

    # head_raw: int32, body_raw: int32
    def detect(self, head_raw: np.ndarray, body_raw: np.ndarray) -> Dict:
        head = np.clip(head_raw, self.config.value_min, self.config.value_max)
        body = np.clip(body_raw, self.config.value_min, self.config.value_max)

        self.frame_buffer.push(head, body)
        head_avg, body_avg = self.frame_buffer.get_avg()

        adaptive_threshold = self._adaptive_threshold(head_avg, body_avg)

        torso = self._detect_torso_parts(body, adaptive_threshold)
        f_r, f_c = torso["block_rc"]
        block_mean = float(body_avg[f_r:f_r+2, f_c:f_c+2].mean())

        if torso["part_hint"] == TorsoParts.SHOULDERS:
            detected_shoulder = (*torso["center_rc"], block_mean)
            # 하단 부위 중 최댓값에서 엉덩이 탐색
            lower = body_avg[body_avg.shape[0]//2:, :]
            lower_sum = self._sum2x2(lower)
            l_r, l_c = self._argmax2d(lower_sum)
            detected_hip = (l_r+body_avg.shape[0]//2+0.5, l_c+0.5, float(lower[l_r:l_r+2, l_c:l_c+2].mean()))
        elif torso["part_hint"] == TorsoParts.HIPS:
            detected_hip = (*torso["center_rc"], block_mean)
            upper = body_avg[:body_avg.shape[0]//2, :]
            upper_sum = self._sum2x2(upper)
            u_r, u_c = self._argmax2d(upper_sum)
            detected_shoulder = (u_r+0.5, u_c+0.5, float(upper[u_r:u_r+2, u_c:u_c+2].mean()))

        detected_head = self._detect_head(head, adaptive_threshold)
        detected_heels = self._detect_heel(body_avg, adaptive_threshold)
        posture = self._detect_posture(detected_head, detected_shoulder, detected_hip, adaptive_threshold)

        return {
            "threshold": adaptive_threshold,
            "posture": posture,
            "head": detected_head,
            "shoulder": detected_shoulder,
            "hip": detected_hip,
            "heels": detected_heels
        }
