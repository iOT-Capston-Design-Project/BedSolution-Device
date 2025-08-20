from typing import List, Dict, Any, Optional

# 서버 통신 관련 함수들의 인터페이스 (구현은 비워둠)

def register_device(server_url: str, api_key: str) -> Optional[str]:
    """서버에 디바이스를 등록하고 디바이스 ID를 반환합니다."""
    # TODO: 실제 서버 통신 구현
    return "dummy-device-id-12345"

def get_logs_by_date(server_url: str, api_key: str, device_id: str) -> List[Dict[str, Any]]:
    """날짜별 로그 요약(부위별 압력 시간 총합-초)을 가져옵니다."""
    # TODO: 실제 서버 통신 구현
    # 임시 데이터 반환
    return [
        {
            "datetime": "2025-08-19",
            "occiput": 4800,  # 1시간 20분
            "scapula": 7800,  # 2시간 10분
            "elbow": 1800,    # 0시간 30분
            "hip": 13500,   # 3시간 45분
            "heel": 6900,     # 1시간 55분
        },
        {
            "datetime": "2025-08-20",
            "occiput": 3000,  # 0시간 50분
            "scapula": 6000,  # 1시간 40분
            "elbow": 4200,    # 1시간 10분
            "hip": 14700,   # 4시간 05분
            "heel": 8100,     # 2시간 15분
        },
    ]

def get_log_details(server_url: str, api_key: str, device_id: str, date: str) -> List[Dict[str, Any]]:
    """특정 날짜의 상세 로그(시간대별 압력 값)를 가져옵니다."""
    # TODO: 실제 서버 통신 구현
    # 임시 데이터 반환. 압력 값은 int로 수정.
    return [
        {
            "datetime": f"{date} 10:00:00",
            "occiput": 25,
            "scapula": 40,
            "elbow": 12,
            "hip": 80,
            "heel": 30,
        },
        {
            "datetime": f"{date} 10:00:05",
            "occiput": 26,
            "scapula": 41,
            "elbow": 11,
            "hip": 82,
            "heel": 30,
        },
    ]

def send_data(server_url: str, api_key: str, device_id: str, data: Dict[str, Any]) -> bool:
    """측정 데이터를 서버로 전송합니다."""
    # TODO: 실제 서버 통신 구현
    return True
