import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from timetable_manager import TimeTableManager
from tkcalendar import DateEntry
from datetime import date, datetime


class TimeTableGUI:
    """견우물류 타임테이블 GUI 애플리케이션"""

    def __init__(self, root):
        self.root = root
        self.root.title("견우물류 업무 타임테이블 (DB 연동)")
        self.root.geometry("1100x750")

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
            text="견우물류 업무 타임테이블 (DB)",
            font=("맑은 고딕", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        # 날짜 선택 영역
        date_frame = tk.Frame(self.root, bg="#34495e", height=50)
        date_frame.pack(fill=tk.X, side=tk.TOP)

        # 날짜 선택 위젯
        tk.Label(
            date_frame,
            text="작업 날짜:",
            font=("맑은 고딕", 11, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(side=tk.LEFT, padx=(20, 10), pady=10)

        self.date_entry = DateEntry(
            date_frame,
            font=("맑은 고딕", 10),
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
            font=("맑은 고딕", 9),
            bg="#3498db",
            fg="white",
            command=self.prev_date,
            cursor="hand2"
        )
        btn_prev.pack(side=tk.LEFT, padx=5, pady=10)

        btn_today = tk.Button(
            date_frame,
            text="오늘",
            font=("맑은 고딕", 9),
            bg="#27ae60",
            fg="white",
            command=self.goto_today,
            cursor="hand2"
        )
        btn_today.pack(side=tk.LEFT, padx=5, pady=10)

        btn_next = tk.Button(
            date_frame,
            text="다음 ▶",
            font=("맑은 고딕", 9),
            bg="#3498db",
            fg="white",
            command=self.next_date,
            cursor="hand2"
        )
        btn_next.pack(side=tk.LEFT, padx=5, pady=10)

        # 날짜 복사 버튼
        btn_copy = tk.Button(
            date_frame,
            text="다른 날짜에서 복사",
            font=("맑은 고딕", 9),
            bg="#9b59b6",
            fg="white",
            command=self.copy_from_date,
            cursor="hand2"
        )
        btn_copy.pack(side=tk.LEFT, padx=20, pady=10)

        # 메인 컨테이너
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 좌측: 타임테이블 표시 영역
        left_frame = tk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 타임테이블 Treeview
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 스크롤바
        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Treeview 생성
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("시간", "업무명", "상세 설명"),
            show="headings",
            yscrollcommand=tree_scroll.set,
            height=20
        )
        tree_scroll.config(command=self.tree.yview)

        # 컬럼 설정
        self.tree.heading("시간", text="시간")
        self.tree.heading("업무명", text="업무명")
        self.tree.heading("상세 설명", text="상세 설명")

        self.tree.column("시간", width=80, anchor="center")
        self.tree.column("업무명", width=200, anchor="w")
        self.tree.column("상세 설명", width=300, anchor="w")

        self.tree.pack(fill=tk.BOTH, expand=True)

        # 더블클릭 이벤트 바인딩
        self.tree.bind("<Double-1>", self.on_double_click)

        # 우측: 업무 추가/수정 영역
        right_frame = tk.Frame(main_container, width=320)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        # 제목
        control_title = tk.Label(
            right_frame,
            text="업무 관리",
            font=("맑은 고딕", 14, "bold")
        )
        control_title.pack(pady=(0, 10))

        # 시간 선택
        time_frame = tk.Frame(right_frame)
        time_frame.pack(fill=tk.X, pady=5)

        tk.Label(time_frame, text="시간:", font=("맑은 고딕", 10)).pack(side=tk.LEFT)
        self.time_combo = ttk.Combobox(
            time_frame,
            values=self.manager.time_slots,
            state="readonly",
            width=10
        )
        self.time_combo.pack(side=tk.LEFT, padx=(10, 0))
        self.time_combo.set("07:00")

        # 업무명 입력
        task_frame = tk.Frame(right_frame)
        task_frame.pack(fill=tk.X, pady=10)

        tk.Label(task_frame, text="업무명:", font=("맑은 고딕", 10)).pack(anchor="w")
        self.task_entry = tk.Entry(task_frame, font=("맑은 고딕", 10))
        self.task_entry.pack(fill=tk.X, pady=(5, 0))

        # 상세 설명 입력
        desc_frame = tk.Frame(right_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        tk.Label(desc_frame, text="상세 설명:", font=("맑은 고딕", 10)).pack(anchor="w")
        self.desc_text = scrolledtext.ScrolledText(
            desc_frame,
            font=("맑은 고딕", 9),
            height=10,
            wrap=tk.WORD
        )
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # 버튼 영역
        button_frame = tk.Frame(right_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 추가/수정 버튼
        self.add_button = tk.Button(
            button_frame,
            text="업무 추가",
            font=("맑은 고딕", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=self.add_or_update_task,
            cursor="hand2"
        )
        self.add_button.pack(fill=tk.X, pady=2)

        # 삭제 버튼
        delete_button = tk.Button(
            button_frame,
            text="업무 삭제",
            font=("맑은 고딕", 10),
            bg="#e74c3c",
            fg="white",
            command=self.delete_task,
            cursor="hand2"
        )
        delete_button.pack(fill=tk.X, pady=2)

        # 초기화 버튼
        clear_button = tk.Button(
            button_frame,
            text="입력 초기화",
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white",
            command=self.clear_inputs,
            cursor="hand2"
        )
        clear_button.pack(fill=tk.X, pady=2)

        # Excel 내보내기 버튼
        export_button = tk.Button(
            button_frame,
            text="Excel 내보내기",
            font=("맑은 고딕", 10),
            bg="#3498db",
            fg="white",
            command=self.export_to_excel,
            cursor="hand2"
        )
        export_button.pack(fill=tk.X, pady=2)

    def on_date_changed(self, event=None):
        """날짜 변경 시 호출"""
        selected_date = self.date_entry.get_date()
        self.manager.set_current_date(selected_date)
        self.refresh_timetable()
        self.clear_inputs()

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

    def copy_from_date(self):
        """다른 날짜의 업무 복사"""
        # 복사 다이얼로그 생성
        copy_window = tk.Toplevel(self.root)
        copy_window.title("날짜 복사")
        copy_window.geometry("350x150")
        copy_window.resizable(False, False)

        tk.Label(
            copy_window,
            text="복사할 날짜를 선택하세요:",
            font=("맑은 고딕", 10)
        ).pack(pady=10)

        source_date_entry = DateEntry(
            copy_window,
            font=("맑은 고딕", 10),
            width=15,
            date_pattern='yyyy-mm-dd'
        )
        source_date_entry.pack(pady=10)

        def do_copy():
            source_date = source_date_entry.get_date()
            target_date = self.date_entry.get_date()

            if source_date == target_date:
                messagebox.showwarning("복사 오류", "같은 날짜는 복사할 수 없습니다.")
                return

            success = self.manager.copy_tasks_to_date(source_date, target_date)
            if success:
                self.manager.set_current_date(target_date)
                self.refresh_timetable()
                messagebox.showinfo("성공", f"{source_date}의 업무가 복사되었습니다.")
                copy_window.destroy()
            else:
                messagebox.showerror("오류", "업무 복사 중 오류가 발생했습니다.")

        btn_frame = tk.Frame(copy_window)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="복사",
            font=("맑은 고딕", 10),
            bg="#27ae60",
            fg="white",
            command=do_copy,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="취소",
            font=("맑은 고딕", 10),
            bg="#95a5a6",
            fg="white",
            command=copy_window.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=5)

    def refresh_timetable(self):
        """타임테이블 새로고침"""
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 모든 시간 슬롯 표시
        for time_slot in self.manager.time_slots:
            task_info = self.manager.get_task(time_slot)
            if task_info:
                task_name = task_info.get("task", "")
                description = task_info.get("description", "")
            else:
                task_name = ""
                description = ""

            # 행 추가
            self.tree.insert(
                "",
                tk.END,
                values=(time_slot, task_name, description),
                tags=("empty" if not task_name else "filled")
            )

        # 태그 스타일 설정
        self.tree.tag_configure("empty", background="#ecf0f1")
        self.tree.tag_configure("filled", background="#d5f4e6")

    def on_double_click(self, event):
        """더블클릭 시 해당 업무 수정 모드"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item["values"]

        time_slot = values[0]
        task_name = values[1]
        description = values[2]

        # 입력 필드에 값 설정
        self.time_combo.set(time_slot)
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task_name)
        self.desc_text.delete("1.0", tk.END)
        self.desc_text.insert("1.0", description)

        # 버튼 텍스트 변경
        self.add_button.config(text="업무 수정")

    def add_or_update_task(self):
        """업무 추가 또는 수정"""
        time_slot = self.time_combo.get()
        task_name = self.task_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()

        if not task_name:
            messagebox.showwarning("입력 오류", "업무명을 입력해주세요.")
            return

        # 업무 추가
        success = self.manager.add_task(time_slot, task_name, description)

        if success:
            # 화면 갱신
            self.refresh_timetable()
            self.clear_inputs()
            messagebox.showinfo("성공", f"{time_slot} 업무가 저장되었습니다.")
        else:
            messagebox.showerror("오류", "업무 저장에 실패했습니다.")

    def delete_task(self):
        """업무 삭제"""
        time_slot = self.time_combo.get()

        if not self.manager.get_task(time_slot):
            messagebox.showwarning("삭제 오류", "해당 시간에 업무가 없습니다.")
            return

        # 확인 메시지
        result = messagebox.askyesno("삭제 확인", f"{time_slot}의 업무를 삭제하시겠습니까?")
        if result:
            success = self.manager.remove_task(time_slot)
            if success:
                self.refresh_timetable()
                self.clear_inputs()
                messagebox.showinfo("성공", "업무가 삭제되었습니다.")
            else:
                messagebox.showerror("오류", "업무 삭제에 실패했습니다.")

    def clear_inputs(self):
        """입력 필드 초기화"""
        self.time_combo.set("07:00")
        self.task_entry.delete(0, tk.END)
        self.desc_text.delete("1.0", tk.END)
        self.add_button.config(text="업무 추가")

    def export_to_excel(self):
        """Excel 파일로 내보내기"""
        try:
            filename = self.manager.export_to_excel()
            messagebox.showinfo("내보내기 성공", f"Excel 파일이 저장되었습니다.\n{filename}")
        except Exception as e:
            messagebox.showerror("내보내기 오류", f"오류가 발생했습니다.\n{str(e)}")

    def on_closing(self):
        """프로그램 종료 시 호출"""
        self.manager.close()
        self.root.destroy()


def main():
    """메인 함수"""
    root = tk.Tk()
    app = TimeTableGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
