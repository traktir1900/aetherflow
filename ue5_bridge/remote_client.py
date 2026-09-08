"""AetherFlow -> Unreal Engine Remote Control HTTP client.

Dependency-free external client. No gameplay logic belongs here.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class RemoteControlConfig:
    host: str = "127.0.0.1"
    port: int = 30010
    timeout_s: float = 15.0
    python_object_path: str = "/Script/PythonScriptPlugin.Default__PythonScriptLibrary"

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class RemoteControlError(RuntimeError):
    """Raised when UE Remote Control returns an error or is unreachable."""


class RemoteControlClient:
    def __init__(self, config: RemoteControlConfig | None = None) -> None:
        self.config = config or RemoteControlConfig()

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        url = f"{self.config.base_url}{path}"
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url=url,
            data=payload,
            method=method.upper(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_s) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RemoteControlError(
                f"UE Remote Control HTTP {exc.code} for {method} {path}: {detail}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RemoteControlError(
                f"Cannot reach Unreal Remote Control at {self.config.base_url}: {exc}"
            ) from exc

    def info(self) -> Any:
        return self.request("GET", "/remote/info")

    def call(
        self,
        object_path: str,
        function_name: str,
        parameters: dict[str, Any] | None = None,
        generate_transaction: bool = False,
    ) -> Any:
        return self.request(
            "PUT",
            "/remote/object/call",
            {
                "objectPath": object_path,
                "functionName": function_name,
                "parameters": parameters or {},
                "generateTransaction": generate_transaction,
            },
        )

    def batch(self, requests: Iterable[dict[str, Any]]) -> Any:
        items = list(requests)
        return self.request("PUT", "/remote/batch", {"Requests": items})

    def execute_python_file(self, script_path: str) -> Any:
        return self.call(
            self.config.python_object_path,
            "ExecutePythonCommand",
            {"PythonCommand": script_path},
        )

    def execute_python_code(self, code: str) -> Any:
        return self.call(
            self.config.python_object_path,
            "ExecutePythonCommand",
            {"PythonCommand": code},
        )

    def get_level_actors(self) -> list[str]:
        result = self.call(
            "/Script/EditorScriptingUtilities.Default__EditorLevelLibrary",
            "GetAllLevelActors",
        )
        return list((result or {}).get("ReturnValue", []))

    def is_available(self) -> bool:
        try:
            self.info()
            return True
        except RemoteControlError:
            return False
