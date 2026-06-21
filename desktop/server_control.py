from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path
from shutil import which


PROJECT_NAME = "secureoffice"


class ServerCommandError(RuntimeError):
    pass


def app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


class ComposeServerController:
    def __init__(self, project_dir: Path | None = None):
        self.project_dir = project_dir or app_root()
        self.compose_file = self.project_dir / "docker-compose.yml"

    def start(self) -> str:
        self._ensure_docker_ready()
        return self._compose("up", "-d", "--build", timeout=600)

    def stop(self) -> str:
        self._ensure_docker_ready()
        return self._compose("down", timeout=240)

    def status(self) -> str:
        self._ensure_docker_ready()
        return self._compose("ps", timeout=60)

    def _ensure_docker_ready(self) -> None:
        if which("docker") is None:
            raise ServerCommandError(
                "Docker не найден. Установите Docker Desktop, запустите его и повторите действие."
            )
        if not self.compose_file.exists():
            raise ServerCommandError(
                "Не найден docker-compose.yml рядом с приложением. Пересоберите exe или проверьте файлы проекта."
            )
        self._run_raw(["docker", "compose", "version"], timeout=30)

    def _compose(self, *args: str, timeout: int) -> str:
        return self._run_raw(
            [
                "docker",
                "compose",
                "--ansi",
                "never",
                "--project-name",
                PROJECT_NAME,
                "-f",
                str(self.compose_file),
                *args,
            ],
            timeout=timeout,
        )

    def _run_raw(
        self,
        command: list[str],
        *,
        timeout: int,
    ) -> str:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            completed = subprocess.run(
                command,
                cwd=self.project_dir,
                text=True,
                capture_output=True,
                creationflags=creation_flags,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise ServerCommandError(
                "Docker не найден. Установите Docker Desktop, запустите его и повторите действие."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ServerCommandError(
                "Docker отвечает слишком долго. Проверьте, что Docker Desktop запущен, и повторите действие."
            ) from exc

        output = (completed.stdout + "\n" + completed.stderr).strip()
        if completed.returncode == 0:
            return output
        lower_output = output.lower()
        if (
            "docker daemon" in lower_output
            or "error during connect" in lower_output
            or "is the docker daemon running" in lower_output
        ):
            raise ServerCommandError(
                "Docker Desktop не запущен или ещё не готов. Запустите Docker Desktop и дождитесь статуса Running."
            )
        raise ServerCommandError(output or "Команда Docker Compose завершилась ошибкой.")


def local_server_url(port: int = 8765) -> str:
    return f"http://{_local_ip()}:{port}"


def _local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
