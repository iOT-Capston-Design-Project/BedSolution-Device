from dataclasses import dataclass

@dataclass
class DetectionConfig:
    value_min: int = 100
    value_max: int = 900
    sampling_sec: float = 1.0 # 1Hz
    moving_avg_N: int = 3 # 이동 평균 프레임 수
    percentile_p: float = 70.0 # 상위 p%: 입계값
    upright_tolerance_cells: int = 1 # 정자세 허용 좌우 편차
    prone_ratio: float = 0.9 # 엎드림: hip_mean < prone_ratio*tau
    head_expand_lr: int = 1 # 머리 탐색 좌우 확장 셀
    heel_search_rows: int = 1 # 발꿈치 탐색 하단 행 수
    log_path: str = "posture_log.csv" # 로그 파일
    use_pillow: bool = True # 배게 사용 (머리 가중 반영용 플래그)
