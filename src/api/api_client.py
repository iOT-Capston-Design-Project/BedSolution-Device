from datetime import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client
import uuid

from api.device_dto import DeviceDTO


LogSummary = List[Dict[str, Any]]
LogDetails = List[Dict[str, Any]]


class APIClient:
    """서버와 통신하기 위한 객체지향 API 클라이언트.

    - 인스턴스 생성 시 기본 `server_url`, `api_key`를 설정할 수 있으며,
      각 메서드 호출 시 인자로 전달하면 해당 값이 우선합니다.
    - 재시도, 타임아웃, 공통 헤더를 내부 세션에서 관리합니다.
    - 현재는 샘플 데이터를 반환하도록 구현되어 있습니다.
    """

    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.server_url = server_url.rstrip("/") if server_url else None
        self.api_key = api_key
        self.client = create_client(self.server_url, self.api_key)

    def _generate_device_id(self) -> int:
        device_uuid = uuid.uuid4()
        device_id = int(device_uuid.hex, 16) % (2**31)
        return device_id


    def register_device(self, server_url: Optional[str] = None, api_key: Optional[str] = None) -> Optional[int]:
        device_id = self._generate_device_id()
        dto = DeviceDTO(device_id, datetime.now())
        devices_table = self.client.table("devices")
        query = devices_table.insert(dto.to_dict())
        try:
            response = query.execute()
            if response.data:
                return response.data[0]["id"]
        except Exception as e:
            return None
        return None

    def get_logs_by_date(self, server_url: Optional[str], api_key: Optional[str], device_id: str) -> LogSummary:
        """날짜별 로그 요약(부위별 압력 시간 총합-초)을 조회.

        현재는 샘플 데이터를 반환합니다.
        """
        # base_url, key = self._resolve_credentials(server_url, api_key)
        # resp = self._request("GET", f"{base_url}/devices/{device_id}/logs/summary", key)
        # resp.raise_for_status()
        # return resp.json()
        return [
            {
                "datetime": "2025-08-19",
                "occiput": 4800,
                "scapula": 7800,
                "elbow": 1800,
                "hip": 13500,
                "heel": 6900,
            },
            {
                "datetime": "2025-08-20",
                "occiput": 3000,
                "scapula": 6000,
                "elbow": 4200,
                "hip": 14700,
                "heel": 8100,
            },
        ]

    def get_log_details(self, server_url: Optional[str], api_key: Optional[str], device_id: str, date: str) -> LogDetails:
        """특정 날짜의 상세 로그(시간대별 압력 값)를 조회.

        현재는 샘플 데이터를 반환합니다.
        """
        # base_url, key = self._resolve_credentials(server_url, api_key)
        # resp = self._request("GET", f"{base_url}/devices/{device_id}/logs/{date}", key)
        # resp.raise_for_status()
        # return resp.json()
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

    def send_data(self, server_url: Optional[str], api_key: Optional[str], device_id: str, data: Dict[str, Any]) -> bool:
        """측정 데이터를 서버로 전송.

        현재는 성공(True)으로 가정합니다.
        """
        # base_url, key = self._resolve_credentials(server_url, api_key)
        # resp = self._request("POST", f"{base_url}/devices/{device_id}/data", key, json=data)
        # resp.raise_for_status()
        # return True
        return True