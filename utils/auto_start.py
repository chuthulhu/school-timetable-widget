import os
import sys
import winreg
import win32com.client

APP_NAME = "학교시간표위젯"

# 현재 실행 파일 경로 반환 (exe 또는 py)
def get_exe_path():
    if getattr(sys, 'frozen', False):
        return sys.executable
    return os.path.abspath(sys.argv[0])

# 1. 시작프로그램(Startup 폴더)에 바로가기 생성/삭제
def get_startup_folder():
    return os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")

def add_shortcut_to_startup():
    startup_path = get_startup_folder()
    shortcut_path = os.path.join(startup_path, f"{APP_NAME}.lnk")
    exe_path = get_exe_path()
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = exe_path
    shortcut.WorkingDirectory = os.path.dirname(exe_path)
    shortcut.IconLocation = exe_path
    shortcut.save()
    return shortcut_path

def remove_shortcut_from_startup():
    shortcut_path = os.path.join(get_startup_folder(), f"{APP_NAME}.lnk")
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        return True
    return False

# 2. 레지스트리 등록/해제 (HKCU)
def add_to_registry():
    exe_path = get_exe_path()
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
    winreg.CloseKey(key)

def remove_from_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

# 통합 함수: startup 방식 선택 가능
def enable_auto_start(method="shortcut"):
    if method == "shortcut":
        add_shortcut_to_startup()
    elif method == "registry":
        add_to_registry()

def disable_auto_start(method="shortcut"):
    if method == "shortcut":
        remove_shortcut_from_startup()
    elif method == "registry":
        remove_from_registry()
