"""
버전 정보 관리
"""

# 현재 버전 (MAJOR.MINOR.PATCH)
VERSION = "1.0.0"

# 버전 히스토리
VERSION_HISTORY = {
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
