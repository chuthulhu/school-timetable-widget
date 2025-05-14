import os
import sys
import psutil
import time
import signal

# Windows 전용 API 가져오기 시도
try:
    import win32api
    import win32con
    import win32process
    WINDOWS_API_AVAILABLE = True
except ImportError:
    WINDOWS_API_AVAILABLE = False

def force_kill_process(pid):
    """특정 PID를 가진 프로세스를 강제 종료"""
    try:
        if WINDOWS_API_AVAILABLE:
            # Windows API를 사용한 강력한 종료 방식
            PROCESS_TERMINATE = 1
            handle = win32api.OpenProcess(PROCESS_TERMINATE, False, pid)
            if handle:
                win32api.TerminateProcess(handle, 0)
                win32api.CloseHandle(handle)
                print(f"Windows API로 프로세스 종료: {pid}")
                return True
        
        # 일반적인 방식
        process = psutil.Process(pid)
        process.kill()
        return True
    except Exception as e:
        print(f"프로세스 {pid} 강제 종료 실패: {str(e)}")
        return False

def kill_process_by_name(process_name):
    """
    지정된 이름을 포함하는 모든 프로세스 종료
    Args:
        process_name: 종료할 프로세스 이름(부분적으로 일치해도 됨)
    """
    count = 0
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                pid = proc.info['pid']
                print(f"프로세스 종료 중: {proc.info['name']} (PID: {pid})")
                if force_kill_process(pid):
                    count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return count

def kill_python_processes_aggressive(exclude_pid=None):
    """
    현재 프로세스를 제외한 모든 파이썬 관련 프로세스를 적극적으로 종료
    """
    if exclude_pid is None:
        exclude_pid = os.getpid()
    
    count = 0
    print(f"현재 프로세스 ID: {exclude_pid} (제외됨)")
    
    # 프로세스 트리에서 제외할 PID 목록
    exclude_pids = [exclude_pid]
    
    # 현재 프로세스의 부모는 제외
    try:
        parent_pid = psutil.Process(exclude_pid).parent().pid
        exclude_pids.append(parent_pid)
        print(f"부모 프로세스 ID: {parent_pid} (제외됨)")
    except:
        pass
    
    # 모든 프로세스 조사
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            proc_info = proc.info
            pid = proc_info['pid']
            
            if pid in exclude_pids:
                continue
                
            # 파이썬 관련 프로세스인지 확인
            is_python_related = False
            
            # 1. 이름으로 확인
            if proc_info['name'] and ('python' in proc_info['name'].lower()):
                is_python_related = True
            
            # 2. 명령줄로 확인
            elif proc_info['cmdline']:
                cmdline = " ".join(proc_info['cmdline']).lower()
                if 'python' in cmdline or 'whisper_project' in cmdline or 'school' in cmdline:
                    is_python_related = True
            
            # 3. 이 프로세스가 현재 프로세스의 자식인지 확인
            if not is_python_related:
                try:
                    parent = psutil.Process(pid).parent()
                    if parent and parent.pid in exclude_pids:
                        is_python_related = True
                except:
                    pass
            
            if is_python_related:
                try:
                    cmd_line = " ".join(proc_info['cmdline'])[:50]
                    if len(" ".join(proc_info['cmdline'])) > 50:
                        cmd_line += "..."
                except:
                    cmd_line = "명령줄 정보 없음"
                    
                print(f"관련 프로세스 종료 중: {proc_info['name']} (PID: {pid}) - {cmd_line}")
                if force_kill_process(pid):
                    count += 1
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return count

if __name__ == "__main__":
    print("프로세스 정리 도구 (강화 버전)")
    
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--help" or sys.argv[1].lower() == "-h":
            print("사용법:")
            print("  process_killer.py               - 모든 관련 Python 프로세스 종료")
            print("  process_killer.py <이름>        - 지정된 이름의 프로세스 종료")
            print("  process_killer.py --aggressive  - 적극적인 방식으로 모든 관련 프로세스 종료")
        elif sys.argv[1].lower() == "--aggressive" or sys.argv[1].lower() == "-a":
            print("적극적인 방식으로 모든 관련 프로세스를 종료합니다...")
            count = kill_python_processes_aggressive()
            print(f"총 {count}개 프로세스 종료됨")
        else:
            process_name = sys.argv[1]
            print(f"'{process_name}' 이름의 프로세스 종료")
            count = kill_process_by_name(process_name)
            print(f"총 {count}개 프로세스 종료됨")
    else:
        print("현재 프로세스를 제외한 모든 Python 프로세스 종료")
        count = kill_python_processes_aggressive()
        print(f"총 {count}개 Python 프로세스 종료됨")
