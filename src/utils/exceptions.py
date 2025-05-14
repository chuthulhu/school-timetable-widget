"""
학교시간표위젯 예외 모듈
- 애플리케이션 전용 예외 클래스 정의
- 일관된 에러 처리를 위한 기반 클래스 제공
"""

class TimetableError(Exception):
    """시간표 위젯 애플리케이션의 기본 예외 클래스"""
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class ConfigError(TimetableError):
    """설정 관련 오류"""
    pass

class DataError(TimetableError):
    """데이터 로드/저장 관련 오류"""
    pass

class ResourceError(TimetableError):
    """리소스 파일 관련 오류"""
    pass

class TimetableFormatError(DataError):
    """시간표 데이터 형식 오류"""
    pass

class NotificationError(TimetableError):
    """알림 관련 오류"""
    pass

class NetworkError(TimetableError):
    """네트워크 관련 오류"""
    pass

class DisplayError(TimetableError):
    """화면 표시 관련 오류"""
    pass

def handle_exception(exc_type, exc_value, exc_traceback):
    """전역 예외 처리기"""
    import logging
    import sys
    import traceback
    from PyQt5.QtWidgets import QMessageBox
    
    logger = logging.getLogger(__name__)
    
    # 로그에 자세한 정보 기록
    logger.error("Uncaught exception", 
                 exc_info=(exc_type, exc_value, exc_traceback))
    
    # 사용자 친화적인 메시지 표시
    error_msg = str(exc_value)
    traceback_str = ''.join(traceback.format_tb(exc_traceback))
    
    # TimetableError이면 사용자 친화적인 메시지 사용
    if isinstance(exc_value, TimetableError) and exc_value.details:
        details = exc_value.details
    else:
        details = traceback_str
    
    # 터미널일 경우와 GUI일 경우 구분
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setText("오류가 발생했습니다")
            msg_box.setInformativeText(error_msg)
            msg_box.setDetailedText(details)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
            logger.error(f"오류: {error_msg}\n{details}")
        else:
            # GUI가 없으면 콘솔에 출력
            logger.error(f"오류: {error_msg}\n{details}", file=sys.stderr)
    except:
        # GUI 초기화에 실패했을 경우 콘솔에 출력
        logger.error(f"오류: {error_msg}\n{details}", file=sys.stderr)
