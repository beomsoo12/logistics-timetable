"""
PyInstaller를 사용한 실행 파일 빌드 스크립트
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def clean_build_folders():
    """이전 빌드 폴더 정리"""
    print("이전 빌드 폴더를 정리합니다...")
    folders_to_clean = ['build', 'dist', '__pycache__']

    for folder in folders_to_clean:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print(f"  - {folder} 폴더 삭제 완료")

    # .spec 파일 삭제
    spec_files = [f for f in os.listdir('.') if f.endswith('.spec')]
    for spec_file in spec_files:
        os.remove(spec_file)
        print(f"  - {spec_file} 삭제 완료")

def build_executable():
    """PyInstaller로 메인 실행 파일 빌드"""
    print("\n메인 실행 파일을 빌드합니다...")

    # 아이콘 파일 확인
    icon_file = 'app_icon.ico'
    icon_option = f'--icon={icon_file}' if os.path.exists(icon_file) else '--icon=NONE'

    # PyInstaller 명령어 구성 (영문 이름 사용 - 백신 호환성)
    # --onedir 모드 사용 (DLL 오류 방지)
    cmd = [
        'pyinstaller',
        '--name=LogisticsTimetable',
        '--onedir',  # 폴더로 생성 (DLL 오류 방지)
        '--windowed',  # GUI 앱 (콘솔 숨김)
        icon_option,  # 아이콘
        '--add-data=version.py;.',  # 버전 파일 포함
        '--hidden-import=pyodbc',
        '--hidden-import=tkcalendar',
        '--hidden-import=babel.numbers',
        '--hidden-import=urllib.request',
        '--hidden-import=urllib.error',
        '--hidden-import=cryptography',
        '--hidden-import=cryptography.fernet',
        '--hidden-import=openpyxl',
        '--collect-all=tkcalendar',
        '--collect-all=cryptography',
        'main.py'
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
        print("[OK] 메인 프로그램 빌드 성공!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 메인 프로그램 빌드 실패: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False



def create_distribution_package():
    """배포 패키지 생성"""
    print("\n배포 패키지를 생성합니다...")

    # 배포 폴더 이름
    dist_name = f"LogisticsTimetable_v1.3.8_{datetime.now().strftime('%Y%m%d')}"
    dist_folder = os.path.join('dist', dist_name)

    # 배포 폴더 생성
    os.makedirs(dist_folder, exist_ok=True)

    # onedir 모드: 폴더 전체 복사
    onedir_path = os.path.join('dist', 'LogisticsTimetable')
    if os.path.exists(onedir_path):
        # 폴더 내 모든 파일 복사
        for item in os.listdir(onedir_path):
            src = os.path.join(onedir_path, item)
            dst = os.path.join(dist_folder, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        print(f"  [OK] 프로그램 폴더 복사 완료")
    else:
        print(f"  [ERROR] 빌드된 폴더를 찾을 수 없습니다: {onedir_path}")
        return None

    # 아이콘 파일 복사
    icon_file = 'app_icon.ico'
    if os.path.exists(icon_file):
        shutil.copy2(icon_file, dist_folder)
        print(f"  [OK] 아이콘 파일 복사 완료")

    # 암호화된 DB 설정 파일 복사 (필수)
    enc_config = 'db_config.enc'
    if os.path.exists(enc_config):
        shutil.copy2(enc_config, dist_folder)
        print(f"  [OK] 암호화된 DB 설정 파일 복사 완료")
    else:
        print(f"  [WARNING] 암호화된 DB 설정 파일이 없습니다: {enc_config}")

    # 설정 파일 템플릿 복사
    config_template = 'db_config.py'
    if os.path.exists(config_template):
        shutil.copy2(config_template, os.path.join(dist_folder, 'db_config_template.py'))
        print(f"  [OK] 설정 파일 템플릿 복사 완료")

    # README 복사
    if os.path.exists('README.md'):
        shutil.copy2('README.md', dist_folder)
        print(f"  [OK] README 파일 복사 완료")

    # 설치 가이드 생성
    create_install_guide(dist_folder)

    # 데이터 폴더 생성
    data_folder = os.path.join(dist_folder, 'data')
    os.makedirs(data_folder, exist_ok=True)
    print(f"  [OK] data 폴더 생성 완료")


    # ZIP 파일로 압축
    print("\n배포 패키지를 압축합니다...")
    zip_path = shutil.make_archive(
        os.path.join('dist', dist_name),
        'zip',
        os.path.join('dist', dist_name)
    )
    print(f"  [OK] 압축 완료: {zip_path}")

    return dist_folder, zip_path

def create_install_guide(dist_folder):
    """설치 가이드 생성"""
    guide_content = """# 견우물류 타임테이블 설치 가이드

## 📦 설치 방법

### 1. 파일 압축 해제
이 ZIP 파일을 원하는 위치에 압축 해제합니다.

### 2. 데이터베이스 설정
프로그램과 같은 폴더에 `db_config.py` 파일을 생성하고 다음 내용을 입력합니다:

```python
# 데이터베이스 연결 설정
DB_CONFIG = {
    'server': 'localhost',        # SQL Server 주소
    'database': 'LogisticsDB',    # 데이터베이스 이름
    'username': 'sa',             # 사용자명
    'password': 'your_password',  # 비밀번호
    'driver': '{ODBC Driver 17 for SQL Server}'
}
```

**Windows 인증 사용 시:**
```python
DB_CONFIG = {
    'server': 'localhost',
    'database': 'LogisticsDB',
    'trusted_connection': 'yes',
    'driver': '{ODBC Driver 17 for SQL Server}'
}
```

### 3. 사전 요구사항

#### ODBC Driver 설치
MSSQL 연결을 위해 ODBC Driver 17 for SQL Server가 필요합니다.
- 다운로드: https://learn.microsoft.com/ko-kr/sql/connect/odbc/download-odbc-driver-for-sql-server

#### 데이터베이스 생성
MSSQL에서 미리 데이터베이스를 생성해야 합니다:
```sql
CREATE DATABASE LogisticsDB;
```

프로그램을 처음 실행하면 자동으로 필요한 테이블이 생성됩니다.

### 4. 프로그램 실행
`견우물류타임테이블.exe` 파일을 더블클릭하여 실행합니다.

## 🔍 문제 해결

### 데이터베이스 연결 오류
- `db_config.py` 파일이 실행 파일과 같은 폴더에 있는지 확인
- 데이터베이스 서버 주소와 인증 정보 확인
- SQL Server 서비스가 실행 중인지 확인
- 방화벽에서 SQL Server 포트(1433) 허용 확인

### ODBC Driver 오류
- ODBC Driver 17 for SQL Server 설치 확인
- `db_config.py`의 driver 설정 확인

### 프로그램이 실행되지 않음
- Windows Defender나 백신 프로그램에서 차단하지 않는지 확인
- 관리자 권한으로 실행 시도

## 📞 지원

문제가 지속되면 IT 관리자에게 문의하세요.

---
견우물류 타임테이블 v1.0.0
"""

    guide_path = os.path.join(dist_folder, '설치가이드.txt')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    print(f"  [OK] 설치 가이드 생성 완료")

def main():
    """메인 빌드 프로세스"""
    print("=" * 60)
    print("견우물류 타임테이블 빌드 스크립트")
    print("=" * 60)

    # 1. 이전 빌드 정리
    clean_build_folders()

    # 2. 메인 실행 파일 빌드
    if not build_executable():
        print("\n메인 프로그램 빌드 실패!")
        return

    # 3. 배포 패키지 생성
    result = create_distribution_package()
    if result:
        dist_folder, zip_path = result
        print("\n" + "=" * 60)
        print("빌드 완료!")
        print("=" * 60)
        print(f"배포 폴더: {os.path.abspath(dist_folder)}")
        print(f"압축 파일: {os.path.abspath(zip_path)}")
        print("\n배포 파일을 사용자에게 전달하세요.")
    else:
        print("\n배포 패키지 생성 실패!")

if __name__ == "__main__":
    # PyInstaller 설치 확인
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller가 설치되어 있지 않습니다.")
        print("다음 명령어로 설치하세요: pip install pyinstaller")
        sys.exit(1)

    main()
