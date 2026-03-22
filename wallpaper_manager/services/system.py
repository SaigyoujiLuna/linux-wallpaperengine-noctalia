from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from wallpaper_manager.config.constants import ASSETS_SUBPATH, CACHE_DIR, ENGINE_BIN
from wallpaper_manager.i18n import tr

NOCTALIA_SHELL_IPC_TIMEOUT_SECONDS = 2
NOCTALIA_SHELL_STARTUP_TIMEOUT_SECONDS = 20
NOCTALIA_SHELL_STARTUP_POLL_SECONDS = 0.5
NOCTALIA_SHELL_NOTIFY_TIMEOUT_SECONDS = 15
NOCTALIA_SHELL_NOTIFY_POLL_SECONDS = 0.5
SCREENSHOT_READY_TIMEOUT_SECONDS = 20
SCREENSHOT_READY_POLL_SECONDS = 0.25


@dataclass(frozen=True, slots=True)
class OperationResult:
    success: bool
    error: str | None = None


def get_monitors() -> list[str]:
    """Return monitor names reported by wlr-randr, or an empty list."""
    try:
        result = subprocess.run(
            ["wlr-randr", "--json"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    if result.returncode != 0:
        return []

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []

    monitors: list[str] = []
    for item in payload:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            monitors.append(item["name"])
    return monitors


def _find_matching_pids(pattern: str) -> list[int]:
    try:
        result = subprocess.run(
            ["pgrep", "-f", pattern],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return []

    if result.returncode not in (0, 1):
        return []

    pids: list[int] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def terminate_matching_processes(pattern: str) -> int:
    """Terminate processes matched by `pgrep -f pattern` and return count."""
    terminated = 0
    for pid in _find_matching_pids(pattern):
        try:
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            continue
        terminated += 1
    return terminated


def stop_engine_processes() -> int:
    return terminate_matching_processes(ENGINE_BIN)


def prepare_screenshot_path() -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"wallpaper-{time.time_ns()}.png"


def resolve_monitor(preferred_monitor: str | None = None) -> str | None:
    if preferred_monitor:
        return preferred_monitor
    monitors = get_monitors()
    return monitors[0] if monitors else None


def build_engine_command(
    we_install_dir: str,
    wallpaper_dir: str | Path,
    monitor: str,
    scaling: str,
    *,
    screenshot_path: Path | None = None,
) -> list[str]:
    command = [
        ENGINE_BIN,
        "--assets-dir",
        str(Path(we_install_dir).expanduser() / ASSETS_SUBPATH),
        str(Path(wallpaper_dir).expanduser()),
        "--silent",
        "--screen-root",
        monitor,
        "--scaling",
        scaling,
    ]
    if screenshot_path is not None:
        command.extend(
            [
                "--screenshot",
                str(screenshot_path),
                "--screenshot-delay",
                "10",
            ]
        )
    return command


def launch_background_process(command: Sequence[str]) -> None:
    subprocess.Popen(
        list(command),
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def launch_wallpaper(
    we_install_dir: str,
    wallpaper_dir: str | Path,
    monitor: str,
    scaling: str,
) -> Path:
    stop_engine_processes()
    screenshot_path = prepare_screenshot_path()
    command = build_engine_command(
        we_install_dir,
        wallpaper_dir,
        monitor,
        scaling,
        screenshot_path=screenshot_path,
    )
    launch_background_process(command)
    return screenshot_path


def _run_noctalia_shell_ipc(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["qs", "-c", "noctalia-shell", "ipc", *arguments],
        capture_output=True,
        text=True,
        timeout=NOCTALIA_SHELL_IPC_TIMEOUT_SECONDS,
        check=False,
    )


def wait_for_noctalia_shell_startup() -> OperationResult:
    """Wait until noctalia-shell registers the wallpaper IPC target."""
    deadline = time.monotonic() + NOCTALIA_SHELL_STARTUP_TIMEOUT_SECONDS
    last_error: str | None = None

    while time.monotonic() < deadline:
        try:
            result = _run_noctalia_shell_ipc("show")
        except FileNotFoundError:
            return OperationResult(False, tr("service.qs_not_found"))
        except subprocess.TimeoutExpired:
            last_error = tr("service.noctalia_ipc_ready_timeout")
        except OSError as exc:
            last_error = tr("service.noctalia_probe_failed", error=exc)
        else:
            if result.returncode == 0:
                if "target wallpaper" in result.stdout:
                    return OperationResult(True)
                last_error = tr("service.noctalia_target_not_registered")
            else:
                detail = (result.stderr or result.stdout).strip()
                last_error = detail or tr("service.noctalia_ipc_not_ready")

        if time.monotonic() < deadline:
            time.sleep(NOCTALIA_SHELL_STARTUP_POLL_SECONDS)

    return OperationResult(False, last_error or tr("service.noctalia_startup_timeout"))


def wait_for_screenshot(screenshot_path: Path) -> OperationResult:
    """Wait until the screenshot file exists and stops growing."""
    deadline = time.monotonic() + SCREENSHOT_READY_TIMEOUT_SECONDS
    last_size: int | None = None
    stable_polls = 0

    while time.monotonic() < deadline:
        try:
            stat_result = screenshot_path.stat()
        except FileNotFoundError:
            last_size = None
            stable_polls = 0
        except OSError as exc:
            return OperationResult(False, tr("service.screenshot_read_failed", error=exc))
        else:
            if stat_result.st_size > 0:
                if stat_result.st_size == last_size:
                    stable_polls += 1
                else:
                    last_size = stat_result.st_size
                    stable_polls = 0

                if stable_polls >= 1:
                    return OperationResult(True)
            else:
                last_size = stat_result.st_size
                stable_polls = 0

        time.sleep(SCREENSHOT_READY_POLL_SECONDS)

    return OperationResult(False, tr("service.screenshot_timeout"))


def notify_noctalia_shell(
    monitor: str, wallpaper_path: Path
) -> OperationResult:
    """Ask noctalia-shell to regenerate wallpaper-derived colors."""
    screenshot_result = wait_for_screenshot(wallpaper_path)
    if not screenshot_result.success:
        return screenshot_result

    deadline = time.monotonic() + NOCTALIA_SHELL_NOTIFY_TIMEOUT_SECONDS
    last_error: str | None = None

    while time.monotonic() < deadline:
        try:
            result = _run_noctalia_shell_ipc(
                "call",
                "wallpaper",
                "set",
                str(wallpaper_path),
                monitor,
            )
        except FileNotFoundError:
            return OperationResult(False, tr("service.qs_not_found"))
        except subprocess.TimeoutExpired:
            last_error = tr("service.noctalia_response_timeout")
        except OSError as exc:
            last_error = tr("service.noctalia_notify_failed", error=exc)
        else:
            if result.returncode == 0:
                return OperationResult(True)
            detail = (result.stderr or result.stdout).strip()
            last_error = detail or tr("service.noctalia_ipc_call_failed")

        if time.monotonic() < deadline:
            time.sleep(NOCTALIA_SHELL_NOTIFY_POLL_SECONDS)

    return OperationResult(False, last_error or tr("service.noctalia_startup_timeout"))
