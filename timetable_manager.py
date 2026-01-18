import os
from datetime import datetime, date
import pandas as pd
from typing import Dict, List, Optional
from database import Database


class TimeTableManager:
    """견우물류 업무 타임테이블 관리 클래스 (DB 연동)"""

    def __init__(self):
        self.db = Database()
        self.current_date = date.today()
        self.time_slots = self.create_time_slots()
        self.timetable = {}

        # 데이터베이스 연결 및 테이블 생성
        if self.db.connect():
            self.db.create_table()
            self.db.create_change_log_table()  # 변경 로그 테이블 생성
        else:
            raise Exception("데이터베이스 연결 실패")

    def create_time_slots(self) -> List[str]:
        """08:30 ~ 24:00까지 30분 단위 시간 슬롯 생성"""
        time_slots = []
        # 8시 30분부터 시작
        time_slots.append("08:30")
        for hour in range(9, 25):  # 9시부터 24시(자정)까지
            time_slots.append(f"{hour:02d}:00")
            if hour < 24:  # 24:30은 제외
                time_slots.append(f"{hour:02d}:30")
        return time_slots

    def set_current_date(self, work_date: date):
        """작업 날짜 설정"""
        self.current_date = work_date
        self.load_data_by_date(work_date)

    def load_data_by_date(self, work_date: date):
        """특정 날짜의 데이터 불러오기"""
        self.timetable = self.db.get_tasks_by_date(work_date)

    def add_task(self, time_slot: str, task_name: str, description: str = "", special_note: str = "", company: str = "", end_time: str = "") -> bool:
        """특정 시간대에 업무 추가 (특수상황, 업체명, 종료시간 포함)"""
        if time_slot not in self.time_slots:
            return False

        success = self.db.insert_or_update_task(
            self.current_date,
            time_slot,
            task_name,
            description,
            special_note,
            company,
            end_time
        )

        if success:
            # 메모리에도 업데이트
            self.timetable[time_slot] = {
                "task": task_name,
                "description": description,
                "special_note": special_note,
                "company": company,
                "end_time": end_time
            }
        return success

    def remove_task(self, time_slot: str) -> bool:
        """특정 시간대의 업무 삭제"""
        success = self.db.delete_task(self.current_date, time_slot)

        if success and time_slot in self.timetable:
            del self.timetable[time_slot]

        return success

    def get_task(self, time_slot: str) -> Optional[Dict]:
        """특정 시간대의 업무 조회"""
        return self.timetable.get(time_slot)

    def get_all_tasks(self) -> Dict:
        """현재 날짜의 모든 업무 조회"""
        return self.timetable

    def get_all_dates(self) -> List[date]:
        """업무가 등록된 모든 날짜 조회"""
        return self.db.get_all_dates()

    def copy_tasks_to_date(self, source_date: date, target_date: date) -> bool:
        """특정 날짜의 업무를 다른 날짜로 복사"""
        return self.db.copy_tasks_to_date(source_date, target_date)

    def export_to_excel(self, filename=None):
        """타임테이블을 Excel 파일로 내보내기 (특수상황, 업체명, 종료시간 포함)"""
        if filename is None:
            # 날짜를 포함한 파일명 생성
            date_str = self.current_date.strftime('%Y%m%d')
            filename = f'data/timetable_{date_str}.xlsx'

        data = []
        for time_slot in self.time_slots:
            task_info = self.timetable.get(time_slot, {"task": "", "description": "", "special_note": "", "company": "", "end_time": ""})
            data.append({
                "날짜": self.current_date.strftime('%Y-%m-%d'),
                "시작시간": time_slot,
                "종료시간": task_info.get("end_time", ""),
                "업체명": task_info.get("company", ""),
                "업무명": task_info.get("task", ""),
                "상세 설명": task_info.get("description", ""),
                "특수상황": task_info.get("special_note", "")
            })

        df = pd.DataFrame(data)

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        df.to_excel(filename, index=False, engine='openpyxl')
        return filename

    def get_timetable_dataframe(self) -> pd.DataFrame:
        """타임테이블을 DataFrame으로 반환"""
        data = []
        for time_slot in self.time_slots:
            task_info = self.timetable.get(time_slot, {"task": "", "description": ""})
            data.append({
                "시간": time_slot,
                "업무명": task_info.get("task", ""),
                "상세 설명": task_info.get("description", "")
            })
        return pd.DataFrame(data)

    # === 기본 업무 템플릿 관련 메서드 ===

    def get_default_tasks(self) -> Dict:
        """기본 업무 템플릿 조회"""
        return self.db.get_default_tasks()

    def add_default_task(self, time_slot: str, task_name: str, description: str = "", company: str = "", end_time: str = "", display_order: int = None, color: str = "") -> bool:
        """기본 업무 템플릿 추가 (업체명, 종료시간, 표시순서, 색상 포함)"""
        if time_slot not in self.time_slots:
            return False
        return self.db.insert_or_update_default_task(time_slot, task_name, description, company, end_time, display_order, color)

    def remove_default_task(self, display_order: int) -> bool:
        """기본 업무 템플릿 삭제 (표시순서 기준)"""
        return self.db.delete_default_task(display_order)

    def apply_default_tasks(self) -> bool:
        """현재 날짜에 기본 업무 적용"""
        success = self.db.apply_default_tasks_to_date(self.current_date)
        if success:
            # 데이터 다시 불러오기
            self.load_data_by_date(self.current_date)
        return success

    def save_special_time(self, company: str, corp_name: str, time_slot: str, is_colored: bool,
                          user_info: dict = None) -> bool:
        """특수 시간 저장 (업체명, 법인명 조합) + 로그 기록"""
        # 이전 상태 조회
        old_value = "OFF"
        special_times = self.db.get_special_times(self.current_date, company, corp_name)
        if special_times.get(time_slot, False):
            old_value = "ON"

        new_value = "ON" if is_colored else "OFF"

        # 상태가 변경된 경우에만 로그 기록
        if old_value != new_value and user_info:
            action = "색상 ON" if is_colored else "색상 OFF"
            self.db.add_change_log(
                log_type="특수시간",
                work_date=self.current_date,
                company=company,
                corp_name=corp_name,
                time_slot=time_slot,
                action=action,
                old_value=old_value,
                new_value=new_value,
                user_id=user_info.get('id'),
                username=user_info.get('username'),
                display_name=user_info.get('display_name')
            )

        return self.db.save_special_time(self.current_date, company, corp_name, time_slot, is_colored)

    def get_special_times(self, company: str, corp_name: str) -> Dict:
        """특수 시간 조회 (업체명, 법인명 조합)"""
        return self.db.get_special_times(self.current_date, company, corp_name)

    def delete_special_times(self, company: str, corp_name: str) -> bool:
        """특수 시간 삭제 (업체명, 법인명 조합)"""
        return self.db.delete_special_times_by_date(self.current_date, company, corp_name)

    def update_display_order(self, time_slot: str, display_order: int) -> bool:
        """기본 업무 템플릿의 표시 순서 업데이트"""
        return self.db.update_display_order(time_slot, display_order)

    def get_change_logs(self, start_date=None, end_date=None, log_type=None,
                        company=None, username=None, limit=500):
        """변경 로그 조회"""
        return self.db.get_change_logs(start_date, end_date, log_type, company, username, limit)

    def close(self):
        """데이터베이스 연결 종료"""
        self.db.disconnect()
