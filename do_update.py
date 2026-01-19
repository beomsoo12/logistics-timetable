"""
업데이트 전용 프로그램
메인 프로그램 종료 후 ZIP 압축 해제 및 재실행
"""

import os
import sys
import time
import shutil
import zipfile
import subprocess
from datetime import datetime

# 설정
UPDATE_DIR = r"C:\gyunwoo\update"
INSTALL_DIR = r"C:\gyunwoo\logistics"
ZIP_FILE = os.path.join(UPDATE_DIR, "update.zip")
EXE_NAME = "LogisticsTimetable.exe"
LOG_FILE = os.path.join(UPDATE_DIR, "update_log.txt")


def write_log(message):
    """로그 기록"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass
    print(message)


def wait_for_main_exit(max_wait=30):
    """메인 프로그램 종료 대기"""
    target_exe = os.path.join(INSTALL_DIR, EXE_NAME)

    write_log(f"메인 프로그램 종료 대기 중...")

    for i in range(max_wait):
        # 파일이 사용 중인지 확인 (삭제 시도)
        try:
            if os.path.exists(target_exe):
                # 파일 열기 시도로 잠금 확인
                with open(target_exe, 'r+b'):
                    pass
                write_log(f"메인 프로그램 종료 확인 ({i+1}초)")
                return True
            else:
                write_log("EXE 파일 없음 - 신규 설치")
                return True
        except (IOError, PermissionError):
            write_log(f"대기 중... ({i+1}/{max_wait})")
            time.sleep(1)

    write_log("경고: 타임아웃 - 강제 진행")
    return False


def clean_install_folder():
    """설치 폴더 정리 (db_config.enc 제외)"""
    write_log("설치 폴더 정리 중...")

    if not os.path.exists(INSTALL_DIR):
        os.makedirs(INSTALL_DIR, exist_ok=True)
        write_log("설치 폴더 생성 완료")
        return True

    try:
        # 파일 삭제 (db_config.enc 제외)
        for item in os.listdir(INSTALL_DIR):
            item_path = os.path.join(INSTALL_DIR, item)

            # db_config.enc는 보존
            if item.lower() == 'db_config.enc':
                write_log(f"  보존: {item}")
                continue

            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    write_log(f"  폴더 삭제: {item}")
                else:
                    os.remove(item_path)
                    write_log(f"  파일 삭제: {item}")
            except Exception as e:
                write_log(f"  삭제 실패: {item} - {e}")

        return True
    except Exception as e:
        write_log(f"폴더 정리 오류: {e}")
        return False


def extract_update():
    """ZIP 파일 압축 해제"""
    write_log(f"ZIP 파일 압축 해제 중: {ZIP_FILE}")

    if not os.path.exists(ZIP_FILE):
        write_log(f"오류: ZIP 파일 없음 - {ZIP_FILE}")
        return False

    try:
        with zipfile.ZipFile(ZIP_FILE, 'r') as zf:
            zf.extractall(INSTALL_DIR)
        write_log("압축 해제 완료")

        # ZIP 내부에 폴더가 있으면 상위로 이동
        for item in os.listdir(INSTALL_DIR):
            item_path = os.path.join(INSTALL_DIR, item)
            exe_in_folder = os.path.join(item_path, EXE_NAME)

            if os.path.isdir(item_path) and os.path.exists(exe_in_folder):
                write_log(f"내부 폴더 발견: {item}")

                # 폴더 내용을 상위로 이동
                for sub_item in os.listdir(item_path):
                    src = os.path.join(item_path, sub_item)
                    dst = os.path.join(INSTALL_DIR, sub_item)

                    if os.path.exists(dst):
                        if os.path.isdir(dst):
                            shutil.rmtree(dst)
                        else:
                            os.remove(dst)

                    shutil.move(src, dst)

                # 빈 폴더 삭제
                shutil.rmtree(item_path)
                write_log("파일 이동 완료")
                break

        return True
    except Exception as e:
        write_log(f"압축 해제 오류: {e}")
        return False


def cleanup():
    """정리 작업"""
    write_log("정리 작업 중...")

    # ZIP 파일 삭제
    try:
        if os.path.exists(ZIP_FILE):
            os.remove(ZIP_FILE)
            write_log("ZIP 파일 삭제 완료")
    except Exception as e:
        write_log(f"ZIP 파일 삭제 실패: {e}")


def launch_main_program():
    """메인 프로그램 실행"""
    target_exe = os.path.join(INSTALL_DIR, EXE_NAME)

    if not os.path.exists(target_exe):
        write_log(f"오류: EXE 파일 없음 - {target_exe}")
        return False

    write_log(f"메인 프로그램 실행: {target_exe}")

    try:
        # 설치 폴더에서 프로그램 실행
        subprocess.Popen(
            [target_exe],
            cwd=INSTALL_DIR,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        write_log("프로그램 실행 완료")
        return True
    except Exception as e:
        write_log(f"프로그램 실행 오류: {e}")
        return False


def main():
    """메인 업데이트 프로세스"""
    write_log("=" * 50)
    write_log("업데이트 프로세스 시작")
    write_log("=" * 50)

    # 1. 메인 프로그램 종료 대기
    wait_for_main_exit()

    # 2. 설치 폴더 정리
    if not clean_install_folder():
        write_log("설치 폴더 정리 실패")
        input("엔터를 눌러 종료...")
        return

    # 3. 압축 해제
    if not extract_update():
        write_log("압축 해제 실패")
        input("엔터를 눌러 종료...")
        return

    # 4. 정리
    cleanup()

    # 5. 메인 프로그램 실행
    if not launch_main_program():
        write_log("프로그램 실행 실패")
        input("엔터를 눌러 종료...")
        return

    write_log("=" * 50)
    write_log("업데이트 완료!")
    write_log("=" * 50)

    # 잠시 대기 후 종료
    time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        write_log(f"치명적 오류: {e}")
        input("엔터를 눌러 종료...")
