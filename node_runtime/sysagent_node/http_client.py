from __future__ import annotations

import json
from typing import Any
from urllib import error, parse, request


class ApiError(RuntimeError):
    pass


class SysAgentApi:
    def __init__(self, server_url: str, node_token: str | None = None, timeout: int = 15) -> None:
        self.server_url = server_url.rstrip("/")
        self.node_token = node_token
        self.timeout = timeout

    def register(self, token: str, name: str, ip_address: str | None, node_type: str) -> dict[str, Any]:
        return self._post("/api/node/register", {
            "token": token,
            "name": name,
            "ipAddress": ip_address,
            "type": node_type,
        })

    def heartbeat(self, payload: dict[str, Any]) -> None:
        self._post("/api/node/heartbeat", payload, auth=True)

    def submit_context(self, payload: dict[str, Any]) -> None:
        self._post("/api/node/context", payload, auth=True)

    def next_command(self, device_id: int) -> dict[str, Any] | None:
        query = parse.urlencode({"deviceId": device_id})
        response = self._get(f"/api/node/commands/next?{query}", auth=True)
        return response.get("data")

    def command_result(self, command_id: str, payload: dict[str, Any]) -> None:
        self._post(f"/api/node/commands/{command_id}/result", payload, auth=True)

    def _get(self, path: str, auth: bool = False) -> dict[str, Any]:
        return self._request("GET", path, None, auth)

    def _post(self, path: str, payload: dict[str, Any], auth: bool = False) -> dict[str, Any]:
        return self._request("POST", path, payload, auth)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None, auth: bool) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if auth:
            if not self.node_token:
                raise ApiError("Node token is missing.")
            headers["X-SysAgent-Node-Token"] = self.node_token
        req = request.Request(f"{self.server_url}{path}", data=body, method=method, headers=headers)
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                data = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ApiError(f"HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise ApiError(f"Could not reach SysAgent backend: {exc.reason}") from exc

        parsed = json.loads(data) if data else {}
        if parsed.get("status") == "ERROR":
            raise ApiError(parsed.get("message") or "SysAgent API returned an error.")
        return parsed
