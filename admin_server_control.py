import socket
import subprocess
from pathlib import Path

from config import BASE_DIR


class ServerCommandError(RuntimeError):
    pass


class ComposeServerController:
    def __init__(self, project_dir: Path = BASE_DIR):
        self.project_dir = project_dir

    def start(self) -> str:
        return self._run("up", "-d", "--build")

    def stop(self) -> str:
        return self._run("down")

    def status(self) -> str:
        return self._run("ps")

    def _run(self, *args: str) -> str:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        completed = subprocess.run(
            ["docker", "compose", *args],
            cwd=self.project_dir,
            text=True,
            capture_output=True,
            creationflags=creation_flags,
            timeout=180,
        )
        output = (completed.stdout + "\n" + completed.stderr).strip()
        if completed.returncode != 0:
            raise ServerCommandError(output or "Команда Docker Compose завершилась ошибкой.")
        return output


def local_server_url(port: int = 8765) -> str:
    return f"http://{_local_ip()}:{port}"


def _local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
