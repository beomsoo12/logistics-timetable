# 견우물류 업무 타임테이블 (MSSQL DB 연동)

견우물류의 일자별 업무를 시간대별로 관리하는 GUI 프로그램입니다.

## 📋 주요 기능

- **일자별 업무 관리**: 날짜를 선택하여 해당 날짜의 업무를 관리
- **시간대별 업무 등록**: 08:30 ~ 24:00까지 30분 단위 시간대 관리
- **MSSQL 데이터베이스 연동**: 업무 데이터를 안전하게 DB에 저장
- **기본 업무 템플릿**: 업체별/법인별 기본 업무 시간 설정
- **특수 시간 관리**: 드래그로 특수 시간 셀 토글
- **추가 시간 자동 계산**: 기본 시간과 특수 시간의 차이 자동 계산
- **법인별 합계**: 일별/기간별 법인 추가 시간 합계 표시
- **기간별 통계**: 선택한 기간 동안의 법인별 추가 시간 집계
- **날짜 이동**: 이전/다음/오늘 버튼으로 빠른 날짜 이동
- **자동 업데이트**: 프로그램 시작 시 최신 버전 자동 확인
- **색상 구분**: 업체별 색상으로 시각적 구분

## 🔧 설치 방법

### 1. Python 설치
- Python 3.8 이상 필요

### 2. 라이브러리 설치
```bash
pip install -r requirements.txt
```

### 3. ODBC Driver 설치
MSSQL 연결을 위해 ODBC Driver 17 for SQL Server 설치 필요
- 다운로드: https://learn.microsoft.com/ko-kr/sql/connect/odbc/download-odbc-driver-for-sql-server

### 4. 데이터베이스 설정
`db_config.py` 파일을 열어 데이터베이스 연결 정보 수정:

```python
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

### 5. 데이터베이스 생성
MSSQL에서 미리 데이터베이스를 생성해야 합니다:

```sql
CREATE DATABASE LogisticsDB;
```

프로그램을 처음 실행하면 자동으로 필요한 테이블이 생성됩니다.

## 🚀 실행 방법

```bash
python main.py
```

## 📊 데이터베이스 구조

### TimeTable 테이블
```sql
CREATE TABLE TimeTable (
    id INT IDENTITY(1,1) PRIMARY KEY,
    work_date DATE NOT NULL,           -- 작업 날짜
    time_slot VARCHAR(10) NOT NULL,     -- 시간대 (예: 07:00)
    task_name NVARCHAR(200),            -- 업무명
    description NVARCHAR(MAX),          -- 상세 설명
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT UQ_TimeTable_Date_Time UNIQUE(work_date, time_slot)
)
```

## 🎯 사용 방법

### 1. 날짜 선택
- 캘린더 위젯을 클릭하여 날짜 선택
- 또는 이전/다음/오늘 버튼 사용

### 2. 업무 추가
1. 시간대 선택 (콤보박스)
2. 업무명 입력
3. 상세 설명 입력 (선택사항)
4. "업무 추가" 버튼 클릭

### 3. 업무 수정
- 타임테이블에서 수정할 업무를 더블클릭
- 내용 수정 후 "업무 수정" 버튼 클릭

### 4. 업무 삭제
1. 시간대 선택
2. "업무 삭제" 버튼 클릭

### 5. 날짜 복사
- "다른 날짜에서 복사" 버튼 클릭
- 복사할 날짜 선택
- 현재 날짜로 업무가 복사됨

### 6. Excel 내보내기
- "Excel 내보내기" 버튼 클릭
- data 폴더에 날짜별로 Excel 파일 저장 (예: timetable_20260116.xlsx)

## 📁 파일 구조

```
물류업무별타임테이블/
├── main.py                  # GUI 메인 프로그램
├── timetable_manager.py     # 타임테이블 관리 클래스
├── database.py              # 데이터베이스 연결 및 쿼리
├── db_config.py             # 데이터베이스 설정 (수정 필요)
├── version.py               # 버전 정보 관리
├── updater.py               # 자동 업데이트 기능
├── build_exe.py             # 실행 파일 빌드 스크립트
├── installer.iss            # Inno Setup 설치 파일 스크립트
├── build_installer.bat      # 통합 빌드 배치 파일
├── requirements.txt         # 필요 라이브러리 목록
├── README.md               # 사용 설명서
├── DEPLOYMENT.md           # 배포 가이드
└── data/                   # Excel 파일 저장 폴더
    └── timetable_*.xlsx
```

## 🔄 자동 업데이트

프로그램은 시작 시 자동으로 최신 버전을 확인합니다.

### 수동 업데이트 확인
- 메뉴: **도움말 > 업데이트 확인**
- 새 버전이 있으면 변경 사항을 확인하고 업데이트 가능

### 버전 정보 확인
- 메뉴: **도움말 > 버전 정보**
- 현재 버전과 주요 기능 확인 가능

### GitHub 릴리스 설정
자동 업데이트를 활성화하려면 `updater.py`에서 GitHub 정보를 설정하세요:
```python
GITHUB_USER = "your-username"  # GitHub 사용자명
GITHUB_REPO = "logistics-timetable"  # 저장소 이름
```

## ⚠️ 주의사항

1. **데이터베이스 연결**: 프로그램 실행 전 db_config.py 설정 확인
2. **ODBC Driver**: SQL Server ODBC Driver 17 이상 설치 필요
3. **데이터베이스 권한**: 테이블 생성 권한 필요 (CREATE TABLE)
4. **네트워크**: 원격 서버 연결 시 방화벽 확인
5. **자동 업데이트**: GitHub 릴리스 사용 시 인터넷 연결 필요

## 🔍 문제 해결

### 데이터베이스 연결 실패
- db_config.py의 서버 주소, 데이터베이스 이름, 인증 정보 확인
- SQL Server 서비스 실행 중인지 확인
- 방화벽에서 SQL Server 포트(기본 1433) 허용 확인

### ODBC Driver 오류
- ODBC Driver 17 for SQL Server 설치 확인
- db_config.py의 driver 설정 확인

### 한글 깨짐
- 데이터베이스 Collation이 Korean_100_CI_AS 등 한글 지원 확인
- NVARCHAR 타입 사용 확인

## 🏗️ 배포용 파일 생성

개발자가 배포용 실행 파일을 생성하는 방법은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참조하세요.

### 빠른 빌드

관리자 권한으로 실행:

```bash
build_installer.bat
```

이 명령은 다음을 자동으로 수행합니다:
1. PyInstaller로 실행 파일 생성
2. 배포 패키지 (ZIP) 생성
3. Windows 설치 파일 생성 (Inno Setup 필요)

### 생성되는 파일

- `dist/견우물류타임테이블.exe` - 단독 실행 파일
- `dist/LogisticsTimetable_v1.0.0_YYYYMMDD.zip` - 배포용 ZIP 패키지
- `dist/견우물류타임테이블_v1.0.0_Setup.exe` - Windows 설치 파일

자세한 내용은 [DEPLOYMENT.md](DEPLOYMENT.md)를 참조하세요.

## 📝 라이선스

이 프로그램은 견우물류 내부 사용을 위해 제작되었습니다.
