param(
    [switch]$Clean
)

if ($Clean) {
    Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
}

py -m venv .venv
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\pip install -r requirements.txt
pyinstaller --noconfirm --name TimetableWidgetV2 --icon assets/app_icon.ico --onefile app\main.py

Write-Host "Build complete. See dist/"


