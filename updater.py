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
    GITHUB_USER = "your-username"  # 실제 GitHub 사용자명으로 변경
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

            # 설치 (현재 디렉토리에 파일 복사)
            status_label.config(text="파일을 설치하고 있습니다...")
            progress_dialog.update()

            current_dir = os.path.dirname(os.path.abspath(__file__))

            # .py 파일들만 복사 (데이터베이스 파일 제외)
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.endswith('.py') and not file.startswith('db_config'):
                        src_path = os.path.join(root, file)
                        dst_path = os.path.join(current_dir, file)

                        # 백업
                        if os.path.exists(dst_path):
                            backup_path = dst_path + '.backup'
                            shutil.copy2(dst_path, backup_path)

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
                progress_dialog.destroy()

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
