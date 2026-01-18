import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from timetable_manager import TimeTableManager
from tkcalendar import DateEntry
from datetime import date, datetime, timedelta
from version import VERSION, get_latest_changes
from updater import check_for_updates_on_startup, manual_update_check


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

    def __init__(self, root):
        self.root = root
        self.root.title("견우물류 업무 타임테이블 (DB 연동)")

        # 화면 크기 가져오기
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 창 크기 설정 (가로: 최대, 세로: 최대)
        window_width = screen_width - 10  # 거의 전체 화면
        window_height = screen_height - 100  # 작업 표시줄 영역 제외

        # 창 위치 (화면 중앙)
        x_position = 0
        y_position = 0

        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")

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

        title_label = tk.Label(
            title_frame,
            text=f"견우물류 업무 타임테이블 v{VERSION}",
            font=("굴림체", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=10)

        # 메뉴바 추가
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

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
            font=("굴림체", 11, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(side=tk.LEFT, padx=(20, 10), pady=10)

        self.date_entry = DateEntry(
            date_frame,
            font=("굴림체", 10),
            width=15,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd',
            locale='ko_KR'
        )
        self.date_entry.pack(side=tk.LEFT, padx=5, pady=10)
        self.date_entry.bind("<<DateEntrySelected>>", self.on_date_changed)

        # 날짜 이동 버튼
        btn_prev = tk.Button(
            date_frame,
            text="◀ 이전",
            font=("굴림체", 9),
            bg="#3498db",
            fg="white",
            command=self.prev_date,
            cursor="hand2"
        )
        btn_prev.pack(side=tk.LEFT, padx=5, pady=10)

        btn_today = tk.Button(
            date_frame,
            text="오늘",
            font=("굴림체", 9),
            bg="#27ae60",
            fg="white",
            command=self.goto_today,
            cursor="hand2"
        )
        btn_today.pack(side=tk.LEFT, padx=5, pady=10)

        btn_next = tk.Button(
            date_frame,
            text="다음 ▶",
            font=("굴림체", 9),
            bg="#3498db",
            fg="white",
            command=self.next_date,
            cursor="hand2"
        )
        btn_next.pack(side=tk.LEFT, padx=5, pady=10)

        # 기본 업무 관리 버튼
        btn_manage_default = tk.Button(
            date_frame,
            text="기본 업무 관리",
            font=("굴림체", 9),
            bg="#16a085",
            fg="white",
            command=self.manage_default_tasks,
            cursor="hand2"
        )
        btn_manage_default.pack(side=tk.LEFT, padx=5, pady=10)

        # 기간별 통계 버튼
        btn_period_summary = tk.Button(
            date_frame,
            text="기간별 통계",
            font=("굴림체", 9),
            bg="#2980b9",
            fg="white",
            command=self.show_period_summary,
            cursor="hand2"
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

        for display_order, task_info in default_tasks.items():
            company = task_info.get("company", "")
            corp_name = task_info.get("task", "")  # task_name이 법인명
            time_slot = task_info.get("time_slot", "")

            if company and time_slot:
                key = (company, corp_name)
                if key not in tasks_by_company_corp:
                    tasks_by_company_corp[key] = {}
                    company_corp_display_order[key] = display_order
                else:
                    # 해당 조합의 최소 display_order 유지
                    if display_order < company_corp_display_order[key]:
                        company_corp_display_order[key] = display_order
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
            header_label = tk.Label(
                self.canvas_frame,
                text=time_slot,
                font=("굴림체", 10, "bold"),
                bg="#2c3e50",
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
            bg_color = self.COMPANY_COLORS.get(company, "#d5f4e6")

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

                # 셀 생성 (기본 업무 행은 클릭 불가)
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
                                self.manager.save_special_time(company, corp_name, time_slot, True)
                                break
                        except ValueError:
                            continue

                # 특수상황 셀 생성
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
        company_color = self.COMPANY_COLORS.get(company, "#d5f4e6")

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
            bg_color = self.COMPANY_COLORS.get(company, "#d5f4e6")

            # 색상 토글
            if current_bg == bg_color or current_bg == bg_color.lower():
                clicked_widget.config(bg="white")
                is_colored = False
            else:
                clicked_widget.config(bg=bg_color)
                is_colored = True

            # DB에 저장 (업체명, 법인명 포함)
            self.manager.save_special_time(company, corp_name, time_slot, is_colored)

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
                    bg_color = self.COMPANY_COLORS.get(widget_company, "#d5f4e6")

                    # 색상 토글
                    if current_bg == bg_color or current_bg == bg_color.lower():
                        widget_under_mouse.config(bg="white")
                        is_colored = False
                    else:
                        widget_under_mouse.config(bg=bg_color)
                        is_colored = True

                    # DB에 저장 (업체명, 법인명 포함)
                    if widget_time_slot and widget_company and widget_corp_name:
                        self.manager.save_special_time(widget_company, widget_corp_name, widget_time_slot, is_colored)

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
            columns=("표시순서", "시작시간", "종료시간", "업체명", "법인명", "상세 설명", "특수상황"),
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
        default_tree.heading("특수상황", text="특수상황")

        default_tree.column("표시순서", width=50, anchor="center")
        default_tree.column("시작시간", width=70, anchor="center")
        default_tree.column("종료시간", width=70, anchor="center")
        default_tree.column("업체명", width=80, anchor="center")
        default_tree.column("법인명", width=100, anchor="w")
        default_tree.column("상세 설명", width=180, anchor="w")
        default_tree.column("특수상황", width=120, anchor="w")

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
                        special_note
                    )
                )

        def on_tree_select(event):
            """리스트 선택 시 (표시순서, 업체명, 종료시간 포함)"""
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
            special_text.delete("1.0", tk.END)
            special_text.insert("1.0", values[6] if len(values) > 6 else "")

        default_tree.bind("<<TreeviewSelect>>", on_tree_select)

        def add_default():
            """기본 업무 추가 - 기본업무는 템플릿에, 특수상황은 실제 DB에 저장"""
            time_slot = time_combo.get()
            end_time = end_time_combo.get()
            company = company_combo.get()
            task_name = task_combo.get().strip()
            description = desc_text.get("1.0", tk.END).strip()
            special_note = special_text.get("1.0", tk.END).strip()
            display_order_str = display_order_entry.get().strip()

            if not task_name:
                messagebox.showwarning("입력 오류", "법인명을 입력해주세요.")
                return

            # 표시순서 검증
            try:
                display_order = int(display_order_str) if display_order_str else None
            except ValueError:
                messagebox.showwarning("입력 오류", "표시순서는 숫자여야 합니다.")
                return

            # 기본 업무 템플릿 저장
            success = self.manager.add_default_task(time_slot, task_name, description, company, end_time, display_order)

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
                # 메인 화면 새로고침
                self.refresh_timetable()
                messagebox.showinfo("성공", "기본 업무 및 특수상황이 저장되었습니다.")
            else:
                messagebox.showerror("오류", "저장에 실패했습니다.")

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
                    old_order + 1
                )

            # 2. 새 항목을 지정된 순서에 삽입
            success = self.manager.add_default_task(time_slot, task_name, description, company, end_time, new_display_order)

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

        tk.Button(
            btn_frame,
            text="삽입",
            font=("굴림체", 10),
            bg="#3498db",
            fg="white",
            command=insert_default
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            btn_frame,
            text="저장",
            font=("굴림체", 10),
            bg="#27ae60",
            fg="white",
            command=add_default
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            btn_frame,
            text="삭제",
            font=("굴림체", 10),
            bg="#e74c3c",
            fg="white",
            command=delete_default
        ).pack(fill=tk.X, pady=2)

        tk.Button(
            btn_frame,
            text="닫기",
            font=("굴림체", 10),
            bg="#95a5a6",
            fg="white",
            command=manage_window.destroy
        ).pack(fill=tk.X, pady=2)

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

            # 결과 텍스트 초기화
            result_text.delete(1.0, tk.END)

            # 날짜 범위 표시
            result_text.insert(tk.END, f"{'='*60}\n", "header")
            result_text.insert(tk.END, f"기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}\n", "header")
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
                result_text.insert(tk.END, f"총 {date_count}일 기간 동안의 법인별 추가 시간 집계:\n\n", "subheader")

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

        # 조회 버튼
        btn_query = tk.Button(
            period_frame,
            text="조회",
            font=("굴림체", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=calculate_period_summary,
            cursor="hand2",
            width=10
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

        # 닫기 버튼
        close_btn = tk.Button(
            about_window,
            text="닫기",
            font=("굴림체", 10),
            bg="#95a5a6",
            fg="white",
            command=about_window.destroy,
            cursor="hand2",
            width=10,
            pady=5
        )
        close_btn.pack(pady=20)

    def on_closing(self):
        """프로그램 종료 시 호출"""
        self.manager.close()
        self.root.destroy()


def main():
    """메인 함수"""
    root = tk.Tk()
    app = TimeTableGUI(root)

    # 프로그램 시작 시 자동으로 업데이트 확인 (백그라운드에서 실행)
    root.after(1000, lambda: check_for_updates_on_startup(root))

    root.mainloop()


if __name__ == "__main__":
    main()
