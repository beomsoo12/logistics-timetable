@echo off
chcp 65001 >nul
echo ==========================================
echo 견우물류 타임테이블 설치 파일 빌드 스크립트
echo ==========================================
echo.

REM 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [오류] 이 스크립트는 관리자 권한으로 실행해야 합니다.
    echo 마우스 오른쪽 버튼 클릭 후 "관리자 권한으로 실행"을 선택하세요.
    pause
    exit /b 1
)

REM 1단계: PyInstaller로 실행 파일 빌드
echo [1/3] PyInstaller로 실행 파일을 빌드합니다...
echo.
python build_exe.py
if %errorLevel% neq 0 (
    echo.
    echo [오류] 실행 파일 빌드 실패!
    pause
    exit /b 1
)

echo.
echo [2/3] 실행 파일 빌드 완료!
echo.

REM 2단계: Inno Setup 설치 확인
echo [3/3] Inno Setup으로 설치 파일을 생성합니다...
echo.

REM Inno Setup 경로 찾기
set INNO_PATH=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set INNO_PATH=C:\Program Files\Inno Setup 6\ISCC.exe
) else (
    echo [경고] Inno Setup 6가 설치되어 있지 않습니다.
    echo.
    echo Inno Setup 다운로드: https://jrsoftware.org/isdl.php
    echo.
    echo PyInstaller 빌드는 완료되었습니다.
    echo dist 폴더에서 실행 파일을 확인하세요.
    pause
    exit /b 0
)

REM 3단계: Inno Setup으로 설치 파일 생성
"%INNO_PATH%" installer.iss
if %errorLevel% neq 0 (
    echo.
    echo [오류] 설치 파일 생성 실패!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 빌드 완료!
echo ==========================================
echo.
echo 생성된 파일:
echo - 실행 파일: dist\견우물류타임테이블.exe
echo - 설치 파일: dist\견우물류타임테이블_v1.0.0_Setup.exe
echo.
echo 설치 파일을 사용자에게 전달하세요.
echo.
pause
