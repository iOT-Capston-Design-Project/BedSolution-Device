from typing import List, Dict, Any, Optional
import requests
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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
        *,
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
        backoff_factor: float = 0.3,
    ) -> None:
        self.server_url = server_url.rstrip("/") if server_url else None
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _resolve_credentials(self, server_url: Optional[str], api_key: Optional[str]) -> (str, str):
        """메서드 인자와 인스턴스 기본값을 조합해 실제 사용할 자격 정보를 반환."""
        final_url = (server_url or self.server_url or "").rstrip("/")
        final_key = api_key or self.api_key or ""
        if not final_url or not final_key:
            raise ValueError("Server URL과 API Key는 반드시 설정되어야 합니다.")
        return final_url, final_key

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(self, method: str, url: str, api_key: str, **kwargs: Any) -> Response:
        """공통 요청 메서드. 필요 시 실제 서버 연동에 사용하세요."""
        headers = kwargs.pop("headers", {})
        merged_headers = {**self._build_headers(api_key), **headers}
        return self.session.request(
            method=method,
            url=url,
            headers=merged_headers,
            timeout=self.timeout_seconds,
            **kwargs,
        )

    def register_device(self, server_url: Optional[str] = None, api_key: Optional[str] = None) -> Optional[str]:
        """서버에 디바이스를 등록하고 디바이스 ID를 반환.

        현재는 샘플 값을 반환합니다.
        """
        # 실제 연동 예시
        # base_url, key = self._resolve_credentials(server_url, api_key)
        # resp = self._request("POST", f"{base_url}/devices", key, json={})
        # resp.raise_for_status()
        # return resp.json().get("device_id")
        return "dummy-device-id-12345"

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


# 모듈 수준의 기본 클라이언트와 하위 호환 함수 래퍼
_default_client = APIClient()


def register_device(server_url: str, api_key: str) -> Optional[str]:
    return _default_client.register_device(server_url, api_key)


def get_logs_by_date(server_url: str, api_key: str, device_id: str) -> LogSummary:
    return _default_client.get_logs_by_date(server_url, api_key, device_id)


def get_log_details(server_url: str, api_key: str, device_id: str, date: str) -> LogDetails:
    return _default_client.get_log_details(server_url, api_key, device_id, date)


def send_data(server_url: str, api_key: str, device_id: str, data: Dict[str, Any]) -> bool:
    return _default_client.send_data(server_url, api_key, device_id, data)
