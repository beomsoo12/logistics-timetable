"""
자동 업데이트 기능
GitHub 릴리스를 확인하고 새 버전을 다운로드하여 설치
"""

import os
import sys
import json
import tempfile
from urllib import request, error
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from version import VERSION


def write_update_log(message):
    """업데이트 로그 파일에 기록"""
    try:
        if getattr(sys, 'frozen', False):
            log_dir = os.path.dirname(sys.executable)
        else:
            log_dir = os.path.dirname(os.path.abspath(__file__))

        log_path = os.path.join(log_dir, "update_log.txt")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass


class Updater:
    """자동 업데이트 관리 클래스"""

    # GitHub 저장소 정보
    GITHUB_USER = "beomsoo12"
    GITHUB_REPO = "logistics-timetable"

    def __init__(self):
        self.current_version = VERSION
        self.latest_version = None
        self.download_url = None
        self.release_notes = None

    def check_for_updates(self, silent=False):
        """
        업데이트 확인

        Args:
            silent (bool): True이면 업데이트가 없을 때 메시지 표시 안 함

        Returns:
            bool: 업데이트가 있으면 True, 없으면 False
        """
        write_update_log(f"업데이트 확인 시작 - 현재 버전: {self.current_version}")

        try:
            api_url = f"https://api.github.com/repos/{self.GITHUB_USER}/{self.GITHUB_REPO}/releases/latest"
            write_update_log(f"API 호출: {api_url}")

            req = request.Request(api_url)
            req.add_header('User-Agent', 'LogisticsTimetable-Updater')

            with request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                self.latest_version = data.get('tag_name', '').lstrip('v')
                self.release_notes = data.get('body', '')

                assets = data.get('assets', [])
                if assets:
                    self.download_url = assets[0].get('browser_download_url')

                write_update_log(f"최신 버전: {self.latest_version}, 현재 버전: {self.current_version}")

                compare_result = self._compare_versions(self.latest_version, self.current_version)

                if compare_result > 0:
                    write_update_log("업데이트 필요")
                    return True
                else:
                    write_update_log("최신 버전 사용 중")
                    if not silent:
                        messagebox.showinfo(
                            "업데이트 확인",
                            f"현재 최신 버전을 사용 중입니다.\n\n현재 버전: v{self.current_version}"
                        )
                    return False

        except error.URLError as e:
            write_update_log(f"URLError: {str(e)}")
            if not silent:
                messagebox.showwarning(
                    "업데이트 확인 실패",
                    f"업데이트 확인 중 오류가 발생했습니다.\n\n인터넷 연결을 확인해주세요."
                )
            return False
        except Exception as e:
            write_update_log(f"예외: {str(e)}")
            if not silent:
                messagebox.showerror("오류", f"업데이트 확인 중 오류: {str(e)}")
            return False

    def _compare_versions(self, version1, version2):
        """버전 비교"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]

            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            for i in range(max_len):
                if v1_parts[i] > v2_parts[i]:
                    return 1
                elif v1_parts[i] < v2_parts[i]:
                    return -1
            return 0
        except:
            return 0

    def show_update_dialog(self, parent=None):
        """
        업데이트 확인 다이얼로그 표시

        Returns:
            bool: 사용자가 업데이트를 선택하면 True
        """
        write_update_log("업데이트 다이얼로그 표시")

        dialog = tk.Toplevel()
        dialog.title("업데이트 확인")
        dialog.geometry("450x300")
        dialog.resizable(False, False)

        # 화면 중앙 배치
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 300) // 2
        dialog.geometry(f"450x300+{x}+{y}")

        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)

        result = {"update": False}

        def on_update():
            result["update"] = True
            dialog.destroy()

        def on_skip():
            result["update"] = False
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_skip)
        dialog.grab_set()

        # UI 구성
        tk.Label(
            dialog,
            text=f"새 버전이 있습니다!",
            font=("맑은 고딕", 14, "bold"),
            fg="#2980b9"
        ).pack(pady=(20, 10))

        info_frame = tk.Frame(dialog)
        info_frame.pack(pady=10)

        tk.Label(info_frame, text=f"현재 버전: v{self.current_version}", font=("맑은 고딕", 10)).pack()
        tk.Label(info_frame, text=f"최신 버전: v{self.latest_version}", font=("맑은 고딕", 10, "bold"), fg="#27ae60").pack()

        # 변경사항
        tk.Label(dialog, text="변경 사항:", font=("맑은 고딕", 10, "bold")).pack(pady=(15, 5))

        notes_frame = tk.Frame(dialog)
        notes_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        notes_text = tk.Text(notes_frame, wrap=tk.WORD, font=("맑은 고딕", 9), height=5, bg="#f5f5f5")
        notes_text.pack(fill=tk.BOTH, expand=True)
        notes_text.insert("1.0", self.release_notes if self.release_notes else "변경 사항 정보가 없습니다.")
        notes_text.config(state=tk.DISABLED)

        # 버튼
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame, text="업데이트", font=("맑은 고딕", 10, "bold"),
            bg="#27ae60", fg="white", width=10, command=on_update
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame, text="나중에", font=("맑은 고딕", 10),
            bg="#95a5a6", fg="white", width=10, command=on_skip
        ).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result["update"]

    def download_and_install(self, parent=None):
        """
        업데이트 다운로드 및 설치 (배치파일 방식)
        """
        if not self.download_url:
            messagebox.showerror("오류", "다운로드 URL을 찾을 수 없습니다.")
            return False

        write_update_log(f"다운로드 시작: {self.download_url}")

        # 현재 실행 파일 경로
        if getattr(sys, 'frozen', False):
            current_exe = sys.executable
            install_dir = os.path.dirname(current_exe)
        else:
            # 개발 모드
            messagebox.showinfo("개발 모드", "개발 모드에서는 수동으로 업데이트하세요.")
            return False

        # 프로그레스 다이얼로그
        progress_win = tk.Toplevel()
        progress_win.title("업데이트 다운로드")
        progress_win.geometry("400x150")
        progress_win.resizable(False, False)

        x = (progress_win.winfo_screenwidth() - 400) // 2
        y = (progress_win.winfo_screenheight() - 150) // 2
        progress_win.geometry(f"400x150+{x}+{y}")

        progress_win.lift()
        progress_win.attributes('-topmost', True)
        progress_win.grab_set()

        status_label = tk.Label(progress_win, text="다운로드 준비 중...", font=("맑은 고딕", 10))
        status_label.pack(pady=(30, 10))

        progress_bar = ttk.Progressbar(progress_win, length=350, mode='determinate')
        progress_bar.pack(pady=10)

        percent_label = tk.Label(progress_win, text="0%", font=("맑은 고딕", 9))
        percent_label.pack()

        progress_win.update()

        try:
            # 임시 폴더에 다운로드
            temp_dir = tempfile.gettempdir()
            zip_path = os.path.join(temp_dir, "logistics_update.zip")
            extract_dir = os.path.join(temp_dir, "logistics_update_temp")

            # 다운로드
            status_label.config(text="다운로드 중...")
            progress_win.update()

            req = request.Request(self.download_url)
            req.add_header('User-Agent', 'LogisticsTimetable-Updater')

            with request.urlopen(req, timeout=300) as response:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                block_size = 8192

                with open(zip_path, 'wb') as f:
                    while True:
                        chunk = response.read(block_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            progress_bar['value'] = percent
                            percent_label.config(text=f"{percent}% ({downloaded // 1024 // 1024}MB / {total_size // 1024 // 1024}MB)")
                            progress_win.update()

            write_update_log(f"다운로드 완료: {zip_path}")

            status_label.config(text="업데이트 준비 중...")
            progress_bar['value'] = 100
            progress_win.update()

            # 배치 파일 생성
            batch_path = os.path.join(temp_dir, "do_update.bat")

            # 경로에서 백슬래시 이스케이프 처리
            install_dir_bat = install_dir.replace('/', '\\')
            zip_path_bat = zip_path.replace('/', '\\')
            extract_dir_bat = extract_dir.replace('/', '\\')

            batch_content = f'''@echo off
chcp 949 >nul
echo.
echo ========================================
echo   Logistics Timetable Update v{self.latest_version}
echo ========================================
echo.
echo Waiting for program to close...
timeout /t 3 /nobreak >nul

echo.
echo Extracting update files...
if exist "{extract_dir_bat}" rmdir /s /q "{extract_dir_bat}"
powershell -Command "Expand-Archive -Path '{zip_path_bat}' -DestinationPath '{extract_dir_bat}' -Force"

echo.
echo Copying files...
REM Check if EXE exists directly in extract folder
if exist "{extract_dir_bat}\\LogisticsTimetable.exe" (
    xcopy "{extract_dir_bat}\\*.*" "{install_dir_bat}\\" /E /H /Y /Q >nul 2>&1
) else (
    REM EXE is in a subfolder
    for /d %%i in ("{extract_dir_bat}\\*") do (
        if exist "%%i\\LogisticsTimetable.exe" (
            xcopy "%%i\\*.*" "{install_dir_bat}\\" /E /H /Y /Q >nul 2>&1
        )
    )
)

echo.
echo Cleaning up...
del /f /q "{zip_path_bat}" >nul 2>&1
rmdir /s /q "{extract_dir_bat}" >nul 2>&1

echo.
echo ========================================
echo   Update complete! Starting program...
echo ========================================
echo.
timeout /t 2 /nobreak >nul

start "" "{install_dir_bat}\\LogisticsTimetable.exe"
del "%~f0"
'''

            with open(batch_path, 'w', encoding='cp949') as f:
                f.write(batch_content)

            write_update_log(f"배치 파일 생성: {batch_path}")
            progress_win.destroy()

            # 사용자에게 알림
            messagebox.showinfo(
                "업데이트",
                f"v{self.latest_version} 업데이트를 설치합니다.\n\n"
                "프로그램이 종료되고 업데이트가 진행됩니다.\n"
                "업데이트 완료 후 자동으로 재시작됩니다."
            )

            write_update_log("배치 파일 실행")

            # 배치 파일 실행 (새 창에서)
            os.startfile(batch_path)

            # 메인 프로그램 종료
            write_update_log("메인 프로그램 종료")
            if parent:
                try:
                    parent.destroy()
                except:
                    pass
            sys.exit(0)

        except Exception as e:
            write_update_log(f"업데이트 실패: {str(e)}")
            try:
                progress_win.destroy()
            except:
                pass
            messagebox.showerror("업데이트 실패", f"업데이트 중 오류가 발생했습니다.\n\n{str(e)}")
            return False

    def check_and_update(self, parent=None, auto=True):
        """
        업데이트 확인 및 설치 (전체 프로세스)
        """
        write_update_log(f"check_and_update 시작 - auto: {auto}")

        # 업데이트 확인
        has_update = self.check_for_updates(silent=auto)

        if not has_update:
            return False

        # 사용자에게 업데이트 여부 확인
        user_accepted = self.show_update_dialog(parent)

        if user_accepted:
            write_update_log("사용자가 업데이트 승인")
            return self.download_and_install(parent)

        write_update_log("사용자가 업데이트 거부")
        return False


def check_for_updates_on_startup(parent=None):
    """프로그램 시작 시 자동으로 업데이트 확인"""
    updater = Updater()
    updater.check_and_update(parent, auto=True)


def manual_update_check(parent=None):
    """수동으로 업데이트 확인 (메뉴에서 호출)"""
    updater = Updater()
    updater.check_and_update(parent, auto=False)
