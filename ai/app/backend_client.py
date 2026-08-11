"""HTTP client used by the AI service to report detections to the backend API."""
import logging
import threading
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

from app.config import settings

logger = logging.getLogger(__name__)


class BackendClient:
    """Thin, thread-safe client for the backend API.

    The AI service never talks to the database directly; it authenticates
    against the backend and pushes detections/events through the REST API.
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self._lock = threading.RLock()
        self._token: Optional[str] = None

    def _url(self, path: str) -> str:
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    def login(self) -> Optional[str]:
        """Authenticate and cache the access token. Returns None on failure."""
        try:
            resp = requests.post(
                self._url("/api/auth/login"),
                data={"username": self.username, "password": self.password},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.warning("Backend login request failed: %s", exc)
            return None
        if resp.status_code != 200:
            logger.error(
                "Backend login failed: %s %s", resp.status_code, resp.text[:200]
            )
            return None
        self._token = resp.json()["access_token"]
        logger.info("Authenticated with backend as %s", self.username)
        return self._token

    def _ensure_token(self) -> Optional[str]:
        if self._token is None:
            with self._lock:
                if self._token is None:
                    self.login()
        return self._token

    def _request(self, method: str, path: str, json: Optional[Dict[str, Any]] = None):
        with self._lock:
            try:
                token = self._ensure_token()
            except Exception as exc:
                logger.warning("Failed to obtain backend token: %s", exc)
                return None
            if token is None:
                return None
            try:
                return requests.request(
                    method,
                    self._url(path),
                    json=json,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                logger.warning("Backend request to %s failed: %s", path, exc)
                return None

    def post_vehicle(self, payload: Dict[str, Any]) -> bool:
        """Register a detected vehicle with the backend."""
        resp = self._request("POST", "/api/vehicles/", json=payload)
        if resp is None:
            return False
        if resp.status_code in (401, 403):
            with self._lock:
                self._token = None
            logger.info("Backend rejected token, re-authenticating once")
            resp = self._request("POST", "/api/vehicles/", json=payload)
        if resp is not None and resp.status_code < 300:
            return True
        logger.warning(
            "Failed to report vehicle to backend: %s %s",
            resp.status_code if resp else "no-response",
            resp.text[:200] if resp is not None else "",
        )
        return False

    def post_event(self, payload: Dict[str, Any]) -> bool:
        """Register an event (parking/unparking/plate) with the backend."""
        resp = self._request("POST", "/api/events/", json=payload)
        if resp is None:
            return False
        if resp.status_code in (401, 403):
            with self._lock:
                self._token = None
            resp = self._request("POST", "/api/events/", json=payload)
        if resp is not None and resp.status_code < 300:
            return True
        logger.warning(
            "Failed to report event to backend: %s %s",
            resp.status_code if resp else "no-response",
            resp.text[:200] if resp is not None else "",
        )
        return False


backend_client = BackendClient(
    base_url=settings.BACKEND_URL,
    username=settings.BACKEND_USERNAME,
    password=settings.BACKEND_PASSWORD,
)
