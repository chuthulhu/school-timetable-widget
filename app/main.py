import sys
import os
from PyQt5.QtWidgets import QApplication

# Ensure project root (containing app/core/infra) is on sys.path when running as a script
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from infra.logging import setup_logging
from infra.settings import load_config
from infra.updater import Updater
from app.widget import TimetableWidget
from app.tray_icon import TrayIcon
from infra.version import get_version_string


def main() -> int:
    logger = setup_logging()
    logger.info(f"학교 시간표 위젯 v{get_version_string()} 시작")
    cfg, created = load_config()
    if created:
        logger.info("기본 설정 파일 생성 완료")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # 비동기 업데이트 체크 (알림 없이 로그만 남김)
    def _check_update():
        try:
            up = Updater()
            if up.check_for_update():
                logger.info(f"새 릴리즈 감지: {up.latest_version}")
        except Exception as e:
            logger.warning(f"업데이트 확인 실패: {e}")

    from PyQt5.QtCore import QTimer
    QTimer.singleShot(1000, _check_update)

    widget = TimetableWidget()
    widget.show()

    tray = TrayIcon(widget)
    tray.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())


