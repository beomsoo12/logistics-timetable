"""
자동 업데이트 기능
GitHub 릴리스를 확인하고 새 버전을 다운로드하여 설치
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
from urllib import request, error
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from version import VERSION

class Updater:
    """자동 업데이트 관리 클래스"""

    # GitHub 저장소 정보 (실제 저장소로 변경 필요)
    GITHUB_USER = "beomsoo12"  # 실제 GitHub 사용자명으로 변경
    GITHUB_REPO = "logistics-timetable"  # 실제 저장소 이름으로 변경

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
        try:
            # GitHub API를 통해 최신 릴리스 정보 가져오기
            api_url = f"https://api.github.com/repos/{self.GITHUB_USER}/{self.GITHUB_REPO}/releases/latest"

            req = request.Request(api_url)
            req.add_header('User-Agent', 'LogisticsTimetable-Updater')

            with request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

                # 최신 버전 정보 추출
                self.latest_version = data.get('tag_name', '').lstrip('v')
                self.release_notes = data.get('body', '')

                # 다운로드 URL 찾기 (첫 번째 asset)
                assets = data.get('assets', [])
                if assets:
                    self.download_url = assets[0].get('browser_download_url')

                # 버전 비교
                if self._compare_versions(self.latest_version, self.current_version) > 0:
                    return True
                else:
                    if not silent:
                        messagebox.showinfo(
                            "업데이트 확인",
                            f"현재 최신 버전을 사용 중입니다.\n\n현재 버전: {self.current_version}"
                        )
                    return False

        except error.URLError as e:
            if not silent:
                messagebox.showwarning(
                    "업데이트 확인 실패",
                    f"업데이트 확인 중 오류가 발생했습니다.\n\n{str(e)}\n\n"
                    "인터넷 연결을 확인하거나 나중에 다시 시도해주세요."
                )
            return False
        except Exception as e:
            if not silent:
                messagebox.showerror(
                    "오류",
                    f"업데이트 확인 중 예상치 못한 오류가 발생했습니다.\n\n{str(e)}"
                )
            return False

    def _compare_versions(self, version1, version2):
        """
        버전 비교

        Args:
            version1 (str): 비교할 첫 번째 버전 (예: "1.2.3")
            version2 (str): 비교할 두 번째 버전 (예: "1.2.0")

        Returns:
            int: version1 > version2이면 1, version1 < version2이면 -1, 같으면 0
        """
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]

            # 길이를 맞추기 (예: 1.2 vs 1.2.0)
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
        업데이트 다이얼로그 표시

        Args:
            parent: 부모 윈도우 (tkinter)

        Returns:
            bool: 사용자가 업데이트를 선택하면 True
        """
        dialog = tk.Toplevel(parent) if parent else tk.Tk()
        dialog.title("업데이트 확인")
        dialog.geometry("600x400")
        dialog.resizable(False, False)

        if parent:
            dialog.transient(parent)
            dialog.grab_set()

        # 제목
        title_label = tk.Label(
            dialog,
            text=f"새로운 버전이 있습니다! (v{self.latest_version})",
            font=("굴림체", 14, "bold"),
            fg="#2980b9"
        )
        title_label.pack(pady=20)

        # 현재 버전 정보
        info_frame = tk.Frame(dialog)
        info_frame.pack(pady=10)

        tk.Label(
            info_frame,
            text=f"현재 버전: v{self.current_version}",
            font=("굴림체", 10)
        ).grid(row=0, column=0, sticky="w", padx=20)

        tk.Label(
            info_frame,
            text=f"최신 버전: v{self.latest_version}",
            font=("굴림체", 10, "bold"),
            fg="#27ae60"
        ).grid(row=1, column=0, sticky="w", padx=20)

        # 릴리스 노트
        notes_label = tk.Label(
            dialog,
            text="변경 사항:",
            font=("굴림체", 10, "bold")
        )
        notes_label.pack(pady=(20, 5))

        # 스크롤 가능한 텍스트
        text_frame = tk.Frame(dialog)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        notes_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("굴림체", 9),
            yscrollcommand=scrollbar.set,
            height=10
        )
        notes_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=notes_text.yview)

        if self.release_notes:
            notes_text.insert("1.0", self.release_notes)
        else:
            notes_text.insert("1.0", "변경 사항 정보가 없습니다.")

        notes_text.config(state=tk.DISABLED)

        # 버튼
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        result = {"update": False}

        def on_update():
            result["update"] = True
            dialog.destroy()

        def on_skip():
            result["update"] = False
            dialog.destroy()

        update_btn = tk.Button(
            button_frame,
            text="지금 업데이트",
            font=("굴림체", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=on_update,
            cursor="hand2",
            width=15,
            padx=10,
            pady=5
        )
        update_btn.pack(side=tk.LEFT, padx=10)

        skip_btn = tk.Button(
            button_frame,
            text="나중에",
            font=("굴림체", 10),
            bg="#95a5a6",
            fg="white",
            command=on_skip,
            cursor="hand2",
            width=15,
            padx=10,
            pady=5
        )
        skip_btn.pack(side=tk.LEFT, padx=10)

        # 다이얼로그 중앙 배치
        if parent:
            dialog.update_idletasks()
            x = parent.winfo_x() + (parent.winfo_width() - dialog.winfo_width()) // 2
            y = parent.winfo_y() + (parent.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")

        dialog.wait_window()
        return result["update"]

    def download_and_install(self, parent=None):
        """
        업데이트 다운로드 및 설치

        Args:
            parent: 부모 윈도우

        Returns:
            bool: 성공하면 True
        """
        if not self.download_url:
            messagebox.showerror("오류", "다운로드 URL을 찾을 수 없습니다.")
            return False

        try:
            # 프로그레스 다이얼로그
            progress_dialog = tk.Toplevel(parent) if parent else tk.Tk()
            progress_dialog.title("업데이트 중...")
            progress_dialog.geometry("400x150")
            progress_dialog.resizable(False, False)

            if parent:
                progress_dialog.transient(parent)
                progress_dialog.grab_set()

                # 중앙 배치
                progress_dialog.update_idletasks()
                x = parent.winfo_x() + (parent.winfo_width() - 400) // 2
                y = parent.winfo_y() + (parent.winfo_height() - 150) // 2
                progress_dialog.geometry(f"+{x}+{y}")

            status_label = tk.Label(
                progress_dialog,
                text="업데이트를 다운로드하고 있습니다...",
                font=("굴림체", 10)
            )
            status_label.pack(pady=30)

            progress_label = tk.Label(
                progress_dialog,
                text="0%",
                font=("굴림체", 9)
            )
            progress_label.pack()

            progress_dialog.update()

            # 현재 실행 경로 확인
            if getattr(sys, 'frozen', False):
                # PyInstaller EXE 실행 파일인 경우
                current_exe = sys.executable
                current_dir = os.path.dirname(current_exe)
                is_exe = True
            else:
                # 일반 Python 스크립트인 경우
                current_dir = os.path.dirname(os.path.abspath(__file__))
                is_exe = False

            # 임시 디렉토리에 다운로드
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")

            # 다운로드
            def download_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, int(downloaded * 100 / total_size))
                    progress_label.config(text=f"{percent}%")
                    progress_dialog.update()

            request.urlretrieve(self.download_url, zip_path, download_progress)

            # 압축 해제
            status_label.config(text="압축을 해제하고 있습니다...")
            progress_dialog.update()

            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # 설치
            status_label.config(text="파일을 설치하고 있습니다...")
            progress_dialog.update()

            if is_exe:
                # EXE 파일 업데이트: 폴더 전체 교체 (onedir 모드)
                new_exe = None
                new_icon = None
                new_internal = None
                update_source_dir = None

                # 압축 해제된 폴더에서 EXE, _internal 폴더, ICO 파일 찾기
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith('.exe'):
                            new_exe = os.path.join(root, file)
                            update_source_dir = root
                        elif file.endswith('.ico'):
                            new_icon = os.path.join(root, file)
                    # _internal 폴더 찾기
                    if '_internal' in dirs:
                        new_internal = os.path.join(root, '_internal')

                if new_exe and update_source_dir:
                    # 배치 스크립트를 현재 프로그램 폴더에 생성 (임시 폴더가 아님)
                    batch_path = os.path.join(current_dir, "update_temp.bat")
                    current_internal = os.path.join(current_dir, "_internal")

                    # 폴더 전체 교체 방식으로 업데이트
                    batch_content = f'''@echo off
chcp 65001 >nul
echo ============================================
echo 업데이트를 설치하고 있습니다...
echo ============================================
echo 현재 폴더: {current_dir}
echo 업데이트 소스: {update_source_dir}
cd /d "{current_dir}"
timeout /t 3 /nobreak >nul

:retry
del "{current_exe}" 2>nul
if exist "{current_exe}" (
    echo 프로그램 종료 대기 중...
    timeout /t 2 /nobreak >nul
    goto retry
)

echo.
echo [1/3] 기존 _internal 폴더 삭제 중...
if exist "{current_internal}" (
    rmdir /s /q "{current_internal}"
    timeout /t 1 /nobreak >nul
)

echo [2/3] 새 파일 복사 중...
echo 소스 폴더의 모든 파일을 복사합니다...
xcopy /s /e /y /q "{update_source_dir}\\*.*" "{current_dir}\\"
if errorlevel 1 (
    echo 파일 복사 실패!
    pause
    goto cleanup
)

echo [3/3] 복사 완료 확인 중...
if not exist "{current_exe}" (
    echo EXE 파일이 없습니다!
    pause
    goto cleanup
)

echo.
echo ============================================
echo 업데이트가 완료되었습니다.
echo ============================================
echo 프로그램을 시작합니다...
timeout /t 1 /nobreak >nul
cd /d "{current_dir}"
start "" /D "{current_dir}" "{current_exe}"

:cleanup
echo 임시 파일 정리 중...
rmdir /s /q "{temp_dir}" 2>nul
del "%~f0"
'''

                    with open(batch_path, 'w', encoding='utf-8') as f:
                        f.write(batch_content)

                    progress_dialog.destroy()

                    # 안내 메시지
                    messagebox.showinfo(
                        "업데이트",
                        f"v{self.latest_version} 업데이트를 설치합니다.\n\n"
                        "프로그램이 자동으로 재시작됩니다."
                    )

                    # 배치 스크립트 실행 후 프로그램 종료
                    subprocess.Popen(
                        ['cmd', '/c', batch_path],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )

                    # 프로그램 종료
                    if parent:
                        parent.destroy()
                    sys.exit(0)

                else:
                    raise Exception("업데이트 파일에서 실행 파일을 찾을 수 없습니다.")

            else:
                # Python 스크립트 업데이트: .py 파일 복사
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        # db_config 파일은 제외 (사용자 설정 유지)
                        if file.endswith('.py') and not file.startswith('db_config'):
                            src_path = os.path.join(root, file)
                            dst_path = os.path.join(current_dir, file)

                            # 백업
                            if os.path.exists(dst_path):
                                backup_path = dst_path + '.backup'
                                shutil.copy2(dst_path, backup_path)

                            shutil.copy2(src_path, dst_path)

                        # ico 파일도 복사
                        elif file.endswith('.ico'):
                            src_path = os.path.join(root, file)
                            dst_path = os.path.join(current_dir, file)
                            shutil.copy2(src_path, dst_path)

                # 정리
                shutil.rmtree(temp_dir, ignore_errors=True)

                progress_dialog.destroy()

                # 성공 메시지
                messagebox.showinfo(
                    "업데이트 완료",
                    f"v{self.latest_version} 업데이트가 완료되었습니다.\n\n"
                    "프로그램을 다시 시작해주세요."
                )

            return True

        except Exception as e:
            if 'progress_dialog' in locals():
                try:
                    progress_dialog.destroy()
                except:
                    pass

            messagebox.showerror(
                "업데이트 실패",
                f"업데이트 중 오류가 발생했습니다.\n\n{str(e)}"
            )
            return False

    def check_and_update(self, parent=None, auto=True):
        """
        업데이트 확인 및 설치 (전체 프로세스)

        Args:
            parent: 부모 윈도우
            auto (bool): True이면 자동 체크 (업데이트 없을 때 메시지 안 보임)

        Returns:
            bool: 업데이트가 설치되었으면 True
        """
        # 업데이트 확인
        has_update = self.check_for_updates(silent=auto)

        if not has_update:
            return False

        # 업데이트 다이얼로그 표시
        if self.show_update_dialog(parent):
            # 다운로드 및 설치
            return self.download_and_install(parent)

        return False


def check_for_updates_on_startup(parent=None):
    """
    프로그램 시작 시 자동으로 업데이트 확인

    Args:
        parent: 부모 윈도우
    """
    updater = Updater()
    updater.check_and_update(parent, auto=True)


def manual_update_check(parent=None):
    """
    수동으로 업데이트 확인 (메뉴에서 호출)

    Args:
        parent: 부모 윈도우
    """
    updater = Updater()
    updater.check_and_update(parent, auto=False)
