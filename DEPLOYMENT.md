# 견우물류 타임테이블 배포 가이드

## 📦 배포 파일 생성 방법

### 사전 요구사항

1. **Python 3.11 이상**
2. **PyInstaller**
   ```bash
   pip install pyinstaller
   ```

3. **Inno Setup 6** (Windows 설치 파일 생성용)
   - 다운로드: https://jrsoftware.org/isdl.php
   - 선택사항이지만 권장됨

### 빌드 방법

#### 옵션 1: 자동 빌드 (권장)

관리자 권한으로 배치 파일을 실행:

```bash
# 마우스 오른쪽 버튼 -> "관리자 권한으로 실행"
build_installer.bat
```

이 스크립트는 다음 작업을 수행합니다:
1. PyInstaller로 실행 파일 빌드
2. 배포 패키지 생성 (ZIP)
3. Inno Setup으로 설치 파일 생성 (설치되어 있는 경우)

#### 옵션 2: 수동 빌드

**1단계: 실행 파일 빌드**

```bash
python build_exe.py
```

생성되는 파일:
- `dist/견우물류타임테이블.exe` - 실행 파일
- `dist/LogisticsTimetable_v1.0.0_YYYYMMDD/` - 배포 폴더
- `dist/LogisticsTimetable_v1.0.0_YYYYMMDD.zip` - 배포 ZIP

**2단계: 설치 파일 생성** (선택사항)

Inno Setup이 설치되어 있는 경우:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

생성되는 파일:
- `dist/견우물류타임테이블_v1.0.0_Setup.exe` - Windows 설치 파일

---

## 📋 배포 파일 구조

### ZIP 배포 (간편 배포)

```
LogisticsTimetable_v1.0.0_20260116.zip
├── 견우물류타임테이블.exe         # 실행 파일
├── db_config_template.py          # 설정 파일 템플릿
├── README.md                      # 사용자 매뉴얼
├── 설치가이드.txt                 # 설치 안내
└── data/                          # 데이터 폴더 (비어있음)
```

### 설치 파일 배포 (권장)

```
견우물류타임테이블_v1.0.0_Setup.exe
```

설치 파일 실행 시 자동으로:
- 프로그램 파일 복사
- 데이터베이스 설정 입력
- 바로가기 생성
- 레지스트리 등록

---

## 🚀 사용자 설치 가이드

### 방법 1: 설치 파일 사용 (권장)

1. **설치 파일 실행**
   - `견우물류타임테이블_v1.0.0_Setup.exe` 더블클릭

2. **설치 마법사 따라가기**
   - 설치 위치 선택 (기본: `C:\Program Files\견우물류 타임테이블`)
   - 데이터베이스 정보 입력:
     - SQL Server 주소 (예: localhost)
     - 데이터베이스 이름 (예: LogisticsDB)
     - Windows 인증 또는 SQL Server 인증 선택
   - 바로가기 생성 옵션 선택

3. **설치 완료**
   - "프로그램 실행" 체크하여 바로 시작 가능

### 방법 2: ZIP 파일 사용

1. **압축 해제**
   - ZIP 파일을 원하는 위치에 압축 해제

2. **데이터베이스 설정**
   - `db_config.py` 파일 생성 (또는 `db_config_template.py` 복사)
   - 데이터베이스 연결 정보 입력:

   **Windows 인증:**
   ```python
   DB_CONFIG = {
       'server': 'localhost',
       'database': 'LogisticsDB',
       'trusted_connection': 'yes',
       'driver': '{ODBC Driver 17 for SQL Server}'
   }
   ```

   **SQL Server 인증:**
   ```python
   DB_CONFIG = {
       'server': 'localhost',
       'database': 'LogisticsDB',
       'username': 'sa',
       'password': 'your_password',
       'driver': '{ODBC Driver 17 for SQL Server}'
   }
   ```

3. **프로그램 실행**
   - `견우물류타임테이블.exe` 더블클릭

---

## 🔧 사전 요구사항 (사용자 시스템)

### 필수 구성요소

1. **Windows 10 이상**

2. **ODBC Driver 17 for SQL Server**
   - 다운로드: https://learn.microsoft.com/ko-kr/sql/connect/odbc/download-odbc-driver-for-sql-server
   - 설치 파일: `msodbcsql.msi`

3. **SQL Server 데이터베이스**
   - SQL Server 2016 이상 (Express 버전도 가능)
   - 미리 데이터베이스 생성 필요:
     ```sql
     CREATE DATABASE LogisticsDB;
     ```
   - 테이블은 프로그램 첫 실행 시 자동 생성됨

### 선택 구성요소

- **관리자 권한**: 처음 실행 시 테이블 생성을 위해 필요할 수 있음

---

## 🔍 문제 해결

### 데이터베이스 연결 오류

**증상:** "데이터베이스 연결 실패" 메시지

**해결방법:**
1. SQL Server 서비스가 실행 중인지 확인
2. `db_config.py` 파일이 실행 파일과 같은 폴더에 있는지 확인
3. 데이터베이스 서버 주소와 인증 정보 확인
4. 방화벽에서 SQL Server 포트(1433) 허용 확인
5. SQL Server가 TCP/IP 연결을 허용하는지 확인

### ODBC Driver 오류

**증상:** "ODBC Driver 17 for SQL Server를 찾을 수 없습니다" 메시지

**해결방법:**
1. ODBC Driver 17 설치 확인
2. 다운로드: https://learn.microsoft.com/ko-kr/sql/connect/odbc/download-odbc-driver-for-sql-server
3. 설치 후 컴퓨터 재시작

### 프로그램이 실행되지 않음

**증상:** 더블클릭해도 아무 반응이 없거나 즉시 종료됨

**해결방법:**
1. Windows Defender나 백신 프로그램 예외 추가
2. 관리자 권한으로 실행
3. 실행 파일과 같은 폴더에 있는 `logs` 폴더의 오류 로그 확인

### 테이블이 생성되지 않음

**증상:** "테이블을 찾을 수 없습니다" 오류

**해결방법:**
1. 데이터베이스 사용자가 CREATE TABLE 권한이 있는지 확인
2. 관리자 권한으로 프로그램 실행
3. SQL Server Management Studio에서 수동으로 테이블 생성 스크립트 실행

---

## 📱 업데이트 배포

### 새 버전 배포 프로세스

1. **버전 정보 업데이트**
   - `version.py`에서 `VERSION` 변경
   - `VERSION_HISTORY`에 변경사항 추가

2. **빌드 실행**
   ```bash
   build_installer.bat
   ```

3. **GitHub 릴리스 생성**
   - 저장소의 "Releases" 페이지에서 "Draft a new release" 클릭
   - Tag: `v1.0.1` (버전 번호)
   - Release title: "v1.0.1 - 업데이트 내용 요약"
   - Description: 변경사항 자세히 설명
   - 빌드된 ZIP 파일 또는 설치 파일 첨부
   - "Publish release" 클릭

4. **자동 업데이트**
   - 사용자가 프로그램 실행 시 자동으로 업데이트 확인
   - "업데이트 확인" 다이얼로그 표시
   - 사용자가 "지금 업데이트" 선택 시 자동 다운로드 및 설치

### 수동 업데이트

사용자가 프로그램 메뉴에서:
1. "도움말" → "업데이트 확인" 클릭
2. 새 버전이 있으면 다이얼로그 표시
3. "지금 업데이트" 클릭하여 설치

---

## 🔐 보안 고려사항

### 데이터베이스 인증 정보

- `db_config.py` 파일은 **배포하지 않음**
- 각 사용자가 자신의 환경에 맞게 생성
- 설치 파일 사용 시 설치 과정에서 자동 생성
- `.gitignore`에 `db_config.py` 추가하여 Git에서 제외

### 실행 파일 서명

프로덕션 배포 시 권장사항:
1. 코드 사이닝 인증서 획득
2. `signtool.exe`로 실행 파일 서명
   ```bash
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com 견우물류타임테이블.exe
   ```

---

## 📞 지원

### 기술 지원 연락처

- IT 관리자: [이메일/전화번호]
- 개발팀: [이메일/전화번호]

### 로그 파일 위치

- 실행 파일과 같은 폴더의 `logs` 폴더
- 오류 발생 시 로그 파일을 지원팀에 전달

---

## 📄 라이선스

[라이선스 정보 추가]

---

**견우물류 타임테이블 v1.0.0**
