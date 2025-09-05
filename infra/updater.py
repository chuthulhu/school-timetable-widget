import requests
from typing import Optional

GITHUB_REPO = "chuthulhu/school-timetable-widget"  # placeholder; update for v2
GITHUB_API_RELEASES = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


class Updater:
    def __init__(self):
        self.latest_version: Optional[str] = None
        self.download_url: Optional[str] = None
        self.release_notes: Optional[str] = None

    def check_for_update(self) -> bool:
        try:
            resp = requests.get(GITHUB_API_RELEASES, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                self.latest_version = data.get("tag_name")
                self.release_notes = data.get("body", "")
                for asset in data.get("assets", []):
                    if asset.get("name", "").endswith(".exe"):
                        self.download_url = asset.get("browser_download_url")
                        break
                return bool(self.latest_version and self.download_url)
        except Exception:
            pass
        return False


