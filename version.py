"""
버전 정보 관리
"""

# 현재 버전 (MAJOR.MINOR.PATCH)
VERSION = "1.0.1"

# 버전 히스토리
VERSION_HISTORY = {
    "1.0.1": {
        "date": "2026-01-18",
        "changes": [
            "점심시간(12:30~13:00) 빗금 표시 추가",
            "MAC 주소 기반 자동 로그인 기능",
            "DB 접속 정보 암호화 (db_config.enc)",
            "로그인 UI 개선 (밝은 테마, 로고 추가)",
            "IME 자동 전환 (ID: 한글, PW: 영문)",
            "변경 로그 날짜 필터 수정"
        ]
    },
    "1.0.0": {
        "date": "2026-01-16",
        "changes": [
            "초기 릴리스",
            "기본 업무 관리 기능",
            "특수 시간 관리 (드래그로 셀 토글)",
            "법인별 추가 시간 합계 표시",
            "기간별 통계 기능",
            "실시간 자동 재계산"
        ]
    }
}

def get_version():
    """현재 버전 반환"""
    return VERSION

def get_version_info(version=None):
    """특정 버전의 정보 반환"""
    if version is None:
        version = VERSION
    return VERSION_HISTORY.get(version, {})

def get_latest_changes():
    """최신 버전의 변경사항 반환"""
    return VERSION_HISTORY.get(VERSION, {}).get("changes", [])
