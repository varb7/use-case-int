import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from app_paths import data_directory
from desktop_launcher import launch


class DesktopTests(unittest.TestCase):
    def test_source_default_and_desktop_storage_are_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.dict(os.environ, {"QUESTIONNAIRE_DATA_DIR": ""}):
                self.assertEqual(data_directory(root), root)
            with patch.dict(os.environ, {"QUESTIONNAIRE_DATA_DIR": str(root / "user-state")}):
                self.assertEqual(data_directory(root), root / "user-state")
                self.assertTrue((root / "user-state").is_dir())

    def test_tray_start_opens_browser_and_exit_stops_server(self):
        import pystray
        opened = threading.Event()
        def open_url(url):
            opened.set()
            return True

        class FakeIcon:
            def __init__(self, name, image, title, menu):
                self.menu = menu
            def run(self, setup):
                worker = threading.Thread(target=setup, args=(self,))
                worker.start()
                if not opened.wait(5):
                    raise AssertionError("Browser did not open")
                exit_item = next(item for item in self.menu.items if item.text == "Exit")
                exit_item(self)
                worker.join(timeout=5)
                assert not worker.is_alive()
            def stop(self):
                pass

        with tempfile.TemporaryDirectory() as temporary:
            with patch("desktop_launcher.DesktopServer") as host, patch("pystray.Icon", FakeIcon), patch(
                    "desktop_launcher.open_browser", side_effect=open_url):
                host.return_value.start.return_value = "http://127.0.0.1:12345"
                launch(Path(temporary))
                host.return_value.start.assert_called_once()
                host.return_value.stop.assert_called_once()
                self.assertEqual(json.loads((Path(temporary) / "desktop-instance.json").read_text())["url"],
                                 "http://127.0.0.1:12345")


if __name__ == "__main__":
    unittest.main()
