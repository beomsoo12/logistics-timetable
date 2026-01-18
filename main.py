import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from timetable_manager import TimeTableManager
from tkcalendar import DateEntry
from datetime import date, datetime, timedelta
from version import VERSION, get_latest_changes
from updater import check_for_updates_on_startup, manual_update_check
from database import Database
import ctypes
import sys
import os
import uuid


class RoundedButton(tk.Canvas):
    """둥근 모서리 버튼 클래스"""

    def __init__(self, parent, text="", command=None, font=("굴림체", 9),
                 bg="#3498db", fg="white", width=None, height=None,
                 radius=10, padx=12, pady=6, cursor="hand2", **kwargs):

        # 폰트 크기에 따른 기본 크기 계산
        font_family = font[0] if isinstance(font, tuple) else "굴림체"
        font_size = font[1] if isinstance(font, tuple) and len(font) > 1 else 9
        font_weight = font[2] if isinstance(font, tuple) and len(font) > 2 else "normal"

        # 텍스트 길이에 따른 너비 계산 (한글은 더 넓게) - 30% 증가
        char_width = font_size * 1.6
        text_width = len(text) * char_width

        if width is None:
            btn_width = int((text_width + padx * 2) * 1.3)
        else:
            btn_width = int(width * 1.3) if width > 50 else int(width * font_size * 1.3)

        if height is None:
            btn_height = int((font_size * 2.2 + pady) * 1.3)
        else:
            btn_height = int(height * 1.3)

        # 최소 크기 보장 (30% 증가)
        btn_width = max(btn_width, 65)
        btn_height = max(btn_height, 30)

        super().__init__(parent, width=btn_width, height=btn_height,
                        highlightthickness=0, bg=parent.cget('bg') if hasattr(parent, 'cget') else "#f0f0f0",
                        cursor=cursor, **kwargs)

        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        self.text = text
        self.font = (font_family, font_size, font_weight)
        self.radius = radius
        self.btn_width = btn_width
        self.btn_height = btn_height
        self.hover_color = self._adjust_color(bg, -20)  # 약간 어두운 색
        self.is_pressed = False

        self._draw_button(self.bg_color)

        # 이벤트 바인딩
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _adjust_color(self, color, amount):
        """색상을 밝게 또는 어둡게 조정"""
        try:
            # 색상을 RGB로 변환
            if color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
            else:
                # 색상 이름을 RGB로 변환 시도
                return color

            # 조정
            r = max(0, min(255, r + amount))
            g = max(0, min(255, g + amount))
            b = max(0, min(255, b + amount))

            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color

    def _draw_button(self, color):
        """둥근 사각형 버튼 그리기"""
        self.delete("all")

        x1, y1 = 2, 2
        x2, y2 = self.btn_width - 2, self.btn_height - 2
        r = min(self.radius, (x2-x1)//2, (y2-y1)//2)

        # 둥근 사각형 그리기
        self.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, fill=color, outline=color)
        self.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, fill=color, outline=color)
        self.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=color, outline=color)
        self.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=color, outline=color)

        self.create_rectangle(x1+r, y1, x2-r, y2, fill=color, outline=color)
        self.create_rectangle(x1, y1+r, x2, y2-r, fill=color, outline=color)

        # 텍스트 그리기
        self.create_text(self.btn_width//2, self.btn_height//2,
                        text=self.text, fill=self.fg_color, font=self.font)

    def _on_enter(self, event):
        """마우스 호버"""
        self._draw_button(self.hover_color)

    def _on_leave(self, event):
        """마우스 떠남"""
        self._draw_button(self.bg_color)
        self.is_pressed = False

    def _on_press(self, event):
        """버튼 클릭"""
        self.is_pressed = True
        pressed_color = self._adjust_color(self.bg_color, -40)
        self._draw_button(pressed_color)

    def _on_release(self, event):
        """버튼 릴리즈"""
        if self.is_pressed:
            self._draw_button(self.hover_color)
            if self.command:
                self.command()
        self.is_pressed = False

    def config(self, **kwargs):
        """설정 변경"""
        if 'text' in kwargs:
            self.text = kwargs['text']
        if 'bg' in kwargs:
            self.bg_color = kwargs['bg']
            self.hover_color = self._adjust_color(kwargs['bg'], -20)
        if 'fg' in kwargs:
            self.fg_color = kwargs['fg']
        if 'command' in kwargs:
            self.command = kwargs['command']
        self._draw_button(self.bg_color)

    def configure(self, **kwargs):
        """config의 별칭"""
        self.config(**kwargs)

# 자동 로그인 허용 MAC 주소 목록
AUTO_LOGIN_MAC_ADDRESSES = [
    "20:16:01:25:00:0f",  # 개발자 PC
]

def get_mac_address():
    """현재 컴퓨터의 MAC 주소 반환"""
    try:
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) for i in range(0, 48, 8)][::-1])
        return mac.lower()
    except:
        return None


class LoginWindow:
    """로그인 창"""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.db = None
        self.login_window = None
        self.current_user = None

        self.setup_login_window()

    def setup_login_window(self):
        """로그인 창 설정"""
        self.root.withdraw()  # 메인 창 숨김

        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("로그인")
        self.login_window.geometry("420x520")
        self.login_window.resizable(False, False)
        self.login_window.configure(bg="#f8f9fa")

        # 화면 중앙에 배치
        screen_width = self.login_window.winfo_screenwidth()
        screen_height = self.login_window.winfo_screenheight()
        x = (screen_width - 420) // 2
        y = (screen_height - 520) // 2
        self.login_window.geometry(f"420x520+{x}+{y}")

        # 창을 맨 앞으로 가져오기
        self.login_window.lift()
        self.login_window.focus_force()
        self.login_window.attributes('-topmost', True)
        self.login_window.after(100, lambda: self.login_window.attributes('-topmost', False))

        # 아이콘 설정
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            try:
                self.login_window.iconbitmap(icon_path)
            except:
                pass

        # 로그인 창 닫으면 프로그램 종료
        self.login_window.protocol("WM_DELETE_WINDOW", self.on_close)

        # 데이터베이스 연결
        try:
            self.db = Database()
            if not self.db.connect():
                messagebox.showerror("연결 오류", "데이터베이스 연결에 실패했습니다.\ndb_config.py 파일을 확인해주세요.")
                self.root.destroy()
                return

            # 사용자 테이블 생성
            self.db.create_users_table()
        except Exception as e:
            messagebox.showerror("연결 오류", f"데이터베이스 연결 오류:\n{str(e)}")
            self.root.destroy()
            return

        # MAC 주소 기반 자동 로그인 확인
        current_mac = get_mac_address()
        if current_mac and current_mac.lower() in [mac.lower() for mac in AUTO_LOGIN_MAC_ADDRESSES]:
            # 자동 로그인 시도 (admin 계정)
            if self.try_auto_login():
                return  # 자동 로그인 성공 시 로그인 UI 생성하지 않음

        self.create_login_ui()

    def try_auto_login(self):
        """MAC 주소 기반 자동 로그인 시도"""
        try:
            # admin 계정으로 자동 로그인 (비밀번호 확인 없이)
            user = self.db.get_user_by_username("admin")
            if user:
                self.current_user = user
                # 로그인 창 숨기고 메인 창 표시 후 로그인 창 삭제
                self.login_window.withdraw()
                self.on_login_success(user)
                # after를 사용하여 안전하게 로그인 창 삭제
                self.root.after(100, self.safe_destroy_login_window)
                return True
        except Exception as e:
            print(f"자동 로그인 실패: {e}")
        return False

    def safe_destroy_login_window(self):
        """로그인 창 안전하게 삭제"""
        try:
            if self.login_window and self.login_window.winfo_exists():
                self.login_window.destroy()
        except:
            pass

    def set_ime_korean(self):
        """IME를 한글 모드로 설정"""
        if sys.platform == 'win32':
            try:
                # 한글 IME 활성화
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                ime_hwnd = ctypes.windll.imm32.ImmGetDefaultIMEWnd(hwnd)
                # 한글 모드로 전환 (0x15 = IME 한글)
                ctypes.windll.user32.SendMessageW(ime_hwnd, 0x283, 0x1, 0x1)
            except:
                pass

    def set_ime_english(self):
        """IME를 영문 모드로 설정"""
        if sys.platform == 'win32':
            try:
                # 영문 IME 설정
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                ime_hwnd = ctypes.windll.imm32.ImmGetDefaultIMEWnd(hwnd)
                # 영문 모드로 전환
                ctypes.windll.user32.SendMessageW(ime_hwnd, 0x283, 0x1, 0x0)
            except:
                pass

    def draw_logo(self, canvas, x_offset=0, y_offset=0, scale=1.0):
        """견우물류 로고 그리기 - 컬러풀한 점들"""
        # 로고 색상 (견우물류 로고의 컬러풀한 점들)
        colors = [
            ["#8BC34A", "#4CAF50", "#009688"],           # 초록 계열 (1행)
            ["#FFEB3B", "#8BC34A", "#4CAF50", "#00BCD4"],  # 노랑~파랑 (2행)
            ["#FF9800", "#FFEB3B", "#8BC34A", "#00BCD4", "#2196F3"],  # 주황~파랑 (3행)
            ["#FF5722", "#FF9800", "#FFEB3B", "#4CAF50", "#2196F3"],  # 빨강~파랑 (4행)
            ["#E91E63", "#FF5722", "#FF9800", "#8BC34A", "#03A9F4"],  # 분홍~하늘 (5행)
        ]

        dot_size = int(8 * scale)
        gap = int(10 * scale)
        start_x = x_offset + int(15 * scale)
        start_y = y_offset + int(10 * scale)

        for row_idx, row_colors in enumerate(colors):
            # 각 행의 시작 위치 (피라미드 형태)
            row_offset = (5 - len(row_colors)) * gap // 2
            for col_idx, color in enumerate(row_colors):
                x = start_x + row_offset + col_idx * gap
                y = start_y + row_idx * gap
                canvas.create_oval(
                    x, y, x + dot_size, y + dot_size,
                    fill=color, outline=""
                )

    def create_login_ui(self):
        """로그인 UI 생성 - 밝은 모던 스타일 + 견우물류 로고"""
        # 색상 정의
        bg_color = "#f8f9fa"        # 밝은 배경
        card_color = "#ffffff"       # 흰색 카드
        primary_color = "#4a90d9"    # 메인 파란색
        primary_hover = "#3a7bc8"    # 호버 파란색
        text_dark = "#2c3e50"        # 진한 텍스트
        text_light = "#7f8c8d"       # 연한 텍스트
        input_bg = "#f1f3f4"         # 입력창 배경
        input_border = "#e1e5e9"     # 입력창 테두리
        accent_color = "#27ae60"     # 액센트 초록색

        # 메인 프레임
        main_frame = tk.Frame(self.login_window, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 상단 헤더 영역 (밝은 색상)
        header_frame = tk.Frame(main_frame, bg="#e8f4f8", height=130)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # 로고 컨테이너 (헤더 안에)
        logo_frame = tk.Frame(header_frame, bg="#e8f4f8")
        logo_frame.pack(expand=True)

        # 로고 캔버스 (견우물류 로고 + 텍스트)
        logo_canvas = tk.Canvas(logo_frame, width=180, height=80, bg="white", highlightthickness=1, highlightbackground="#ddd")
        logo_canvas.pack(pady=25)

        # 견우물류 로고 그리기
        self.draw_logo(logo_canvas, x_offset=5, y_offset=10, scale=1.0)

        # "견우물류" 텍스트
        logo_canvas.create_text(120, 40, text="견우물류", font=("맑은 고딕", 14, "bold"), fill="#333333")

        # 콘텐츠 영역
        content_frame = tk.Frame(main_frame, bg=bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 20))

        # 타이틀
        title_label = tk.Label(
            content_frame,
            text="업무 타임테이블",
            font=("맑은 고딕", 18, "bold"),
            bg=bg_color,
            fg=text_dark
        )
        title_label.pack(pady=(0, 5))

        version_label = tk.Label(
            content_frame,
            text=f"Version {VERSION}",
            font=("맑은 고딕", 9),
            bg=bg_color,
            fg=text_light
        )
        version_label.pack(pady=(0, 20))

        # 로그인 카드
        card_frame = tk.Frame(content_frame, bg=card_color, padx=35, pady=25)
        card_frame.pack(padx=35, fill=tk.X)

        # 카드 그림자 효과 (시뮬레이션)
        shadow_frame = tk.Frame(content_frame, bg="#e0e0e0", height=2)
        shadow_frame.pack(fill=tk.X, padx=37)

        # 사용자 ID 입력 (한글 모드)
        id_frame = tk.Frame(card_frame, bg=card_color)
        id_frame.pack(fill=tk.X, pady=(0, 12))

        id_label = tk.Label(
            id_frame,
            text="사용자 ID (한글)",
            font=("맑은 고딕", 10, "bold"),
            bg=card_color,
            fg=text_dark,
            anchor="w"
        )
        id_label.pack(fill=tk.X)

        id_entry_frame = tk.Frame(id_frame, bg=input_border, padx=1, pady=1)
        id_entry_frame.pack(fill=tk.X, pady=(5, 0))

        self.username_entry = tk.Entry(
            id_entry_frame,
            font=("맑은 고딕", 11),
            bg=input_bg,
            fg=text_dark,
            insertbackground=text_dark,
            relief=tk.FLAT,
            highlightthickness=0
        )
        self.username_entry.pack(fill=tk.X, ipady=10, padx=10)
        self.username_entry.focus()

        # 로그인 창 열릴 때 한글 모드로 시작
        self.login_window.after(100, self.set_ime_korean)

        # 입력창 포커스 효과 + IME 전환
        def on_id_focus_in(e):
            id_entry_frame.configure(bg=primary_color)
            self.login_window.after(50, self.set_ime_korean)  # 한글 모드

        def on_id_focus_out(e):
            id_entry_frame.configure(bg=input_border)

        self.username_entry.bind("<FocusIn>", on_id_focus_in)
        self.username_entry.bind("<FocusOut>", on_id_focus_out)

        # 비밀번호 입력 (영문 모드)
        pw_frame = tk.Frame(card_frame, bg=card_color)
        pw_frame.pack(fill=tk.X, pady=(0, 20))

        pw_label = tk.Label(
            pw_frame,
            text="비밀번호 (영문)",
            font=("맑은 고딕", 10, "bold"),
            bg=card_color,
            fg=text_dark,
            anchor="w"
        )
        pw_label.pack(fill=tk.X)

        pw_entry_frame = tk.Frame(pw_frame, bg=input_border, padx=1, pady=1)
        pw_entry_frame.pack(fill=tk.X, pady=(5, 0))

        self.password_entry = tk.Entry(
            pw_entry_frame,
            font=("맑은 고딕", 11),
            bg=input_bg,
            fg=text_dark,
            insertbackground=text_dark,
            relief=tk.FLAT,
            show="●",
            highlightthickness=0
        )
        self.password_entry.pack(fill=tk.X, ipady=10, padx=10)

        # 비밀번호 포커스 효과 + IME 전환
        def on_pw_focus_in(e):
            pw_entry_frame.configure(bg=primary_color)
            self.login_window.after(50, self.set_ime_english)  # 영문 모드

        def on_pw_focus_out(e):
            pw_entry_frame.configure(bg=input_border)

        self.password_entry.bind("<FocusIn>", on_pw_focus_in)
        self.password_entry.bind("<FocusOut>", on_pw_focus_out)

        # 엔터키로 로그인
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self.do_login())

        # 로그인 버튼 (둥근 모서리)
        login_btn = RoundedButton(
            card_frame,
            text="로그인",
            font=("맑은 고딕", 11, "bold"),
            bg=primary_color,
            fg="white",
            width=280,
            height=35,
            radius=6,
            command=self.do_login
        )
        login_btn.pack(pady=(10, 0))

        # 안내 메시지
        info_frame = tk.Frame(main_frame, bg=bg_color)
        info_frame.pack(pady=(15, 0))

        info_icon = tk.Label(
            info_frame,
            text="ℹ",
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=accent_color
        )
        info_icon.pack(side=tk.LEFT, padx=(0, 5))

        info_label = tk.Label(
            info_frame,
            text="처음 사용시  ID: admin  /  PW: admin123",
            font=("맑은 고딕", 9),
            bg=bg_color,
            fg=text_light
        )
        info_label.pack(side=tk.LEFT)

        # 하단 저작권
        copyright_label = tk.Label(
            main_frame,
            text="© 2025 견우물류. All rights reserved.",
            font=("맑은 고딕", 8),
            bg=bg_color,
            fg="#bdc3c7"
        )
        copyright_label.pack(side=tk.BOTTOM, pady=15)

    def do_login(self):
        """로그인 처리"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            messagebox.showwarning("입력 오류", "사용자 ID를 입력해주세요.")
            self.username_entry.focus()
            return

        if not password:
            messagebox.showwarning("입력 오류", "비밀번호를 입력해주세요.")
            self.password_entry.focus()
            return

        # 인증 시도
        user = self.db.authenticate_user(username, password)

        if user:
            self.current_user = user
            self.login_window.destroy()
            self.db.disconnect()
            self.on_login_success(user)
        else:
            messagebox.showerror("로그인 실패", "사용자 ID 또는 비밀번호가 올바르지 않습니다.")
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()

    def on_close(self):
        """로그인 창 닫기"""
        if self.db:
            self.db.disconnect()
        self.root.destroy()


class TimeTableGUI:
    """견우물류 타임테이블 GUI 애플리케이션"""

    # 업체별 색상 정의
    COMPANY_COLORS = {
        "롯데마트": "#FFE5E5",     # 연한 빨강
        "롯데슈퍼": "#FFD4D4",     # 더 진한 연한 빨강
        "지에스": "#E5F5FF",       # 연한 파랑
        "이마트": "#FFF5E5",       # 연한 주황
        "홈플러스": "#F0E5FF",     # 연한 보라
        "코스트코": "#E5FFE5"      # 연한 초록
    }

    COMPANIES = ["롯데마트", "롯데슈퍼", "지에스", "이마트", "홈플러스", "코스트코"]

    def __init__(self, root, current_user=None):
        self.root = root
        self.current_user = current_user
        user_display = current_user['display_name'] if current_user else ''
        self.root.title(f"견우물류 업무 타임테이블 - {user_display}")

        # 화면 크기 가져오기
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 창 크기 설정 (전체 화면에 가깝게)
        window_width = screen_width  # 전체 너비
        window_height = screen_height - 40  # 작업 표시줄 영역만 제외

        # 창 위치 (맨 위, 맨 왼쪽)
        x_position = 0
        y_position = 0

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

        # 창이 최대화되지 않은 상태에서 전체화면처럼 보이도록
        self.root.update_idletasks()

        # 마우스 드래그 선택을 위한 변수
        self.drag_start_time = None
        self.drag_end_time = None
        self.is_dragging = False
        self.drag_start_company = None  # 드래그 시작한 업체
        self.header_cells = {}  # 시간 헤더 셀 저장
        self.grid_cells = {}  # 그리드 셀 저장 (row, col) -> widget

        # 셀 드래그를 위한 변수
        self.is_cell_dragging = False
        self.dragged_cells = set()  # 드래그 중 이미 처리된 셀들
        self.drag_company = None  # 드래그 중인 업체
        self.drag_corp_name = None  # 드래그 중인 법인명

        # 업체+법인명별 색상 저장 (DB에서 로드)
        self.company_corp_colors = {}  # key: (업체명, 법인명), value: 색상코드

        try:
            self.manager = TimeTableManager()
        except Exception as e:
            messagebox.showerror("데이터베이스 연결 오류",
                               f"데이터베이스 연결에 실패했습니다.\n{str(e)}\n\n"
                               "db_config.py 파일의 데이터베이스 설정을 확인해주세요.")
            self.root.destroy()
            return

        self.setup_ui()

        self.refresh_timetable()

        # 프로그램 종료 시 DB 연결 해제
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """UI 구성"""
        # 상단 타이틀
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)

        # 타이틀과 사용자 정보를 담을 프레임
        title_inner = tk.Frame(title_frame, bg="#2c3e50")
        title_inner.pack(fill=tk.X, pady=10)

        title_label = tk.Label(
            title_inner,
            text=f"견우물류 업무 타임테이블 v{VERSION}",
            font=("굴림체", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20)

        # 사용자 정보 및 로그아웃 버튼 (우측)
        user_frame = tk.Frame(title_inner, bg="#2c3e50")
        user_frame.pack(side=tk.RIGHT, padx=20)

        if self.current_user:
            user_label = tk.Label(
                user_frame,
                text=f"{self.current_user['display_name']} 님",
                font=("굴림체", 10),
                bg="#2c3e50",
                fg="#ecf0f1"
            )
            user_label.pack(side=tk.LEFT, padx=(0, 10))

            logout_btn = RoundedButton(
                user_frame,
                text="로그아웃",
                font=("굴림체", 11),
                bg="#e74c3c",
                fg="white",
                radius=6,
                command=self.logout
            )
            logout_btn.pack(side=tk.LEFT)

            # 종료 버튼
            exit_btn = RoundedButton(
                user_frame,
                text="종료",
                font=("굴림체", 11),
                bg="#7f8c8d",
                fg="white",
                radius=6,
                command=self.exit_program
            )
            exit_btn.pack(side=tk.LEFT, padx=(10, 0))

        # 메뉴바 추가
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 관리 메뉴 (관리자만)
        if self.current_user and self.current_user.get('is_admin'):
            admin_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="관리", menu=admin_menu)
            admin_menu.add_command(label="사용자 관리", command=self.show_user_management)
            admin_menu.add_command(label="변경 로그 조회", command=self.show_change_logs)
            admin_menu.add_separator()
            admin_menu.add_command(label="비밀번호 변경", command=self.show_change_password)
        else:
            # 일반 사용자 메뉴
            user_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="설정", menu=user_menu)
            user_menu.add_command(label="비밀번호 변경", command=self.show_change_password)

        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도움말", menu=help_menu)
        help_menu.add_command(label="업데이트 확인", command=self.check_for_updates)
        help_menu.add_separator()
        help_menu.add_command(label="버전 정보", command=self.show_about)

        # 날짜 선택 영역
        date_frame = tk.Frame(self.root, bg="#34495e", height=50)
        date_frame.pack(fill=tk.X, side=tk.TOP)

        # 날짜 선택 위젯
        tk.Label(
            date_frame,
            text="작업 날짜:",
            font=("굴림체", 22, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(side=tk.LEFT, padx=(20, 10), pady=10)

        self.date_entry = DateEntry(
            date_frame,
            font=("굴림체", 20),
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            locale='ko_KR'
        )
        self.date_entry.pack(side=tk.LEFT, padx=5, pady=10)
        self.date_entry.bind("<<DateEntrySelected>>", self.on_date_changed)

        # 날짜 이동 버튼 (둥근 모서리)
        btn_prev = RoundedButton(
            date_frame,
            text="◀ 이전",
            font=("굴림체", 11),
            bg="#3498db",
            fg="white",
            radius=6,
            command=self.prev_date
        )
        btn_prev.pack(side=tk.LEFT, padx=5, pady=10)

        btn_today = RoundedButton(
            date_frame,
            text="오늘",
            font=("굴림체", 11),
            bg="#27ae60",
            fg="white",
            radius=6,
            command=self.goto_today
        )
        btn_today.pack(side=tk.LEFT, padx=5, pady=10)

        btn_next = RoundedButton(
            date_frame,
            text="다음 ▶",
            font=("굴림체", 11),
            bg="#3498db",
            fg="white",
            radius=6,
            command=self.next_date
        )
        btn_next.pack(side=tk.LEFT, padx=5, pady=10)

        # 기본 업무 관리 버튼 (둥근 모서리)
        btn_manage_default = RoundedButton(
            date_frame,
            text="기본 업무 관리",
            font=("굴림체", 11),
            bg="#16a085",
            fg="white",
            radius=6,
            command=self.manage_default_tasks
        )
        btn_manage_default.pack(side=tk.LEFT, padx=5, pady=10)

        # 기간별 통계 버튼 (둥근 모서리)
        btn_period_summary = RoundedButton(
            date_frame,
            text="기간별 통계",
            font=("굴림체", 11),
            bg="#2980b9",
            fg="white",
            radius=6,
            command=self.show_period_summary
        )
        btn_period_summary.pack(side=tk.LEFT, padx=5, pady=10)

        # 메인 컨테이너 (세로 방향)
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 타임테이블 표시 영역 (전체 화면 사용)
        top_frame = tk.Frame(main_container)
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 타임테이블 그리드
        self.setup_canvas_grid(top_frame)

    def setup_canvas_grid(self, parent):
        """Canvas 기반 타임테이블 그리드 설정"""
        # Canvas와 Scrollbar 생성하여 가로 스크롤 지원
        canvas = tk.Canvas(parent, bg="white")
        h_scrollbar = tk.Scrollbar(parent, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(xscrollcommand=h_scrollbar.set)

        # Scrollbar 배치
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Frame을 Canvas 안에 배치
        self.canvas_frame = tk.Frame(canvas, bg="white")
        canvas_window = canvas.create_window((0, 0), window=self.canvas_frame, anchor="nw")

        # Canvas 스크롤 영역 업데이트
        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.canvas_frame.bind("<Configure>", update_scroll_region)

        # 마우스 휠 스크롤 지원
        def on_mousewheel(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<Shift-MouseWheel>", on_mousewheel)

        # 클릭 이벤트를 위한 딕셔너리 (시간 -> 위젯)
        self.time_slot_widgets = {}

    def on_date_changed(self, event=None):
        """날짜 변경 시 호출"""
        selected_date = self.date_entry.get_date()
        self.manager.set_current_date(selected_date)

        self.refresh_timetable()

    def prev_date(self):
        """이전 날짜로 이동"""
        current = self.date_entry.get_date()
        from datetime import timedelta
        prev = current - timedelta(days=1)
        self.date_entry.set_date(prev)
        self.on_date_changed()

    def next_date(self):
        """다음 날짜로 이동"""
        current = self.date_entry.get_date()
        from datetime import timedelta
        next_day = current + timedelta(days=1)
        self.date_entry.set_date(next_day)
        self.on_date_changed()

    def goto_today(self):
        """오늘 날짜로 이동"""
        self.date_entry.set_date(date.today())
        self.on_date_changed()

    def create_lunch_cell(self, parent, row, column, width=50, height=30, base_color="white"):
        """점심시간 셀 생성 (빗금 패턴)"""
        # Canvas로 빗금 패턴 그리기
        cell_canvas = tk.Canvas(
            parent,
            width=width,
            height=height,
            bg=base_color,
            highlightthickness=1,
            highlightbackground="#999999"
        )
        cell_canvas.grid(row=row, column=column, sticky="nsew")

        # 빗금 그리기 (대각선 패턴)
        stripe_color = "#cccccc"  # 빗금 색상 (회색)
        stripe_spacing = 8  # 빗금 간격

        # 왼쪽 위에서 오른쪽 아래로 대각선
        for i in range(-height, width + height, stripe_spacing):
            cell_canvas.create_line(
                i, 0, i + height, height,
                fill=stripe_color, width=1
            )

        return cell_canvas

    def refresh_timetable(self):
        """타임테이블 새로고침 (시간 가로, 업무 세로 배치)"""
        # 기존 위젯 삭제
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        self.time_slot_widgets = {}
        self.header_cells = {}
        self.grid_cells = {}  # 그리드 셀 초기화

        # 화면 크기 가져오기
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        frame_width = self.canvas_frame.winfo_width()
        frame_height = self.canvas_frame.winfo_height()

        if frame_width < 100:
            frame_width = int(screen_width * 0.95)  # 화면 너비의 95% 사용
        if frame_height < 100:
            frame_height = screen_height - 250  # 헤더/버튼 영역 제외

        # 시간 슬롯별 컬럼 너비 계산 (화면 크기에 맞게)
        time_slots = self.manager.time_slots
        col_label_width = int(screen_width * 0.08)  # 화면 너비의 8%
        corp_name_width = int(screen_width * 0.065)  # 법인명 열 너비 (화면 너비의 6.5%)
        extra_time_width = int(screen_width * 0.10)  # 추가시간 열 너비 (화면 너비의 10%)
        remaining_width = frame_width - col_label_width - corp_name_width - extra_time_width - 20
        time_col_width = max(40, int(remaining_width / len(time_slots)))  # 각 시간 컬럼 너비

        # 기본 업무 템플릿 로드
        default_tasks = self.manager.get_default_tasks()

        # 기본 업무를 (업체명, 법인명) 조합으로 그룹화하고 최소 display_order 추출
        tasks_by_company_corp = {}  # key: (업체명, 법인명), value: {time_slot: task_info}
        company_corp_display_order = {}  # key: (업체명, 법인명), value: 최소 display_order
        self.company_corp_colors = {}  # key: (업체명, 법인명), value: 색상코드

        for display_order, task_info in default_tasks.items():
            company = task_info.get("company", "")
            corp_name = task_info.get("task", "")  # task_name이 법인명
            time_slot = task_info.get("time_slot", "")
            color = task_info.get("color", "")  # DB에서 색상 가져오기

            if company and time_slot:
                key = (company, corp_name)
                if key not in tasks_by_company_corp:
                    tasks_by_company_corp[key] = {}
                    company_corp_display_order[key] = display_order
                    # 첫 번째 색상 설정 (없으면 COMPANY_COLORS 기본값 사용)
                    if color:
                        self.company_corp_colors[key] = color
                    else:
                        self.company_corp_colors[key] = self.COMPANY_COLORS.get(company, "#d5f4e6")
                else:
                    # 해당 조합의 최소 display_order 유지
                    if display_order < company_corp_display_order[key]:
                        company_corp_display_order[key] = display_order
                    # 색상이 있으면 업데이트 (더 작은 display_order의 색상 우선)
                    if color and display_order <= company_corp_display_order[key]:
                        self.company_corp_colors[key] = color
                tasks_by_company_corp[key][time_slot] = task_info

        # display_order 순서대로 (업체명, 법인명) 정렬
        all_company_corps = sorted(tasks_by_company_corp.keys(), key=lambda c: company_corp_display_order.get(c, 999))

        # 헤더 행 (시간대)
        tk.Label(
            self.canvas_frame,
            text="업체/시간",
            font=("굴림체", 11, "bold"),
            bg="#2c3e50",
            fg="white",
            relief=tk.RIDGE,
            borderwidth=1
        ).grid(row=0, column=0, sticky="nsew")

        # 법인명 헤더
        tk.Label(
            self.canvas_frame,
            text="법인명",
            font=("굴림체", 11, "bold"),
            bg="#2c3e50",
            fg="white",
            relief=tk.RIDGE,
            borderwidth=1
        ).grid(row=0, column=1, sticky="nsew")

        for col_idx, time_slot in enumerate(time_slots):
            # 점심시간(12:30~13:00) 헤더는 다른 색상으로 표시
            is_lunch_time = time_slot in ["12:30", "13:00"]
            header_bg = "#8B4513" if is_lunch_time else "#2c3e50"  # 점심시간은 갈색 배경
            header_text = f"🍴{time_slot}" if is_lunch_time else time_slot  # 점심시간 아이콘 추가

            header_label = tk.Label(
                self.canvas_frame,
                text=header_text,
                font=("굴림체", 10, "bold"),
                bg=header_bg,
                fg="white",
                relief=tk.RIDGE,
                borderwidth=1,
                cursor="hand2"
            )
            header_label.grid(row=0, column=col_idx + 2, sticky="nsew")  # +2로 변경 (법인명 열 추가)

            # 마우스 드래그 이벤트 바인딩
            header_label.bind("<Button-1>", lambda e, t=time_slot: self.on_drag_start(t))
            header_label.bind("<B1-Motion>", lambda e, t=time_slot: self.on_drag_motion(t))
            header_label.bind("<ButtonRelease-1>", lambda e: self.on_drag_end())
            header_label.bind("<Enter>", lambda e, t=time_slot: self.on_drag_enter(t))

            # 헤더 셀 저장
            self.header_cells[time_slot] = header_label

            self.canvas_frame.grid_columnconfigure(col_idx + 2, minsize=time_col_width, weight=1)  # +2로 변경

        # 추가 시간 컬럼 헤더
        tk.Label(
            self.canvas_frame,
            text="추가 시간",
            font=("굴림체", 10, "bold"),
            bg="#2c3e50",
            fg="white",
            relief=tk.RIDGE,
            borderwidth=1
        ).grid(row=0, column=len(time_slots) + 2, sticky="nsew")  # +2로 변경

        self.canvas_frame.grid_columnconfigure(0, minsize=col_label_width)
        self.canvas_frame.grid_columnconfigure(1, minsize=corp_name_width)  # 법인명 열 너비 (반응형)
        self.canvas_frame.grid_columnconfigure(len(time_slots) + 2, minsize=extra_time_width)  # 추가시간 열 너비 (반응형)

        # 행 높이 설정 (화면 높이에 비례)
        # 업체 수를 고려해서 행 높이 계산 (6개 업체 × 3줄 = 18줄 + 헤더 + 총합)
        available_height = frame_height - 100  # 헤더/여백 제외
        row_height = max(20, int(available_height / 30))  # 최소 20px, 30줄로 나눔 (행 높이 축소)

        # (업체명, 법인명) 조합별로 행 생성 (기본업무 행 + 특수상황 행, 한 줄 띄우기)
        row_num = 1
        for company_corp in all_company_corps:
            company, corp_name = company_corp
            company_tasks = tasks_by_company_corp.get(company_corp, {})
            # DB에 저장된 색상 사용 (없으면 COMPANY_COLORS 기본값)
            bg_color = self.company_corp_colors.get(company_corp, self.COMPANY_COLORS.get(company, "#d5f4e6"))

            # 기본업무 행
            tk.Label(
                self.canvas_frame,
                text=company,
                font=("굴림체", 11, "bold"),
                bg=bg_color,
                relief=tk.RIDGE,
                borderwidth=1
            ).grid(row=row_num, column=0, sticky="nsew")
            self.canvas_frame.grid_rowconfigure(row_num, minsize=row_height)

            # 법인명 셀 (기본업무 행)
            tk.Label(
                self.canvas_frame,
                text=corp_name,
                font=("굴림체", 10),
                bg=bg_color,
                relief=tk.RIDGE,
                borderwidth=1
            ).grid(row=row_num, column=1, sticky="nsew")

            # 각 시간대별 셀 - 시작시간부터 종료시간까지 색상 칠하기
            for col_idx, time_slot in enumerate(time_slots):
                # 해당 시간이 어떤 업무의 범위에 포함되는지 확인
                cell_bg_color = "white"
                cell_task_slot = None

                for task_time_slot, task_info in company_tasks.items():
                    start_time = task_time_slot
                    end_time = task_info.get("end_time", task_time_slot)

                    # 시작과 종료 인덱스 확인
                    try:
                        start_idx = time_slots.index(start_time)
                        end_idx = time_slots.index(end_time)
                        current_idx = time_slots.index(time_slot)

                        # 현재 시간이 범위 내에 있으면 색상 적용
                        if start_idx <= current_idx <= end_idx:
                            cell_bg_color = bg_color
                            cell_task_slot = task_time_slot
                            break
                    except ValueError:
                        continue

                # 점심시간(12:30~13:00) 여부 확인
                is_lunch_time = time_slot in ["12:30", "13:00"]

                # 셀 생성 (기본 업무 행은 클릭 불가)
                if is_lunch_time:
                    # 점심시간 셀 - 빗금 패턴 적용
                    task_cell = self.create_lunch_cell(
                        self.canvas_frame,
                        row_num,
                        col_idx + 2,
                        width=time_col_width,
                        height=row_height,
                        base_color=cell_bg_color
                    )
                else:
                    task_cell = tk.Label(
                        self.canvas_frame,
                        text="",
                        font=("굴림체", 10),
                        bg=cell_bg_color,
                        relief=tk.RIDGE,
                        borderwidth=1
                    )
                    task_cell.grid(row=row_num, column=col_idx + 2, sticky="nsew")  # +2로 변경

                # 그리드 셀 저장 (기본 업무 행은 이벤트 바인딩 없음)
                # (widget, company, corp_name, time_slot, is_special)
                self.grid_cells[(row_num, col_idx + 2)] = (task_cell, company, corp_name, time_slot, False)  # +2로 변경

            # 기본업무 행의 추가 시간 셀 (빈 셀)
            tk.Label(
                self.canvas_frame,
                text="",
                font=("굴림체", 10),
                bg="white",
                relief=tk.RIDGE,
                borderwidth=1
            ).grid(row=row_num, column=len(time_slots) + 2, sticky="nsew")  # +2로 변경

            row_num += 1

            # 특수상황 행
            tk.Label(
                self.canvas_frame,
                text=f"{company} 특수",
                font=("굴림체", 10),
                bg="#f0f0f0",
                relief=tk.RIDGE,
                borderwidth=1
            ).grid(row=row_num, column=0, sticky="nsew")
            self.canvas_frame.grid_rowconfigure(row_num, minsize=row_height)

            # 법인명 셀 (특수상황 행) - 동일한 법인명 표시
            tk.Label(
                self.canvas_frame,
                text=corp_name,
                font=("굴림체", 10),
                bg="#f0f0f0",
                relief=tk.RIDGE,
                borderwidth=1
            ).grid(row=row_num, column=1, sticky="nsew")

            # DB에서 특수 시간 정보 로드 (업체명, 법인명 조합)
            special_times = self.manager.get_special_times(company, corp_name)

            # 각 시간대별 특수상황 셀
            for col_idx, time_slot in enumerate(time_slots):
                cell_bg_color = "white"

                # 1. DB에 특수 시간 데이터가 있으면 그것을 사용
                if special_times:
                    if time_slot in special_times and special_times[time_slot]:
                        cell_bg_color = bg_color
                else:
                    # 2. DB에 특수 시간 데이터가 없으면, 기본 업무 시간과 동일하게 초기화
                    for task_time_slot, task_info in company_tasks.items():
                        start_time = task_time_slot
                        end_time = task_info.get("end_time", task_time_slot)

                        # 시작과 종료 인덱스 확인
                        try:
                            start_idx = time_slots.index(start_time)
                            end_idx = time_slots.index(end_time)
                            current_idx = time_slots.index(time_slot)

                            # 현재 시간이 범위 내에 있으면 색상 적용 및 DB 저장
                            if start_idx <= current_idx <= end_idx:
                                cell_bg_color = bg_color
                                # DB에 특수 시간 저장 (기본 업무 시간으로 초기화) - 업체명, 법인명 포함
                                self.manager.save_special_time(company, corp_name, time_slot, True, self.current_user)
                                break
                        except ValueError:
                            continue

                # 점심시간(12:30~13:00) 여부 확인
                is_lunch_time = time_slot in ["12:30", "13:00"]

                # 특수상황 셀 생성
                if is_lunch_time:
                    # 점심시간 셀 - 빗금 패턴 적용
                    special_cell = self.create_lunch_cell(
                        self.canvas_frame,
                        row_num,
                        col_idx + 2,
                        width=time_col_width,
                        height=row_height,
                        base_color=cell_bg_color
                    )
                    special_cell.config(cursor="hand2")
                else:
                    special_cell = tk.Label(
                        self.canvas_frame,
                        text="",
                        font=("굴림체", 10),
                        bg=cell_bg_color,
                        relief=tk.RIDGE,
                        borderwidth=1,
                        cursor="hand2"
                    )
                    special_cell.grid(row=row_num, column=col_idx + 2, sticky="nsew")  # +2로 변경

                # 클릭 및 드래그 이벤트 바인딩 - 법인명도 전달
                special_cell.bind("<Button-1>", lambda e, t=time_slot, c=company, cn=corp_name, r=row_num: self.on_cell_drag_start(e, t, c, cn, r))
                special_cell.bind("<B1-Motion>", lambda e, t=time_slot, c=company, cn=corp_name, r=row_num: self.on_cell_drag_motion(e, t, c, cn, r))
                special_cell.bind("<ButtonRelease-1>", lambda e: self.on_cell_drag_end(e))

                # 그리드 셀 저장 (특수 행 플래그 추가) - 법인명도 저장
                # (widget, company, corp_name, time_slot, is_special)
                self.grid_cells[(row_num, col_idx + 2)] = (special_cell, company, corp_name, time_slot, True)  # +2로 변경

            # 특수상황 행의 추가 시간 셀 - 시간 차이 계산
            extra_time_text = self.calculate_extra_time(company, corp_name, company_tasks)
            tk.Label(
                self.canvas_frame,
                text=extra_time_text,
                font=("굴림체", 10, "bold"),
                bg="#FFF9C4",
                fg="#E65100",
                relief=tk.RIDGE,
                borderwidth=1
            ).grid(row=row_num, column=len(time_slots) + 2, sticky="nsew")  # +2로 변경

            row_num += 1

            # 한 줄 띄우기
            separator_height = max(5, int(row_height * 0.3))  # 행 높이의 30%
            separator_label = tk.Label(
                self.canvas_frame,
                text="",
                font=("굴림체", 10),
                bg="#e0e0e0"
            )
            separator_label.grid(row=row_num, column=0, columnspan=len(time_slots) + 3, sticky="ew")  # +3으로 변경 (법인명 열 추가)
            self.canvas_frame.grid_rowconfigure(row_num, minsize=separator_height)
            row_num += 1

        # 법인별 추가 시간 합계 계산
        corp_name_totals = {}  # key: 법인명, value: 추가 시간(분)
        total_extra_minutes = 0

        for company_corp in all_company_corps:
            company, corp_name = company_corp
            company_tasks = tasks_by_company_corp.get(company_corp, {})
            extra_time_text = self.calculate_extra_time(company, corp_name, company_tasks)

            # 시간 문자열 파싱 (+2h 30m, -1h, +45m 등)
            extra_minutes = 0
            if extra_time_text:
                sign = 1 if extra_time_text.startswith("+") else -1
                parts = extra_time_text[1:].split()  # + 또는 - 제거

                for part in parts:
                    if 'h' in part:
                        hours = int(part.replace('h', ''))
                        extra_minutes += sign * hours * 60
                    elif 'm' in part:
                        minutes = int(part.replace('m', ''))
                        extra_minutes += sign * minutes

            # 법인별 합계 누적
            if corp_name:
                if corp_name not in corp_name_totals:
                    corp_name_totals[corp_name] = 0
                corp_name_totals[corp_name] += extra_minutes

            total_extra_minutes += extra_minutes

        # 법인별 합계 표시
        if corp_name_totals:
            # 제목 행
            tk.Label(
                self.canvas_frame,
                text="법인별 추가 시간 합계",
                font=("굴림체", 14, "bold"),
                bg="#E3F2FD",
                fg="#1976D2",
                relief=tk.RIDGE,
                borderwidth=2,
                pady=5
            ).grid(row=row_num, column=0, columnspan=len(time_slots) + 3, sticky="ew", pady=(10, 0))
            row_num += 1

            # 각 법인별 합계 표시
            for corp_name, minutes in sorted(corp_name_totals.items()):
                if minutes != 0:
                    abs_minutes = abs(minutes)
                    hours = abs_minutes // 60
                    mins = abs_minutes % 60
                    sign_text = "+" if minutes > 0 else "-"

                    if hours > 0 and mins > 0:
                        time_text = f"{sign_text}{hours}h {mins}m"
                    elif hours > 0:
                        time_text = f"{sign_text}{hours}h"
                    elif mins > 0:
                        time_text = f"{sign_text}{mins}m"
                    else:
                        time_text = "0"
                else:
                    time_text = "0"

                tk.Label(
                    self.canvas_frame,
                    text=f"{corp_name}: {time_text}",
                    font=("굴림체", 12),
                    bg="#E8F5E9",
                    fg="#2E7D32",
                    relief=tk.RIDGE,
                    borderwidth=1,
                    pady=3
                ).grid(row=row_num, column=0, columnspan=len(time_slots) + 3, sticky="ew")
                row_num += 1

        # 총합을 시간 형식으로 변환
        if total_extra_minutes != 0:
            abs_minutes = abs(total_extra_minutes)
            total_hours = abs_minutes // 60
            total_mins = abs_minutes % 60
            sign_text = "+" if total_extra_minutes > 0 else "-"

            if total_hours > 0 and total_mins > 0:
                total_text = f"총 추가 시간: {sign_text}{total_hours}h {total_mins}m"
            elif total_hours > 0:
                total_text = f"총 추가 시간: {sign_text}{total_hours}h"
            elif total_mins > 0:
                total_text = f"총 추가 시간: {sign_text}{total_mins}m"
            else:
                total_text = "총 추가 시간: 0"
        else:
            total_text = "총 추가 시간: 0"

        # 총합 레이블 표시
        total_label = tk.Label(
            self.canvas_frame,
            text=total_text,
            font=("굴림체", 24, "bold"),
            bg="#FFF9C4",
            fg="#E65100",
            relief=tk.RIDGE,
            borderwidth=2,
            padx=20,
            pady=8
        )
        total_label.grid(row=row_num, column=0, columnspan=len(time_slots) + 3, sticky="ew", pady=10)  # +3으로 변경

    def calculate_extra_time(self, company, corp_name, company_tasks):
        """기본 시간과 특수 시간의 차이 계산 (업체명+법인명 기준)"""
        # 1. 기본 업무 시간 계산 (DB에서 가져온 데이터)
        basic_minutes = 0
        for time_slot, task_info in company_tasks.items():
            start_time = time_slot
            end_time = task_info.get("end_time", time_slot)

            try:
                start_parts = start_time.split(":")
                start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])

                end_parts = end_time.split(":")
                end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])

                # 시간 차이 (분)
                duration = end_minutes - start_minutes + 30  # 30분 단위이므로 +30
                basic_minutes += duration
            except (ValueError, IndexError):
                continue

        # 2. 특수 시간 계산 (특수 행의 색칠된 셀)
        special_minutes = 0
        # DB에 저장된 업체 색상 사용 (없으면 기본값)
        company_corp_key = (company, corp_name)
        company_color = self.company_corp_colors.get(company_corp_key, self.COMPANY_COLORS.get(company, "#d5f4e6"))

        # 특수 행의 셀들만 확인 (업체명+법인명 모두 일치해야 함)
        for (row, col), value in self.grid_cells.items():
            cell_widget = value[0]
            cell_company = value[1]
            cell_corp_name = value[2]
            is_special = value[4] if len(value) >= 5 else False

            if cell_company == company and cell_corp_name == corp_name and is_special:  # 특수 행
                try:
                    bg_color = cell_widget.cget("bg")
                    # 색상이 업체 색상이면 30분 추가
                    if bg_color.lower() == company_color.lower():
                        special_minutes += 30
                except:
                    pass

        # 3. 차이 계산
        diff_minutes = special_minutes - basic_minutes

        if diff_minutes == 0:
            return ""

        # 절대값으로 시간 계산
        abs_minutes = abs(diff_minutes)
        hours = abs_minutes // 60
        minutes = abs_minutes % 60

        # 부호 표시
        sign = "+" if diff_minutes > 0 else "-"

        if hours > 0 and minutes > 0:
            return f"{sign}{hours}h {minutes}m"
        elif hours > 0:
            return f"{sign}{hours}h"
        elif minutes > 0:
            return f"{sign}{minutes}m"
        else:
            return ""

    def on_drag_start(self, time_slot):
        """드래그 시작 - 시작 시간 설정"""
        self.is_dragging = True
        self.drag_start_time = time_slot
        self.drag_end_time = time_slot
        # 현재 행 찾기 (드래그 시작한 행)
        self.drag_start_company = None
        self.highlight_time_range()

    def on_drag_motion(self, time_slot):
        """드래그 중 - 현재 시간 업데이트"""
        if self.is_dragging:
            self.drag_end_time = time_slot
            self.highlight_time_range()

    def on_drag_enter(self, time_slot):
        """마우스가 다른 시간 셀로 진입할 때"""
        if self.is_dragging:
            self.drag_end_time = time_slot
            self.highlight_time_range()

    def on_drag_end(self):
        """드래그 종료"""
        # 드래그 상태 초기화
        self.is_dragging = False
        self.drag_start_time = None
        self.drag_end_time = None
        self.reset_time_range_highlight()

    def highlight_time_range(self):
        """선택된 시간 범위 하이라이트 (헤더 + 그리드 셀)"""
        if not self.drag_start_time or not self.drag_end_time:
            return

        time_slots = self.manager.time_slots

        try:
            start_idx = time_slots.index(self.drag_start_time)
            end_idx = time_slots.index(self.drag_end_time)

            # 시작이 끝보다 나중이면 교환
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx

            # 모든 헤더 셀의 배경색 변경
            for time_slot, header_cell in self.header_cells.items():
                idx = time_slots.index(time_slot)
                if start_idx <= idx <= end_idx:
                    header_cell.config(bg="#f39c12")  # 주황색으로 하이라이트
                else:
                    header_cell.config(bg="#2c3e50")  # 원래 색상

            # 그리드 셀의 배경색도 변경
            for (row, col), (cell_widget, company, time_slot) in self.grid_cells.items():
                try:
                    idx = time_slots.index(time_slot)
                    if start_idx <= idx <= end_idx:
                        # 업체 색상으로 하이라이트
                        bg_color = self.COMPANY_COLORS.get(company, "#d5f4e6")
                        cell_widget.config(bg=bg_color)
                    else:
                        # 원래 색상 복원 (업무의 시작~종료 시간 범위 확인)
                        all_tasks = self.manager.get_all_tasks()
                        cell_bg_color = "white"

                        for task_time_slot, task_info in all_tasks.items():
                            if task_info.get("company", "") == company:
                                start_time = task_time_slot
                                end_time = task_info.get("end_time", task_time_slot)

                                try:
                                    task_start_idx = time_slots.index(start_time)
                                    task_end_idx = time_slots.index(end_time)
                                    current_idx = time_slots.index(time_slot)

                                    if task_start_idx <= current_idx <= task_end_idx:
                                        cell_bg_color = self.COMPANY_COLORS.get(company, "#d5f4e6")
                                        break
                                except ValueError:
                                    continue

                        cell_widget.config(bg=cell_bg_color)
                except (ValueError, KeyError):
                    pass

        except ValueError:
            pass

    def reset_time_range_highlight(self):
        """시간 범위 하이라이트 초기화"""
        # 헤더 셀 초기화
        for header_cell in self.header_cells.values():
            header_cell.config(bg="#2c3e50")  # 원래 색상으로 복원

        # 그리드 셀 초기화
        time_slots = self.manager.time_slots
        all_tasks = self.manager.get_all_tasks()

        for (row, col), (cell_widget, company, time_slot) in self.grid_cells.items():
            # 원래 색상 복원 (업무의 시작~종료 시간 범위 확인)
            cell_bg_color = "white"

            for task_time_slot, task_info in all_tasks.items():
                if task_info.get("company", "") == company:
                    start_time = task_time_slot
                    end_time = task_info.get("end_time", task_time_slot)

                    try:
                        task_start_idx = time_slots.index(start_time)
                        task_end_idx = time_slots.index(end_time)
                        current_idx = time_slots.index(time_slot)

                        if task_start_idx <= current_idx <= task_end_idx:
                            cell_bg_color = self.COMPANY_COLORS.get(company, "#d5f4e6")
                            break
                    except ValueError:
                        continue

            cell_widget.config(bg=cell_bg_color)

    def on_cell_drag_start(self, event, time_slot, company, corp_name, row_num):
        """셀 드래그 시작 - 특수 행만 토글 가능"""
        # 셀이 특수 행인지 확인
        cell_key = None
        is_special_row = False
        for key, value in self.grid_cells.items():
            if len(value) >= 5 and value[0] == event.widget:
                cell_key = key
                is_special_row = value[4]  # is_special 플래그
                break

        # 기본 업무 행이면 아무것도 하지 않음
        if not is_special_row:
            return

        self.is_cell_dragging = True
        self.dragged_cells = set()
        self.drag_company = company  # 드래그 중인 업체 저장
        self.drag_corp_name = corp_name  # 드래그 중인 법인명 저장

        # 클릭된 셀 찾기
        clicked_widget = event.widget

        if clicked_widget:
            # 현재 셀의 배경색 확인
            current_bg = clicked_widget.cget("bg")
            # DB에 저장된 업체 색상 사용 (없으면 기본값)
            company_corp_key = (company, corp_name)
            bg_color = self.company_corp_colors.get(company_corp_key, self.COMPANY_COLORS.get(company, "#d5f4e6"))

            # 색상 토글
            if current_bg == bg_color or current_bg == bg_color.lower():
                clicked_widget.config(bg="white")
                is_colored = False
            else:
                clicked_widget.config(bg=bg_color)
                is_colored = True

            # DB에 저장 (업체명, 법인명 포함) + 로그 기록
            self.manager.save_special_time(company, corp_name, time_slot, is_colored, self.current_user)

            # 드래그된 셀 추가
            self.dragged_cells.add(id(clicked_widget))

    def on_cell_drag_motion(self, event, time_slot, company, corp_name, row_num):
        """셀 드래그 중 - 특수 행만 토글 가능"""
        if not self.is_cell_dragging:
            return

        # 현재 마우스 위치의 위젯 찾기
        widget_under_mouse = self.root.winfo_containing(
            self.root.winfo_pointerx(),
            self.root.winfo_pointery()
        )

        if widget_under_mouse and id(widget_under_mouse) not in self.dragged_cells:
            # 해당 위젯의 time_slot과 특수 행 여부 찾기
            widget_time_slot = None
            widget_row_num = None
            widget_company = None
            widget_corp_name = None
            is_special_row = False
            for (row, col), value in self.grid_cells.items():
                cell_widget = value[0]
                if cell_widget == widget_under_mouse:
                    widget_company = value[1]
                    widget_corp_name = value[2]
                    widget_time_slot = value[3]
                    widget_row_num = row
                    is_special_row = value[4] if len(value) >= 5 else False
                    break

            # 기본 업무 행이면 아무것도 하지 않음
            if widget_row_num is not None:
                if not is_special_row:
                    return

                # 같은 업체+법인명의 특수 행인지 확인
                if widget_company != self.drag_company or widget_corp_name != self.drag_corp_name:
                    return

                # 현재 위젯의 배경색 확인
                try:
                    current_bg = widget_under_mouse.cget("bg")
                    # DB에 저장된 업체 색상 사용 (없으면 기본값)
                    company_corp_key = (widget_company, widget_corp_name)
                    bg_color = self.company_corp_colors.get(company_corp_key, self.COMPANY_COLORS.get(widget_company, "#d5f4e6"))

                    # 색상 토글
                    if current_bg == bg_color or current_bg == bg_color.lower():
                        widget_under_mouse.config(bg="white")
                        is_colored = False
                    else:
                        widget_under_mouse.config(bg=bg_color)
                        is_colored = True

                    # DB에 저장 (업체명, 법인명 포함) + 로그 기록
                    if widget_time_slot and widget_company and widget_corp_name:
                        self.manager.save_special_time(widget_company, widget_corp_name, widget_time_slot, is_colored, self.current_user)

                    # 드래그된 셀 추가
                    self.dragged_cells.add(id(widget_under_mouse))
                except:
                    pass

    def on_cell_drag_end(self, event):
        """셀 드래그 종료 - 차이 시간 업데이트 및 상태 저장"""
        if self.is_cell_dragging and self.drag_company and self.drag_corp_name:
            # 드래그한 업체+법인명의 추가 시간 업데이트
            self.update_extra_time_display(self.drag_company, self.drag_corp_name)

        self.is_cell_dragging = False
        self.dragged_cells = set()
        self.drag_company = None
        self.drag_corp_name = None

    def update_extra_time_display(self, company, corp_name):
        """특정 업체+법인명의 추가 시간 표시 업데이트 및 총합 업데이트"""
        # 해당 업체+법인명의 특수 행을 찾아서 추가 시간 셀 업데이트
        time_slots = self.manager.time_slots

        # 기본 업무 템플릿에서 업체+법인명별 기본 업무 정보 가져오기
        default_tasks = self.manager.get_default_tasks()
        company_tasks = {}
        for display_order, task_info in default_tasks.items():
            if task_info.get("company", "") == company and task_info.get("task", "") == corp_name:
                time_slot = task_info.get("time_slot", "")
                if time_slot:
                    company_tasks[time_slot] = task_info

        # 추가 시간 계산
        extra_time_text = self.calculate_extra_time(company, corp_name, company_tasks)

        # 추가 시간 셀 찾아서 업데이트 (특수 행의 마지막 컬럼)
        for (row, col), value in self.grid_cells.items():
            cell_company = value[1]
            cell_corp_name = value[2]
            is_special = value[4] if len(value) >= 5 else False

            # 특수 행이고 해당 업체+법인명인 경우
            if cell_company == company and cell_corp_name == corp_name and is_special:
                # 해당 행의 마지막 컬럼 (추가 시간 셀) 찾기
                extra_time_col = len(time_slots) + 2  # +2로 변경 (법인명 열 추가)

                # Canvas frame의 모든 위젯 검색
                for widget in self.canvas_frame.grid_slaves(row=row, column=extra_time_col):
                    if isinstance(widget, tk.Label):
                        widget.config(text=extra_time_text)
                        break
                break

        # 총 추가 시간 업데이트
        self.update_total_extra_time()

    def update_total_extra_time(self):
        """총 추가 시간 및 법인별 합계 레이블 업데이트"""
        # 기본 업무 템플릿 로드
        default_tasks = self.manager.get_default_tasks()

        # 기본 업무를 (업체명, 법인명) 조합으로 그룹화
        tasks_by_company_corp = {}
        for display_order, task_info in default_tasks.items():
            company = task_info.get("company", "")
            corp_name = task_info.get("task", "")
            time_slot = task_info.get("time_slot", "")
            if company and time_slot:
                key = (company, corp_name)
                if key not in tasks_by_company_corp:
                    tasks_by_company_corp[key] = {}
                tasks_by_company_corp[key][time_slot] = task_info

        # 법인별 추가 시간 합계 계산
        corp_name_totals = {}
        total_extra_minutes = 0

        for company_corp, company_tasks in tasks_by_company_corp.items():
            company, corp_name = company_corp
            extra_time_text = self.calculate_extra_time(company, corp_name, company_tasks)

            # 시간 문자열 파싱 (+2h 30m, -1h, +45m 등)
            extra_minutes = 0
            if extra_time_text:
                sign = 1 if extra_time_text.startswith("+") else -1
                parts = extra_time_text[1:].split()  # + 또는 - 제거

                for part in parts:
                    if 'h' in part:
                        hours = int(part.replace('h', ''))
                        extra_minutes += sign * hours * 60
                    elif 'm' in part:
                        minutes = int(part.replace('m', ''))
                        extra_minutes += sign * minutes

            # 법인별 합계 누적
            if corp_name:
                if corp_name not in corp_name_totals:
                    corp_name_totals[corp_name] = 0
                corp_name_totals[corp_name] += extra_minutes

            total_extra_minutes += extra_minutes

        # 법인별 합계 레이블 업데이트
        for widget in self.canvas_frame.winfo_children():
            if isinstance(widget, tk.Label):
                text = widget.cget("text")
                # 법인별 합계 행 업데이트 (형식: "법인명: +2h 30m")
                if ":" in text and text != "총 추가 시간: 0" and not text.startswith("총 추가 시간:") and not text == "법인별 추가 시간 합계":
                    parts = text.split(":", 1)
                    if len(parts) == 2:
                        label_corp_name = parts[0].strip()
                        if label_corp_name in corp_name_totals:
                            minutes = corp_name_totals[label_corp_name]
                            if minutes != 0:
                                abs_minutes = abs(minutes)
                                hours = abs_minutes // 60
                                mins = abs_minutes % 60
                                sign_text = "+" if minutes > 0 else "-"

                                if hours > 0 and mins > 0:
                                    time_text = f"{sign_text}{hours}h {mins}m"
                                elif hours > 0:
                                    time_text = f"{sign_text}{hours}h"
                                elif mins > 0:
                                    time_text = f"{sign_text}{mins}m"
                                else:
                                    time_text = "0"
                            else:
                                time_text = "0"

                            widget.config(text=f"{label_corp_name}: {time_text}")

        # 총합을 시간 형식으로 변환
        if total_extra_minutes != 0:
            abs_minutes = abs(total_extra_minutes)
            total_hours = abs_minutes // 60
            total_mins = abs_minutes % 60
            sign_text = "+" if total_extra_minutes > 0 else "-"

            if total_hours > 0 and total_mins > 0:
                total_text = f"총 추가 시간: {sign_text}{total_hours}h {total_mins}m"
            elif total_hours > 0:
                total_text = f"총 추가 시간: {sign_text}{total_hours}h"
            elif total_mins > 0:
                total_text = f"총 추가 시간: {sign_text}{total_mins}m"
            else:
                total_text = "총 추가 시간: 0"
        else:
            total_text = "총 추가 시간: 0"

        # 총합 레이블 찾아서 업데이트
        for widget in self.canvas_frame.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text").startswith("총 추가 시간:"):
                widget.config(text=total_text)
                break

    def export_to_excel(self):
        """Excel 파일로 내보내기"""
        try:
            filename = self.manager.export_to_excel()
            messagebox.showinfo("내보내기 성공", f"Excel 파일이 저장되었습니다.\n{filename}")
        except Exception as e:
            messagebox.showerror("내보내기 오류", f"오류가 발생했습니다.\n{str(e)}")

    def manage_default_tasks(self):
        """기본 업무 관리 창 열기"""
        manage_window = tk.Toplevel(self.root)
        manage_window.title("기본 업무 관리")
        manage_window.geometry("1000x600")

        # 창이 뒤로 숨지 않도록 설정
        manage_window.transient(self.root)  # 부모 창에 종속
        manage_window.grab_set()  # 모달 창으로 설정
        manage_window.focus_force()  # 포커스 강제 설정

        # 타이틀
        title_label = tk.Label(
            manage_window,
            text="기본 업무 템플릿 관리",
            font=("굴림체", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(fill=tk.X, pady=10)

        # 메인 프레임
        main_frame = tk.Frame(manage_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 좌측: 리스트
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Treeview
        tree_scroll = ttk.Scrollbar(left_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        default_tree = ttk.Treeview(
            left_frame,
            columns=("표시순서", "시작시간", "종료시간", "업체명", "법인명", "상세 설명", "색상", "특수상황"),
            show="headings",
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=default_tree.yview)

        default_tree.heading("표시순서", text="순서")
        default_tree.heading("시작시간", text="시작")
        default_tree.heading("종료시간", text="종료")
        default_tree.heading("업체명", text="업체명")
        default_tree.heading("법인명", text="법인명")
        default_tree.heading("상세 설명", text="상세 설명")
        default_tree.heading("색상", text="색상")
        default_tree.heading("특수상황", text="특수상황")

        default_tree.column("표시순서", width=50, anchor="center")
        default_tree.column("시작시간", width=60, anchor="center")
        default_tree.column("종료시간", width=60, anchor="center")
        default_tree.column("업체명", width=70, anchor="center")
        default_tree.column("법인명", width=80, anchor="w")
        default_tree.column("상세 설명", width=150, anchor="w")
        default_tree.column("색상", width=70, anchor="center")
        default_tree.column("특수상황", width=100, anchor="w")

        default_tree.pack(fill=tk.BOTH, expand=True)

        # 우측: 입력 영역
        right_frame = tk.Frame(main_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        # 표시순서 (맨 위로 이동)
        tk.Label(right_frame, text="표시순서 (작은 숫자가 위에 표시):", font=("굴림체", 10)).pack(anchor="w")
        display_order_entry = tk.Entry(right_frame, font=("굴림체", 9))
        display_order_entry.pack(fill=tk.X, pady=(5, 10))
        display_order_entry.insert(0, "1")

        # 시작/종료 시간
        time_row_frame = tk.Frame(right_frame)
        time_row_frame.pack(fill=tk.X, pady=5)

        tk.Label(time_row_frame, text="시작:", font=("굴림체", 10)).pack(side=tk.LEFT)
        time_combo = ttk.Combobox(
            time_row_frame,
            values=self.manager.time_slots,
            state="readonly",
            width=8,
            font=("굴림체", 9)
        )
        time_combo.pack(side=tk.LEFT, padx=(5, 10))
        time_combo.set("08:30")

        tk.Label(time_row_frame, text="종료:", font=("굴림체", 10)).pack(side=tk.LEFT)
        end_time_combo = ttk.Combobox(
            time_row_frame,
            values=self.manager.time_slots,
            state="readonly",
            width=8,
            font=("굴림체", 9)
        )
        end_time_combo.pack(side=tk.LEFT, padx=(5, 0))
        end_time_combo.set("08:30")

        # 업체명
        tk.Label(right_frame, text="업체명:", font=("굴림체", 10)).pack(anchor="w")
        company_combo = ttk.Combobox(
            right_frame,
            values=[""] + self.COMPANIES,
            state="readonly",
            font=("굴림체", 9)
        )
        company_combo.pack(fill=tk.X, pady=(5, 10))
        company_combo.set("")

        # 업체 선택 시 법인명 자동 설정
        def on_company_selected_default(event=None):
            selected = company_combo.get()
            # 업체명과 법인명 매핑
            company_corp_mapping = {
                "롯데마트": "한중푸드",
                "롯데슈퍼": "한중푸드",
                "지에스": "견우마을",
                "이마트": "견우푸드",
                "홈플러스": "견우마을",
                "코스트코": "견우푸드"
            }
            if selected in company_corp_mapping:
                task_combo.set(company_corp_mapping[selected])

        company_combo.bind("<<ComboboxSelected>>", on_company_selected_default)

        # 법인명
        tk.Label(right_frame, text="법인명:", font=("굴림체", 10)).pack(anchor="w")
        task_combo = ttk.Combobox(
            right_frame,
            values=["한중푸드", "견우마을", "견우푸드"],
            font=("굴림체", 9)
        )
        task_combo.pack(fill=tk.X, pady=(5, 10))
        task_combo.set("한중푸드")

        tk.Label(right_frame, text="상세 설명:", font=("굴림체", 10)).pack(anchor="w")
        desc_text = scrolledtext.ScrolledText(
            right_frame,
            font=("굴림체", 8),
            height=6,
            wrap=tk.WORD
        )
        desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        tk.Label(right_frame, text="특수상황 (실제 DB 저장):", font=("굴림체", 10)).pack(anchor="w")
        special_text = scrolledtext.ScrolledText(
            right_frame,
            font=("굴림체", 8),
            height=4,
            wrap=tk.WORD
        )
        special_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # 색상 선택
        color_frame = tk.Frame(right_frame)
        color_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(color_frame, text="표시 색상:", font=("굴림체", 10)).pack(side=tk.LEFT)

        # 색상 미리보기 라벨
        color_preview = tk.Label(color_frame, text="    ", bg="#d5f4e6", relief="solid", width=4)
        color_preview.pack(side=tk.LEFT, padx=(10, 5))

        # 선택된 색상 저장
        selected_color = {"value": ""}

        def choose_color():
            """색상 선택 다이얼로그"""
            from tkinter import colorchooser
            current_color = selected_color["value"] if selected_color["value"] else "#d5f4e6"
            color = colorchooser.askcolor(
                title="표시 색상 선택",
                initialcolor=current_color,
                parent=manage_window  # 부모 창 지정
            )
            if color[1]:  # 색상이 선택된 경우
                selected_color["value"] = color[1]
                color_preview.config(bg=color[1])
                color_entry.delete(0, tk.END)
                color_entry.insert(0, color[1])
            # 색상 선택 후 창을 다시 앞으로
            manage_window.lift()
            manage_window.focus_force()

        color_btn = RoundedButton(color_frame, text="색상 선택", command=choose_color, font=("굴림체", 9), bg="#9b59b6", fg="white", radius=6)
        color_btn.pack(side=tk.LEFT, padx=5)

        # 색상 코드 직접 입력
        color_entry = tk.Entry(color_frame, font=("굴림체", 9), width=10)
        color_entry.pack(side=tk.LEFT, padx=5)

        def on_color_entry_change(event=None):
            """색상 코드 직접 입력 시 미리보기 업데이트"""
            color_code = color_entry.get().strip()
            if color_code and (color_code.startswith('#') and len(color_code) == 7):
                try:
                    color_preview.config(bg=color_code)
                    selected_color["value"] = color_code
                except:
                    pass

        color_entry.bind("<KeyRelease>", on_color_entry_change)

        # 색상 초기화 버튼
        def reset_color():
            """색상 초기화"""
            selected_color["value"] = ""
            color_preview.config(bg="#d5f4e6")
            color_entry.delete(0, tk.END)

        reset_color_btn = RoundedButton(color_frame, text="초기화", command=reset_color, font=("굴림체", 9), bg="#95a5a6", fg="white", radius=6)
        reset_color_btn.pack(side=tk.LEFT, padx=5)

        # 버튼들
        btn_frame = tk.Frame(right_frame)
        btn_frame.pack(fill=tk.X)

        # 선택된 display_order를 저장하는 변수
        selected_display_order = {"value": None}

        def refresh_default_list():
            """기본 업무 리스트 새로고침 - 기본업무는 템플릿, 특수상황은 실제 DB"""
            for item in default_tree.get_children():
                default_tree.delete(item)

            # 기본 업무 템플릿 조회 (display_order로 이미 정렬됨)
            default_tasks = self.manager.get_default_tasks()
            # 실제 저장된 업무 조회 (특수상황용)
            actual_tasks = self.manager.get_all_tasks()

            # display_order 순서대로 정렬 (키가 이미 display_order임)
            sorted_tasks = sorted(default_tasks.items(), key=lambda x: x[0])

            for display_order, task_info in sorted_tasks:
                time_slot = task_info.get("time_slot", "")
                # 실제 DB에서 특수상황 가져오기
                special_note = ""
                if time_slot in actual_tasks:
                    special_note = actual_tasks[time_slot].get("special_note", "")

                # 색상 값 (없으면 빈 문자열)
                color_value = task_info.get("color", "")

                default_tree.insert(
                    "",
                    tk.END,
                    values=(
                        display_order,
                        time_slot,
                        task_info.get("end_time", ""),
                        task_info.get("company", ""),
                        task_info.get("task", ""),
                        task_info.get("description", ""),
                        color_value,
                        special_note
                    )
                )

        def on_tree_select(event):
            """리스트 선택 시 (표시순서, 업체명, 종료시간, 색상 포함)"""
            selection = default_tree.selection()
            if not selection:
                return

            item = default_tree.item(selection[0])
            values = item["values"]

            # 선택된 display_order 저장
            selected_display_order["value"] = values[0] if len(values) > 0 else None

            display_order_entry.delete(0, tk.END)
            display_order_entry.insert(0, values[0] if len(values) > 0 else "1")
            time_combo.set(values[1] if len(values) > 1 else "")
            end_time_combo.set(values[2] if len(values) > 2 and values[2] else values[1] if len(values) > 1 else "")
            company_combo.set(values[3] if len(values) > 3 else "")
            task_combo.set("")
            task_combo.set(values[4] if len(values) > 4 else "")
            desc_text.delete("1.0", tk.END)
            desc_text.insert("1.0", values[5] if len(values) > 5 else "")

            # 색상 로드 (인덱스 6)
            color_value = values[6] if len(values) > 6 else ""
            color_entry.delete(0, tk.END)
            if color_value:
                color_entry.insert(0, color_value)
                color_preview.config(bg=color_value)
                selected_color["value"] = color_value
            else:
                color_preview.config(bg="#d5f4e6")
                selected_color["value"] = ""

            # 특수상황 (인덱스 7)
            special_text.delete("1.0", tk.END)
            special_text.insert("1.0", values[7] if len(values) > 7 else "")

        default_tree.bind("<<TreeviewSelect>>", on_tree_select)

        def add_default():
            """기본 업무 수정 - 기본업무는 템플릿에, 특수상황은 실제 DB에 저장"""
            time_slot = time_combo.get()
            end_time = end_time_combo.get()
            company = company_combo.get()
            task_name = task_combo.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            special_note = special_text.get("1.0", tk.END).strip()
            display_order_str = display_order_entry.get().strip()
            color = color_entry.get().strip()  # 색상 값

            if not task_name:
                messagebox.showwarning("입력 오류", "법인명을 입력해주세요.")
                return

            # 표시순서 검증
            try:
                display_order = int(display_order_str) if display_order_str else None
            except ValueError:
                messagebox.showwarning("입력 오류", "표시순서는 숫자여야 합니다.")
                return

            # 수정 확인
            if not messagebox.askyesno("수정 확인", f"순서 {display_order}번 ({time_slot}) 기본 업무를 수정하시겠습니까?"):
                return

            # 기본 업무 템플릿 저장 (색상 포함)
            success = self.manager.add_default_task(time_slot, task_name, description, company, end_time, display_order, color)

            # 특수상황이 있으면 실제 업무 테이블에 저장
            if special_note:
                self.manager.add_task(time_slot, task_name, description, special_note, company, end_time)

            if success:
                refresh_default_list()
                # 입력 필드 초기화
                time_combo.set("08:30")
                end_time_combo.set("08:30")
                company_combo.set("")
                task_combo.set("")
                desc_text.delete("1.0", tk.END)
                special_text.delete("1.0", tk.END)
                display_order_entry.delete(0, tk.END)
                display_order_entry.insert(0, "1")
                # 색상 초기화
                color_entry.delete(0, tk.END)
                color_preview.config(bg="#d5f4e6")
                selected_color["value"] = ""
                # 메인 화면 새로고침
                self.refresh_timetable()
                messagebox.showinfo("성공", "기본 업무가 수정되었습니다.")
            else:
                messagebox.showerror("오류", "수정에 실패했습니다.")

        def delete_default():
            """기본 업무 삭제"""
            # 선택된 display_order 사용
            if selected_display_order["value"] is None:
                messagebox.showwarning("경고", "삭제할 항목을 선택해주세요.")
                return

            display_order = selected_display_order["value"]
            time_slot = time_combo.get()
            result = messagebox.askyesno("삭제 확인", f"순서 {display_order}번 ({time_slot})의 기본 업무를 삭제하시겠습니까?")

            if result:
                success = self.manager.remove_default_task(display_order)
                if success:
                    refresh_default_list()
                    clear_inputs()
                    selected_display_order["value"] = None
                    # 메인 화면 새로고침
                    self.refresh_timetable()
                    messagebox.showinfo("성공", "기본 업무가 삭제되었습니다.")
                else:
                    messagebox.showerror("오류", "삭제에 실패했습니다.")

        def clear_inputs():
            """입력 필드 초기화"""
            time_combo.set("08:30")
            end_time_combo.set("08:30")
            company_combo.set("")
            task_combo.set("")
            desc_text.delete("1.0", tk.END)
            special_text.delete("1.0", tk.END)
            display_order_entry.delete(0, tk.END)
            display_order_entry.insert(0, "1")
            # 색상 초기화
            color_entry.delete(0, tk.END)
            color_preview.config(bg="#d5f4e6")
            selected_color["value"] = ""
            selected_display_order["value"] = None

        def insert_default():
            """기본 업무 삽입 - 기존 display_order들을 밀어내고 새로 삽입"""
            time_slot = time_combo.get()
            end_time = end_time_combo.get()
            company = company_combo.get()
            task_name = task_combo.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            special_note = special_text.get("1.0", tk.END).strip()
            display_order_str = display_order_entry.get().strip()
            color = color_entry.get().strip()  # 색상 값

            if not task_name:
                messagebox.showwarning("입력 오류", "법인명을 입력해주세요.")
                return

            # 표시순서 검증
            try:
                new_display_order = int(display_order_str) if display_order_str else None
                if new_display_order is None:
                    messagebox.showwarning("입력 오류", "표시순서를 입력해주세요.")
                    return
            except ValueError:
                messagebox.showwarning("입력 오류", "표시순서는 숫자여야 합니다.")
                return

            # 삽입 확인
            if not messagebox.askyesno("삽입 확인", f"순서 {new_display_order}번에 새 기본 업무를 삽입하시겠습니까?\n\n기존 {new_display_order}번 이상 항목들은 순서가 1씩 밀립니다."):
                return

            # 1. 기존 데이터에서 new_display_order 이상인 항목들의 순서를 +1씩 증가
            default_tasks = self.manager.get_default_tasks()
            tasks_to_update = []
            for display_order_key, info in default_tasks.items():
                existing_order = info.get("display_order", 999)
                if existing_order >= new_display_order:
                    tasks_to_update.append((display_order_key, info, existing_order))

            # 순서를 역순으로 업데이트 (충돌 방지)
            tasks_to_update.sort(key=lambda x: x[2], reverse=True)
            for display_order_key, info, old_order in tasks_to_update:
                self.manager.add_default_task(
                    info.get("time_slot", ""),
                    info.get("task", ""),
                    info.get("description", ""),
                    info.get("company", ""),
                    info.get("end_time", ""),
                    old_order + 1,
                    info.get("color", "")  # 기존 색상 유지
                )

            # 2. 새 항목을 지정된 순서에 삽입 (색상 포함)
            success = self.manager.add_default_task(time_slot, task_name, description, company, end_time, new_display_order, color)

            # 3. 특수상황이 있으면 실제 업무 테이블에 저장
            if special_note:
                self.manager.add_task(time_slot, task_name, description, special_note, company, end_time)

            if success:
                refresh_default_list()
                clear_inputs()
                self.refresh_timetable()
                messagebox.showinfo("성공", f"순서 {new_display_order}번에 기본 업무가 삽입되었습니다.")
            else:
                messagebox.showerror("오류", "삽입에 실패했습니다.")

        RoundedButton(
            btn_frame,
            text="삽입",
            font=("굴림체", 10),
            bg="#3498db",
            fg="white",
            radius=6,
            width=120,
            command=insert_default
        ).pack(pady=3)

        RoundedButton(
            btn_frame,
            text="수정",
            font=("굴림체", 10),
            bg="#27ae60",
            fg="white",
            radius=6,
            width=120,
            command=add_default
        ).pack(pady=3)

        RoundedButton(
            btn_frame,
            text="삭제",
            font=("굴림체", 10),
            bg="#e74c3c",
            fg="white",
            radius=6,
            width=120,
            command=delete_default
        ).pack(pady=3)

        RoundedButton(
            btn_frame,
            text="닫기",
            font=("굴림체", 10),
            bg="#95a5a6",
            fg="white",
            radius=6,
            width=120,
            command=manage_window.destroy
        ).pack(pady=3)

        # 초기 데이터 로드
        refresh_default_list()

    def show_period_summary(self):
        """기간별 법인 추가 시간 통계 창 표시"""
        summary_window = tk.Toplevel(self.root)
        summary_window.title("기간별 법인 추가 시간 통계")
        summary_window.geometry("900x600")
        summary_window.transient(self.root)

        # 기간 선택 프레임
        period_frame = tk.Frame(summary_window, bg="#ecf0f1", relief=tk.RIDGE, borderwidth=2)
        period_frame.pack(fill=tk.X, padx=10, pady=10)

        # 시작일
        tk.Label(
            period_frame,
            text="시작일:",
            font=("굴림체", 10, "bold"),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=(10, 5), pady=10)

        start_date_entry = DateEntry(
            period_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            locale='ko_KR'
        )
        start_date_entry.pack(side=tk.LEFT, padx=5, pady=10)

        # 종료일
        tk.Label(
            period_frame,
            text="종료일:",
            font=("굴림체", 10, "bold"),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=(20, 5), pady=10)

        end_date_entry = DateEntry(
            period_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            locale='ko_KR'
        )
        end_date_entry.pack(side=tk.LEFT, padx=5, pady=10)

        # 결과 표시 프레임
        result_frame = tk.Frame(summary_window)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # 스크롤바가 있는 텍스트 위젯
        result_scroll = tk.Scrollbar(result_frame)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        result_text = tk.Text(
            result_frame,
            font=("굴림체", 11),
            wrap=tk.WORD,
            yscrollcommand=result_scroll.set
        )
        result_text.pack(fill=tk.BOTH, expand=True)
        result_scroll.config(command=result_text.yview)

        def calculate_period_summary():
            """선택된 기간의 법인별 추가 시간 집계"""
            start_date = start_date_entry.get_date()
            end_date = end_date_entry.get_date()

            if start_date > end_date:
                messagebox.showerror("입력 오류", "시작일이 종료일보다 늦습니다.")
                return

            # 결과 텍스트 초기화 (NORMAL 상태로 변경 후 삭제)
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)

            # 총 일수 계산 (시작일과 종료일 모두 포함)
            total_days = (end_date - start_date).days + 1

            # 날짜 범위 표시
            result_text.insert(tk.END, f"{'='*60}\n", "header")
            result_text.insert(tk.END, f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} (총 {total_days}일)\n", "header")
            result_text.insert(tk.END, f"{'='*60}\n\n", "header")

            # 법인별 추가 시간 집계를 위한 딕셔너리
            corp_totals = {}  # key: corp_name, value: total minutes

            # 날짜별로 반복
            current_date = start_date
            date_count = 0

            while current_date <= end_date:
                # 해당 날짜로 manager의 현재 날짜 설정 (임시)
                self.manager.set_current_date(current_date)

                # 해당 날짜의 기본 업무 로드
                default_tasks = self.manager.get_default_tasks()

                # (company, corp_name)별로 그룹화
                tasks_by_company_corp = {}
                for display_order, task_info in default_tasks.items():
                    company = task_info.get("company", "")
                    corp_name = task_info.get("task", "")
                    time_slot = task_info.get("time_slot", "")
                    if company and time_slot:
                        key = (company, corp_name)
                        if key not in tasks_by_company_corp:
                            tasks_by_company_corp[key] = {}
                        tasks_by_company_corp[key][time_slot] = task_info

                # 각 (company, corp_name)에 대해 해당 날짜의 추가 시간 계산
                for company_corp, company_tasks in tasks_by_company_corp.items():
                    company, corp_name = company_corp

                    if not corp_name:
                        continue

                    # 해당 날짜의 특수 시간 조회 (manager의 current_date가 current_date로 설정됨)
                    special_times = self.manager.get_special_times(company, corp_name)

                    # 추가 시간 계산 (calculate_extra_time 메서드와 동일한 로직)
                    # 1. 기본 업무 시간 계산
                    basic_minutes = 0
                    for time_slot, task_info in company_tasks.items():
                        start_time = time_slot
                        end_time = task_info.get("end_time", time_slot)

                        try:
                            start_parts = start_time.split(":")
                            start_mins = int(start_parts[0]) * 60 + int(start_parts[1])

                            end_parts = end_time.split(":")
                            end_mins = int(end_parts[0]) * 60 + int(end_parts[1])

                            # 시간 차이 (분) - 30분 단위이므로 +30
                            duration = end_mins - start_mins + 30
                            basic_minutes += duration
                        except (ValueError, IndexError):
                            continue

                    # 2. 특수 시간 계산 (색칠된 셀 개수 × 30분)
                    special_minutes = 0
                    time_slots_list = self.manager.time_slots
                    for time_slot in time_slots_list:
                        if special_times.get(time_slot, False):
                            special_minutes += 30

                    # 3. 차이 계산
                    extra_minutes = special_minutes - basic_minutes

                    # 법인별 누적
                    if corp_name not in corp_totals:
                        corp_totals[corp_name] = 0
                    corp_totals[corp_name] += extra_minutes

                date_count += 1
                current_date += timedelta(days=1)

            # 조회 완료 후 원래 날짜로 복원
            self.manager.set_current_date(self.date_entry.get_date())

            # 결과 출력
            if not corp_totals:
                result_text.insert(tk.END, "해당 기간에 추가 시간 데이터가 없습니다.\n", "normal")
            else:
                result_text.insert(tk.END, f"총 {total_days}일 기간 동안의 법인별 추가 시간 집계:\n\n", "subheader")

                # 법인명 순으로 정렬하여 출력
                for corp_name in sorted(corp_totals.keys()):
                    minutes = corp_totals[corp_name]

                    # 시간 포맷팅
                    if minutes == 0:
                        time_text = "0"
                    else:
                        sign = "+" if minutes > 0 else "-"
                        abs_minutes = abs(minutes)
                        hours = abs_minutes // 60
                        mins = abs_minutes % 60

                        if hours > 0 and mins > 0:
                            time_text = f"{sign}{hours}h {mins}m"
                        elif hours > 0:
                            time_text = f"{sign}{hours}h"
                        else:
                            time_text = f"{sign}{mins}m"

                    # 법인명과 추가 시간 출력
                    result_text.insert(tk.END, f"  {corp_name:20s} : ", "normal")

                    # 양수면 빨간색, 음수면 파란색
                    if minutes > 0:
                        result_text.insert(tk.END, f"{time_text}\n", "positive")
                    elif minutes < 0:
                        result_text.insert(tk.END, f"{time_text}\n", "negative")
                    else:
                        result_text.insert(tk.END, f"{time_text}\n", "normal")

                # 전체 합계
                total_minutes = sum(corp_totals.values())

                result_text.insert(tk.END, f"\n{'-'*60}\n", "normal")

                # 전체 합계 포맷팅
                if total_minutes == 0:
                    total_text = "0"
                else:
                    sign = "+" if total_minutes > 0 else "-"
                    abs_minutes = abs(total_minutes)
                    hours = abs_minutes // 60
                    mins = abs_minutes % 60

                    if hours > 0 and mins > 0:
                        total_text = f"{sign}{hours}h {mins}m"
                    elif hours > 0:
                        total_text = f"{sign}{hours}h"
                    else:
                        total_text = f"{sign}{mins}m"

                result_text.insert(tk.END, f"전체 합계: ", "subheader")

                if total_minutes > 0:
                    result_text.insert(tk.END, f"{total_text}\n", "positive_bold")
                elif total_minutes < 0:
                    result_text.insert(tk.END, f"{total_text}\n", "negative_bold")
                else:
                    result_text.insert(tk.END, f"{total_text}\n", "subheader")

            # 텍스트 편집 불가 설정
            result_text.config(state=tk.DISABLED)

        # 조회 버튼 (둥근 모서리)
        btn_query = RoundedButton(
            period_frame,
            text="조회",
            font=("굴림체", 10, "bold"),
            bg="#27ae60",
            fg="white",
            radius=6,
            command=calculate_period_summary
        )
        btn_query.pack(side=tk.LEFT, padx=20, pady=10)

        # 텍스트 태그 스타일 정의
        result_text.tag_config("header", font=("굴림체", 12, "bold"), foreground="#2c3e50")
        result_text.tag_config("subheader", font=("굴림체", 11, "bold"), foreground="#34495e")
        result_text.tag_config("normal", font=("굴림체", 11), foreground="#2c3e50")
        result_text.tag_config("positive", font=("굴림체", 11), foreground="#e74c3c")
        result_text.tag_config("negative", font=("굴림체", 11), foreground="#3498db")
        result_text.tag_config("positive_bold", font=("굴림체", 12, "bold"), foreground="#e74c3c")
        result_text.tag_config("negative_bold", font=("굴림체", 12, "bold"), foreground="#3498db")

    def check_for_updates(self):
        """업데이트 확인 (메뉴에서 호출)"""
        manual_update_check(self.root)

    def logout(self):
        """로그아웃"""
        if messagebox.askyesno("로그아웃", "로그아웃 하시겠습니까?"):
            self.manager.close()
            self.root.destroy()
            # 새 창으로 로그인 화면 표시
            new_root = tk.Tk()
            LoginWindow(new_root, lambda user: start_main_app(new_root, user))
            new_root.mainloop()

    def exit_program(self):
        """프로그램 종료"""
        if messagebox.askyesno("종료", "프로그램을 종료하시겠습니까?"):
            self.manager.close()
            self.root.destroy()

    def show_change_password(self):
        """비밀번호 변경 창"""
        if not self.current_user:
            return

        pw_window = tk.Toplevel(self.root)
        pw_window.title("비밀번호 변경")
        pw_window.geometry("350x250")
        pw_window.resizable(False, False)
        pw_window.transient(self.root)
        pw_window.grab_set()

        # 중앙 배치
        pw_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 250) // 2
        pw_window.geometry(f"+{x}+{y}")

        # 폼
        form_frame = tk.Frame(pw_window)
        form_frame.pack(pady=30)

        tk.Label(form_frame, text="현재 비밀번호:", font=("굴림체", 10)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        current_pw = tk.Entry(form_frame, font=("굴림체", 10), width=20, show="*")
        current_pw.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="새 비밀번호:", font=("굴림체", 10)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        new_pw = tk.Entry(form_frame, font=("굴림체", 10), width=20, show="*")
        new_pw.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(form_frame, text="새 비밀번호 확인:", font=("굴림체", 10)).grid(row=2, column=0, padx=10, pady=10, sticky="e")
        confirm_pw = tk.Entry(form_frame, font=("굴림체", 10), width=20, show="*")
        confirm_pw.grid(row=2, column=1, padx=10, pady=10)

        def change_password():
            current = current_pw.get()
            new = new_pw.get()
            confirm = confirm_pw.get()

            if not current or not new or not confirm:
                messagebox.showwarning("입력 오류", "모든 필드를 입력해주세요.")
                return

            if new != confirm:
                messagebox.showwarning("입력 오류", "새 비밀번호가 일치하지 않습니다.")
                return

            if len(new) < 4:
                messagebox.showwarning("입력 오류", "비밀번호는 4자 이상이어야 합니다.")
                return

            # 현재 비밀번호 확인
            db = Database()
            db.connect()
            user = db.authenticate_user(self.current_user['username'], current)

            if not user:
                messagebox.showerror("오류", "현재 비밀번호가 올바르지 않습니다.")
                db.disconnect()
                return

            # 비밀번호 변경
            if db.change_password(self.current_user['id'], new):
                messagebox.showinfo("완료", "비밀번호가 변경되었습니다.")
                pw_window.destroy()
            else:
                messagebox.showerror("오류", "비밀번호 변경에 실패했습니다.")

            db.disconnect()

        # 버튼
        btn_frame = tk.Frame(pw_window)
        btn_frame.pack(pady=10)

        RoundedButton(
            btn_frame, text="변경", font=("굴림체", 10),
            bg="#3498db", fg="white", radius=6,
            command=change_password
        ).pack(side=tk.LEFT, padx=5)

        RoundedButton(
            btn_frame, text="취소", font=("굴림체", 10),
            bg="#95a5a6", fg="white", radius=6,
            command=pw_window.destroy
        ).pack(side=tk.LEFT, padx=5)

    def show_change_logs(self):
        """변경 로그 조회 창 (관리자 전용)"""
        if not self.current_user or not self.current_user.get('is_admin'):
            messagebox.showwarning("권한 없음", "관리자만 사용할 수 있습니다.")
            return

        log_window = tk.Toplevel(self.root)
        log_window.title("변경 로그 조회")
        log_window.geometry("1000x600")
        log_window.resizable(True, True)
        log_window.transient(self.root)

        # 창을 맨 앞으로
        log_window.lift()
        log_window.focus_force()

        # 메인 컨테이너
        main_container = tk.Frame(log_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 상단 필터 영역 ===
        filter_frame = tk.LabelFrame(main_container, text="검색 조건", padx=10, pady=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # 1행: 날짜 필터
        row1 = tk.Frame(filter_frame)
        row1.pack(fill=tk.X, pady=3)

        use_date_filter = tk.BooleanVar(value=False)
        tk.Checkbutton(row1, text="날짜필터:", variable=use_date_filter).pack(side=tk.LEFT, padx=5)

        start_date_entry = DateEntry(row1, width=12, date_pattern='yyyy-mm-dd')
        start_date_entry.pack(side=tk.LEFT, padx=2)
        start_date_entry.set_date(datetime.now() - timedelta(days=7))

        tk.Label(row1, text="~").pack(side=tk.LEFT, padx=2)
        end_date_entry = DateEntry(row1, width=12, date_pattern='yyyy-mm-dd')
        end_date_entry.pack(side=tk.LEFT, padx=2)

        # 2행: 업체/사용자 필터
        row2 = tk.Frame(filter_frame)
        row2.pack(fill=tk.X, pady=3)

        tk.Label(row2, text="업체:").pack(side=tk.LEFT, padx=5)
        company_var = tk.StringVar(value="전체")
        company_combo = ttk.Combobox(row2, textvariable=company_var, width=15, state="readonly")
        try:
            companies = ["전체"] + self.manager.get_companies()
        except:
            companies = ["전체"]
        company_combo['values'] = companies
        company_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(row2, text="사용자:").pack(side=tk.LEFT, padx=(20, 5))
        user_var = tk.StringVar(value="전체")
        user_combo = ttk.Combobox(row2, textvariable=user_var, width=15, state="readonly")
        users = ["전체"]
        try:
            all_users = self.manager.db.get_all_users()
            if all_users:
                users.extend([u['username'] for u in all_users])
        except:
            pass
        user_combo['values'] = users
        user_combo.pack(side=tk.LEFT, padx=5)

        # 3행: 조회 버튼
        row3 = tk.Frame(filter_frame)
        row3.pack(fill=tk.X, pady=5)

        search_btn = RoundedButton(row3, text="조회", font=("굴림체", 10, "bold"),
                               bg="#3498db", fg="white", radius=6)
        search_btn.pack(side=tk.LEFT, padx=5)

        result_label = tk.Label(row3, text="", font=("굴림체", 10))
        result_label.pack(side=tk.LEFT, padx=10)

        # === 중간 그리드 영역 ===
        tree_frame = tk.Frame(main_container, relief=tk.SUNKEN, borderwidth=1)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Treeview + 스크롤바
        columns = ("변경일시", "사용자", "작업날짜", "업체", "법인명", "시간", "작업", "이전값", "새값")

        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        log_tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings", height=20,
            yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set
        )
        log_tree.pack(fill=tk.BOTH, expand=True)

        y_scrollbar.config(command=log_tree.yview)
        x_scrollbar.config(command=log_tree.xview)

        # 컬럼 설정
        col_widths = {"변경일시": 140, "사용자": 80, "작업날짜": 90,
                      "업체": 100, "법인명": 100, "시간": 60,
                      "작업": 60, "이전값": 50, "새값": 50}
        for col in columns:
            log_tree.heading(col, text=col)
            log_tree.column(col, width=col_widths.get(col, 80), anchor=tk.CENTER)

        # === 하단 버튼 영역 ===
        btn_frame = tk.Frame(main_container)
        btn_frame.pack(fill=tk.X)

        RoundedButton(btn_frame, text="닫기", font=("굴림체", 10),
                  bg="#95a5a6", fg="white", radius=6,
                  command=log_window.destroy).pack()

        # === 조회 함수 ===
        def search_logs():
            for item in log_tree.get_children():
                log_tree.delete(item)

            start_dt = start_date_entry.get_date() if use_date_filter.get() else None
            end_dt = end_date_entry.get_date() if use_date_filter.get() else None
            company = company_var.get() if company_var.get() != "전체" else None
            username = user_var.get() if user_var.get() != "전체" else None

            try:
                logs = self.manager.get_change_logs(
                    start_date=start_dt, end_date=end_dt,
                    company=company, username=username
                )
            except Exception as e:
                messagebox.showerror("오류", f"로그 조회 실패: {e}")
                logs = []

            for log in logs:
                log_tree.insert("", tk.END, values=(
                    log.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if log.get('created_at') else '',
                    log.get('display_name') or log.get('username', ''),
                    log.get('work_date', '').strftime('%Y-%m-%d') if log.get('work_date') else '',
                    log.get('company', ''),
                    log.get('corp_name', ''),
                    log.get('time_slot', ''),
                    log.get('action', ''),
                    log.get('old_value', ''),
                    log.get('new_value', '')
                ))

            result_label.config(text=f"조회 결과: {len(logs)}건")

        # 버튼에 명령 연결
        search_btn.config(command=search_logs)

        # 초기 조회
        log_window.after(100, search_logs)

        # 업데이트 강제
        log_window.update_idletasks()

    def show_user_management(self):
        """사용자 관리 창 (관리자 전용)"""
        if not self.current_user or not self.current_user.get('is_admin'):
            messagebox.showwarning("권한 없음", "관리자만 사용할 수 있습니다.")
            return

        user_window = tk.Toplevel(self.root)
        user_window.title("사용자 관리")
        user_window.geometry("700x500")
        user_window.resizable(False, False)
        user_window.transient(self.root)

        # 중앙 배치
        user_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 700) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        user_window.geometry(f"+{x}+{y}")

        # 데이터베이스 연결
        db = Database()
        db.connect()

        # 사용자 목록 프레임
        list_frame = tk.Frame(user_window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Treeview
        columns = ("ID", "사용자명", "표시이름", "관리자", "활성", "마지막로그인")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)

        tree.heading("ID", text="ID")
        tree.heading("사용자명", text="사용자명")
        tree.heading("표시이름", text="표시이름")
        tree.heading("관리자", text="관리자")
        tree.heading("활성", text="활성")
        tree.heading("마지막로그인", text="마지막 로그인")

        tree.column("ID", width=40, anchor="center")
        tree.column("사용자명", width=100)
        tree.column("표시이름", width=120)
        tree.column("관리자", width=60, anchor="center")
        tree.column("활성", width=60, anchor="center")
        tree.column("마지막로그인", width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def refresh_users():
            """사용자 목록 새로고침"""
            for item in tree.get_children():
                tree.delete(item)

            users = db.get_all_users()
            for user in users:
                last_login = user['last_login'].strftime('%Y-%m-%d %H:%M') if user['last_login'] else '-'
                tree.insert("", tk.END, values=(
                    user['id'],
                    user['username'],
                    user['display_name'],
                    "O" if user['is_admin'] else "",
                    "O" if user['is_active'] else "X",
                    last_login
                ))

        def add_user():
            """사용자 추가"""
            add_window = tk.Toplevel(user_window)
            add_window.title("사용자 추가")
            add_window.geometry("350x280")
            add_window.resizable(False, False)
            add_window.transient(user_window)
            add_window.grab_set()

            form = tk.Frame(add_window)
            form.pack(pady=20)

            tk.Label(form, text="사용자 ID:", font=("굴림체", 10)).grid(row=0, column=0, padx=10, pady=8, sticky="e")
            username_entry = tk.Entry(form, font=("굴림체", 10), width=20)
            username_entry.grid(row=0, column=1, padx=10, pady=8)

            tk.Label(form, text="비밀번호:", font=("굴림체", 10)).grid(row=1, column=0, padx=10, pady=8, sticky="e")
            password_entry = tk.Entry(form, font=("굴림체", 10), width=20, show="*")
            password_entry.grid(row=1, column=1, padx=10, pady=8)

            tk.Label(form, text="표시이름:", font=("굴림체", 10)).grid(row=2, column=0, padx=10, pady=8, sticky="e")
            display_entry = tk.Entry(form, font=("굴림체", 10), width=20)
            display_entry.grid(row=2, column=1, padx=10, pady=8)

            is_admin_var = tk.BooleanVar()
            tk.Checkbutton(form, text="관리자 권한", variable=is_admin_var, font=("굴림체", 10)).grid(row=3, column=1, pady=8, sticky="w")

            def save_user():
                username = username_entry.get().strip()
                password = password_entry.get()
                display_name = display_entry.get().strip()

                if not username or not password:
                    messagebox.showwarning("입력 오류", "사용자 ID와 비밀번호는 필수입니다.")
                    return

                if db.add_user(username, password, display_name, is_admin_var.get()):
                    messagebox.showinfo("완료", "사용자가 추가되었습니다.")
                    refresh_users()
                    add_window.destroy()
                else:
                    messagebox.showerror("오류", "사용자 추가에 실패했습니다.\n이미 존재하는 ID일 수 있습니다.")

            add_btn = RoundedButton(form, text="추가", font=("굴림체", 10), bg="#27ae60", fg="white", radius=6, command=save_user)
            add_btn.grid(row=4, column=0, columnspan=2, pady=20)

        def delete_user():
            """사용자 삭제"""
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("선택 필요", "삭제할 사용자를 선택하세요.")
                return

            item = tree.item(selected[0])
            user_id = item['values'][0]
            username = item['values'][1]

            if username == 'admin':
                messagebox.showwarning("삭제 불가", "기본 관리자 계정은 삭제할 수 없습니다.")
                return

            if messagebox.askyesno("확인", f"'{username}' 사용자를 삭제하시겠습니까?"):
                if db.delete_user(user_id):
                    refresh_users()
                    messagebox.showinfo("완료", "사용자가 삭제되었습니다.")
                else:
                    messagebox.showerror("오류", "삭제에 실패했습니다.")

        def reset_password():
            """비밀번호 초기화"""
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("선택 필요", "사용자를 선택하세요.")
                return

            item = tree.item(selected[0])
            user_id = item['values'][0]
            username = item['values'][1]

            if messagebox.askyesno("확인", f"'{username}'의 비밀번호를 초기화하시겠습니까?\n(초기 비밀번호: 1234)"):
                if db.change_password(user_id, "1234"):
                    messagebox.showinfo("완료", "비밀번호가 '1234'로 초기화되었습니다.")
                else:
                    messagebox.showerror("오류", "비밀번호 초기화에 실패했습니다.")

        # 버튼 프레임
        btn_frame = tk.Frame(user_window)
        btn_frame.pack(pady=10)

        RoundedButton(btn_frame, text="사용자 추가", font=("굴림체", 10), bg="#27ae60", fg="white", radius=6, command=add_user).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="비밀번호 초기화", font=("굴림체", 10), bg="#f39c12", fg="white", radius=6, command=reset_password).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="사용자 삭제", font=("굴림체", 10), bg="#e74c3c", fg="white", radius=6, command=delete_user).pack(side=tk.LEFT, padx=5)
        RoundedButton(btn_frame, text="닫기", font=("굴림체", 10), bg="#95a5a6", fg="white", radius=6, command=lambda: (db.disconnect(), user_window.destroy())).pack(side=tk.LEFT, padx=5)

        # 창 닫을 때 DB 연결 해제
        user_window.protocol("WM_DELETE_WINDOW", lambda: (db.disconnect(), user_window.destroy()))

        # 초기 로드
        refresh_users()

    def show_about(self):
        """버전 정보 표시"""
        about_window = tk.Toplevel(self.root)
        about_window.title("버전 정보")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.transient(self.root)

        # 중앙 배치
        about_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 500) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        about_window.geometry(f"+{x}+{y}")

        # 제목
        title_label = tk.Label(
            about_window,
            text="견우물류 업무 타임테이블",
            font=("굴림체", 16, "bold"),
            fg="#2c3e50"
        )
        title_label.pack(pady=20)

        # 버전
        version_label = tk.Label(
            about_window,
            text=f"버전 {VERSION}",
            font=("굴림체", 12),
            fg="#7f8c8d"
        )
        version_label.pack(pady=5)

        # 구분선
        separator = tk.Frame(about_window, height=2, bg="#ecf0f1")
        separator.pack(fill=tk.X, padx=50, pady=20)

        # 변경사항
        changes_label = tk.Label(
            about_window,
            text="주요 기능:",
            font=("굴림체", 11, "bold")
        )
        changes_label.pack(pady=10)

        # 변경사항 목록
        changes_frame = tk.Frame(about_window)
        changes_frame.pack(fill=tk.BOTH, expand=True, padx=40)

        scrollbar = tk.Scrollbar(changes_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        changes_text = tk.Text(
            changes_frame,
            wrap=tk.WORD,
            font=("굴림체", 9),
            yscrollcommand=scrollbar.set,
            height=8,
            relief=tk.FLAT,
            bg="#f8f9fa"
        )
        changes_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=changes_text.yview)

        # 변경사항 추가
        for change in get_latest_changes():
            changes_text.insert(tk.END, f"• {change}\n")

        changes_text.config(state=tk.DISABLED)

        # 닫기 버튼 (둥근 모서리)
        close_btn = RoundedButton(
            about_window,
            text="닫기",
            font=("굴림체", 10),
            bg="#95a5a6",
            fg="white",
            radius=6,
            command=about_window.destroy
        )
        close_btn.pack(pady=20)

    def on_closing(self):
        """프로그램 종료 시 호출"""
        self.manager.close()
        self.root.destroy()


def start_main_app(root, user):
    """로그인 성공 후 메인 앱 시작"""
    root.deiconify()  # 메인 창 표시
    app = TimeTableGUI(root, user)

    # 창을 맨 앞으로 가져오기
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)
    root.after(100, lambda: root.attributes('-topmost', False))


def get_icon_path():
    """아이콘 파일 경로 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 실행 파일
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'app_icon.ico')


def main():
    """메인 함수"""
    root = tk.Tk()
    root.withdraw()  # 초기 창 숨김

    # 아이콘 설정
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except:
            pass

    # 로그인 전 업데이트 확인
    try:
        check_for_updates_on_startup(root)
    except:
        pass

    # 로그인 창 표시
    login = LoginWindow(root, lambda user: start_main_app(root, user))

    root.mainloop()


if __name__ == "__main__":
    main()
