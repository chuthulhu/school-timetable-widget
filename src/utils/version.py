"""
버전 관리 모듈
- 시맨틱 버저닝을 사용하여 애플리케이션 버전을 관리합니다.
- MAJOR.MINOR.PATCH 형식을 사용합니다.
  * MAJOR: 호환되지 않는 API 변경 시
  * MINOR: 이전 버전과 호환되는 기능 추가 시
  * PATCH: 이전 버전과 호환되는 버그 수정 시
"""

# 애플리케이션 버전
__version__ = "1.0.0"

# 버전 구성 요소
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0

# 버전 문자열
VERSION_STRING = f"v{__version__}"

def get_version():
    """현재 애플리케이션 버전 반환"""
    return __version__

def get_version_string():
    """사용자에게 표시할 버전 문자열 반환"""
    return VERSION_STRING
