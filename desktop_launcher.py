"""Windows tray launcher. Frozen executable also hosts its own server child."""
from __future__ import annotations

import argparse
import asyncio
import ctypes
import json
import logging
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from app_paths import desktop_directory

ROOT = Path(__file__).resolve().parent


def ready(url: str) -> bool:
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(url + "/_stcore/health", timeout=1) as response:
            return response.status == 200 and response.read() == b"ok"
    except (OSError, ValueError):
        return False


def server(port: int) -> None:
    if sys.stdin is None:
        import msvcrt
        from ctypes import wintypes
        get_handle = ctypes.windll.kernel32.GetStdHandle
        get_handle.restype = wintypes.HANDLE
        pipe = get_handle(-10)  # STD_INPUT_HANDLE inherited from our parent.
        sys.stdin = os.fdopen(msvcrt.open_osfhandle(pipe, os.O_RDONLY), "r")
    if sys.stderr is None:
        sys.stderr = open(Path(os.environ["QUESTIONNAIRE_DATA_DIR"]) / "desktop-server.log", "a", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = sys.stderr
    from streamlit.web import bootstrap
    from streamlit import config

    config.get_config_options()
    config._set_option("server.address", "127.0.0.1", "desktop launcher")
    config._set_option("server.port", port, "desktop launcher")
    config._set_option("server.headless", True, "desktop launcher")
    config._set_option("browser.gatherUsageStats", False, "desktop launcher")
    config._set_option("server.fileWatcherType", "none", "desktop launcher")
    original = bootstrap._set_up_signal_handler

    def install_shutdown(instance):
        original(instance)
        loop = asyncio.get_running_loop()

        def listen():
            # Private parent pipe, never an unauthenticated HTTP shutdown URL.
            # EOF also stops the child if the launcher disappears.
            sys.stdin.readline()
            loop.call_soon_threadsafe(instance.stop)

        threading.Thread(target=listen, daemon=True).start()

    # ponytail: one pinned Streamlit bootstrap hook; test when upgrading Streamlit.
    bootstrap._set_up_signal_handler = install_shutdown
    bootstrap.run(str(ROOT / "app.py"), False, [], {})


class DesktopServer:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.process = None
        self.log = None
        self.url = ""

    def start(self, cancelled=None):
        if cancelled and cancelled.is_set():
            raise RuntimeError("Startup cancelled")
        self.directory.mkdir(parents=True, exist_ok=True)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        command = [sys.executable]
        if not getattr(sys, "frozen", False):
            command.append(str(Path(__file__).resolve()))
        command += ["--server", str(port)]
        environment = os.environ.copy()
        environment["QUESTIONNAIRE_DATA_DIR"] = str(self.directory)
        environment["PYTHONNOUSERSITE"] = "1"
        self.log = (self.directory / "desktop-server.log").open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            command, cwd=self.directory, env=environment, stdin=subprocess.PIPE,
            stdout=self.log, stderr=subprocess.STDOUT, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if cancelled and cancelled.is_set():
                raise RuntimeError("Startup cancelled")
            if self.process.poll() is not None:
                raise RuntimeError("The application could not start. See desktop-server.log in the data folder.")
            if ready(self.url):
                return self.url
            time.sleep(0.25)
        raise RuntimeError("The application took too long to start. See desktop-server.log in the data folder.")

    def stop(self):
        if self.process and self.process.poll() is None:
            try:
                self.process.stdin.write("STOP\n")
                self.process.stdin.flush()
                self.process.wait(timeout=30)
            except (OSError, subprocess.TimeoutExpired):
                self.process.terminate()
                self.process.wait(timeout=10)
        if self.process and self.process.stdin:
            self.process.stdin.close()
        if self.log:
            self.log.close()


def notify(message: str):
    ctypes.windll.user32.MessageBoxW(None, message, "Questionnaire Review", 0x40)


def open_browser(url: str):
    # External browser must not inherit PyInstaller's DLL search directory.
    if getattr(sys, "frozen", False):
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    try:
        return webbrowser.open(url)
    finally:
        if getattr(sys, "frozen", False):
            ctypes.windll.kernel32.SetDllDirectoryW(str(ROOT))


def launch(directory: Path):
    import msvcrt
    import pystray
    from PIL import Image, ImageDraw

    directory.mkdir(parents=True, exist_ok=True)
    lock = (directory / "desktop.lock").open("a+b")
    lock.seek(0)
    if not lock.read(1):
        lock.write(b"0")
        lock.flush()
    lock.seek(0)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock.close()
        try:
            url = json.loads((directory / "desktop-instance.json").read_text())["url"]
            if ready(url):
                open_browser(url)
                return
        except (OSError, ValueError, KeyError):
            pass
        notify("Questionnaire Review is already starting. Look for its Q icon near the Windows clock.")
        return

    host = DesktopServer(directory)
    quitting = threading.Event()
    startup_finished = threading.Event()
    picture = Image.new("RGB", (64, 64), "#176b87")
    ImageDraw.Draw(picture).text((22, 18), "Q", fill="white", stroke_width=2)

    def exit_app(icon, item=None):
        quitting.set()
        icon.title = "Questionnaire Review — closing"
        icon.stop()

    def open_app(icon, item=None):
        if ready(host.url):
            open_browser(host.url)

    icon = pystray.Icon("QuestionnaireReview", picture, "Questionnaire Review — starting",
                        pystray.Menu(pystray.MenuItem("Open application", open_app, default=True),
                                     pystray.MenuItem("Exit", exit_app)))

    def startup(icon):
        icon.visible = True
        try:
            url = host.start(quitting)
            (directory / "desktop-instance.json").write_text(json.dumps({"url": url}), encoding="utf-8")
            if not quitting.is_set():
                icon.title = "Questionnaire Review"
                if not open_browser(url):
                    notify(f"Open this address in your browser: {url}")
            while not quitting.wait(1):
                if host.process.poll() is not None:
                    raise RuntimeError("The application stopped. Reopen Questionnaire Review to restart it.")
        except Exception as exc:
            if not quitting.is_set():
                notify(str(exc))
        finally:
            quitting.set()
            startup_finished.set()
            icon.stop()

    try:
        icon.run(setup=startup)
    finally:
        quitting.set()
        startup_finished.wait(timeout=95)
        host.stop()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
        lock.close()


def self_test(directory: Path):
    """Exercise the frozen runtime and real process lifecycle without using Google."""
    import keyring
    from workflow import load_evidence, JobStore
    from streamlit.testing.v1 import AppTest
    from verify import Q1FixtureProvider
    from workflow import retrieve
    from types import SimpleNamespace

    report = {"frozen": bool(getattr(sys, "frozen", False))}
    host = DesktopServer(directory)
    os.environ["QUESTIONNAIRE_DATA_DIR"] = str(directory)
    for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GEMINI_MODEL"):
        os.environ.pop(name, None)
    try:
        assert type(keyring.get_keyring()).__name__ == "WinVaultKeyring"
        report["credential_backend"] = "WinVaultKeyring"
        assert len(load_evidence(ROOT)) == 109
        from unittest.mock import patch
        with patch("secure_settings._read", return_value=None):
            ui = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
        assert not ui.exception, str(ui.exception)
        assert ui.title[0].value == "Guided questionnaire review"
        assert any(b.label == "Save settings" for b in ui.button)
        assert (directory / "questionnaire_jobs.sqlite3").exists()
        report["ui_and_appdata"] = "passed"
        evidence = load_evidence(ROOT)
        index = SimpleNamespace(sync=lambda items: None,
                                search=lambda q, limit=8: [(s, 1.0) for s in retrieve(q, evidence, limit)])
        with (patch("secure_settings.settings_status", return_value=(True, True, "test")),
              patch("secure_settings._read", return_value=None),
              patch("semantic.GeminiProvider", return_value=Q1FixtureProvider()),
              patch("semantic.GoogleEmbeddings"),
              patch("semantic.SemanticIndex", return_value=index)):
            ui = AppTest.from_file(str(ROOT / "app.py")).run(timeout=60)
            ui.get("file_uploader")[0].upload("q1.csv", (ROOT / "questionnaires/questionnaire-1-standard.csv").read_bytes(), "text/csv").run(timeout=60)
            next(b for b in ui.button if b.label == "Generate draft").click().run(timeout=60)
        assert not ui.exception, str(ui.exception)
        store = JobStore(directory / "questionnaire_jobs.sqlite3")
        rows = store.rows(store.list_jobs()[0]["id"])
        assert len(rows) == 25 and not any(r["result"].processing_error for r in rows)
        assert len(ui.get("download_button")) == 2
        report["q1_upload_generate_export_fixture"] = "25 rows; 2 downloads"
        url = host.start()
        report["loopback_health"] = url
        host.stop()
        assert host.process.returncode == 0, host.process.returncode
        assert not ready(url)
        report["graceful_shutdown"] = "passed"
        report["passed"] = True
    except Exception as exc:
        report.update(passed=False, error=str(exc))
        raise
    finally:
        host.stop()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "desktop-self-test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=int)
    parser.add_argument("--self-test", type=Path)
    args = parser.parse_args()
    if args.server:
        try:
            server(args.server)
        except Exception:
            import traceback
            traceback.print_exc()
            sys.exit(1)
    elif args.self_test:
        try:
            self_test(args.self_test.resolve())
        except Exception:
            sys.exit(1)  # The test report carries the error; no modal dialog in automation.
    else:
        try:
            launch(desktop_directory())
        except Exception as exc:
            notify(f"Could not open Questionnaire Review: {exc}")
