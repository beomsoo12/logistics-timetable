import pyodbc
from db_config import DB_CONFIG


class Database:
    """MSSQL 데이터베이스 연결 및 관리 클래스"""

    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        """데이터베이스 연결"""
        try:
            # 연결 문자열 생성
            if 'username' in DB_CONFIG:
                # SQL Server 인증
                conn_str = (
                    f"DRIVER={DB_CONFIG['driver']};"
                    f"SERVER={DB_CONFIG['server']};"
                    f"DATABASE={DB_CONFIG['database']};"
                    f"UID={DB_CONFIG['username']};"
                    f"PWD={DB_CONFIG['password']};"
                    f"TrustServerCertificate=yes;"  # ODBC Driver 18에서 SSL 인증서 검증 비활성화
                    f"Encrypt=no;"  # 암호화 비활성화 (선택사항)
                )
            else:
                # Windows 인증
                conn_str = (
                    f"DRIVER={DB_CONFIG['driver']};"
                    f"SERVER={DB_CONFIG['server']};"
                    f"DATABASE={DB_CONFIG['database']};"
                    f"Trusted_Connection=yes;"
                    f"TrustServerCertificate=yes;"
                    f"Encrypt=no;"
                )

            self.connection = pyodbc.connect(conn_str)
            self.cursor = self.connection.cursor()
            return True
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            return False

    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def create_table(self):
        """타임테이블 테이블 생성"""
        try:
            create_table_query = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TimeTable' AND xtype='U')
            CREATE TABLE TimeTable (
                id INT IDENTITY(1,1) PRIMARY KEY,
                work_date DATE NOT NULL,
                time_slot VARCHAR(10) NOT NULL,
                task_name NVARCHAR(200),
                description NVARCHAR(MAX),
                created_at DATETIME DEFAULT GETDATE(),
                updated_at DATETIME DEFAULT GETDATE(),
                CONSTRAINT UQ_TimeTable_Date_Time UNIQUE(work_date, time_slot)
            )
            """
            self.cursor.execute(create_table_query)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"테이블 생성 오류: {e}")
            return False

    def insert_or_update_task(self, work_date, time_slot, task_name, description, special_note='', company='', end_time=''):
        """업무 추가 또는 수정 (특수상황, 업체명, 종료시간 포함)"""
        try:
            # MERGE 문을 사용하여 INSERT 또는 UPDATE
            query = """
            MERGE TimeTable AS target
            USING (SELECT ? AS work_date, ? AS time_slot) AS source
            ON (target.work_date = source.work_date AND target.time_slot = source.time_slot)
            WHEN MATCHED THEN
                UPDATE SET task_name = ?, description = ?, special_note = ?, company = ?, end_time = ?, updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (work_date, time_slot, task_name, description, special_note, company, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """
            self.cursor.execute(query, (
                work_date, time_slot,
                task_name, description, special_note, company, end_time,
                work_date, time_slot, task_name, description, special_note, company, end_time
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"업무 저장 오류: {e}")
            self.connection.rollback()
            return False

    def delete_task(self, work_date, time_slot):
        """업무 삭제"""
        try:
            query = """
            DELETE FROM TimeTable
            WHERE work_date = ? AND time_slot = ?
            """
            self.cursor.execute(query, (work_date, time_slot))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"업무 삭제 오류: {e}")
            self.connection.rollback()
            return False

    def get_tasks_by_date(self, work_date):
        """특정 날짜의 모든 업무 조회 (특수상황, 업체명, 종료시간 포함)"""
        try:
            query = """
            SELECT time_slot, task_name, description, special_note, company, end_time
            FROM TimeTable
            WHERE work_date = ?
            ORDER BY time_slot
            """
            self.cursor.execute(query, (work_date,))
            rows = self.cursor.fetchall()

            # 딕셔너리 형태로 변환
            tasks = {}
            for row in rows:
                tasks[row.time_slot] = {
                    'task': row.task_name,
                    'description': row.description if row.description else '',
                    'special_note': row.special_note if row.special_note else '',
                    'company': row.company if row.company else '',
                    'end_time': row.end_time if row.end_time else ''
                }
            return tasks
        except Exception as e:
            print(f"업무 조회 오류: {e}")
            return {}

    def get_task(self, work_date, time_slot):
        """특정 날짜의 특정 시간 업무 조회 (특수상황, 업체명, 종료시간 포함)"""
        try:
            query = """
            SELECT task_name, description, special_note, company, end_time
            FROM TimeTable
            WHERE work_date = ? AND time_slot = ?
            """
            self.cursor.execute(query, (work_date, time_slot))
            row = self.cursor.fetchone()

            if row:
                return {
                    'task': row.task_name,
                    'description': row.description if row.description else '',
                    'special_note': row.special_note if row.special_note else '',
                    'company': row.company if row.company else '',
                    'end_time': row.end_time if row.end_time else ''
                }
            return None
        except Exception as e:
            print(f"업무 조회 오류: {e}")
            return None

    def get_all_dates(self):
        """업무가 등록된 모든 날짜 조회"""
        try:
            query = """
            SELECT DISTINCT work_date
            FROM TimeTable
            ORDER BY work_date DESC
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            return [row.work_date for row in rows]
        except Exception as e:
            print(f"날짜 조회 오류: {e}")
            return []

    def copy_tasks_to_date(self, source_date, target_date):
        """특정 날짜의 업무를 다른 날짜로 복사"""
        try:
            query = """
            INSERT INTO TimeTable (work_date, time_slot, task_name, description)
            SELECT ?, time_slot, task_name, description
            FROM TimeTable
            WHERE work_date = ?
            AND NOT EXISTS (
                SELECT 1 FROM TimeTable t2
                WHERE t2.work_date = ? AND t2.time_slot = TimeTable.time_slot
            )
            """
            self.cursor.execute(query, (target_date, source_date, target_date))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"업무 복사 오류: {e}")
            self.connection.rollback()
            return False

    # === 기본 업무 템플릿 관련 메서드 ===

    def get_default_tasks(self):
        """기본 업무 템플릿 전체 조회 (업체명, 종료시간, 표시순서 포함)"""
        try:
            query = """
            SELECT time_slot, task_name, description, is_active, company, end_time, display_order
            FROM DefaultTasks
            WHERE is_active = 1
            ORDER BY display_order, time_slot
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            tasks = {}
            for row in rows:
                # display_order를 키로 사용 (고유값)
                display_order = row.display_order if row.display_order else 999
                tasks[display_order] = {
                    'time_slot': row.time_slot,
                    'task': row.task_name,
                    'description': row.description if row.description else '',
                    'company': row.company if row.company else '',
                    'end_time': row.end_time if row.end_time else '',
                    'display_order': display_order
                }
            return tasks
        except Exception as e:
            print(f"기본 업무 조회 오류: {e}")
            return {}

    def insert_or_update_default_task(self, time_slot, task_name, description, company='', end_time='', display_order=None):
        """기본 업무 템플릿 추가 또는 수정 (업체명, 종료시간, 표시순서 포함)"""
        try:
            # display_order가 지정되지 않은 경우 현재 최대값 + 1
            if display_order is None:
                max_query = "SELECT ISNULL(MAX(display_order), 0) + 1 as next_order FROM DefaultTasks"
                self.cursor.execute(max_query)
                result = self.cursor.fetchone()
                display_order = result.next_order

            query = """
            MERGE DefaultTasks AS target
            USING (SELECT ? AS display_order) AS source
            ON (target.display_order = source.display_order)
            WHEN MATCHED THEN
                UPDATE SET time_slot = ?, task_name = ?, description = ?, company = ?, end_time = ?, is_active = 1, updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (display_order, time_slot, task_name, description, company, end_time, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1);
            """
            self.cursor.execute(query, (
                display_order,
                time_slot, task_name, description, company, end_time,
                display_order, time_slot, task_name, description, company, end_time
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"기본 업무 저장 오류: {e}")
            self.connection.rollback()
            return False

    def delete_default_task(self, display_order):
        """기본 업무 템플릿 삭제 (표시순서 기준)"""
        try:
            query = """
            DELETE FROM DefaultTasks
            WHERE display_order = ?
            """
            self.cursor.execute(query, (display_order,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"기본 업무 삭제 오류: {e}")
            self.connection.rollback()
            return False

    def apply_default_tasks_to_date(self, target_date):
        """기본 업무 템플릿을 특정 날짜에 적용 (업체명, 종료시간 포함)"""
        try:
            query = """
            INSERT INTO TimeTable (work_date, time_slot, task_name, description, company, end_time)
            SELECT ?, time_slot, task_name, description, company, end_time
            FROM DefaultTasks
            WHERE is_active = 1
            AND NOT EXISTS (
                SELECT 1 FROM TimeTable t
                WHERE t.work_date = ? AND t.time_slot = DefaultTasks.time_slot
            )
            """
            self.cursor.execute(query, (target_date, target_date))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"기본 업무 적용 오류: {e}")
            self.connection.rollback()
            return False

    def update_display_order(self, time_slot, display_order):
        """기본 업무 템플릿의 표시 순서 업데이트"""
        try:
            query = """
            UPDATE DefaultTasks
            SET display_order = ?, updated_at = GETDATE()
            WHERE time_slot = ?
            """
            self.cursor.execute(query, (display_order, time_slot))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"표시 순서 업데이트 오류: {e}")
            self.connection.rollback()
            return False

    # === 특수 시간 관련 메서드 ===

    def save_special_time(self, work_date, company, corp_name, time_slot, is_colored):
        """특수 시간 저장 또는 업데이트 (업체명, 법인명 조합)"""
        try:
            query = """
            MERGE SpecialTimes AS target
            USING (SELECT ? AS work_date, ? AS company, ? AS corp_name, ? AS time_slot) AS source
            ON (target.work_date = source.work_date AND target.company = source.company
                AND target.corp_name = source.corp_name AND target.time_slot = source.time_slot)
            WHEN MATCHED THEN
                UPDATE SET is_colored = ?, updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (work_date, company, corp_name, time_slot, is_colored)
                VALUES (?, ?, ?, ?, ?);
            """
            self.cursor.execute(query, (
                work_date, company, corp_name, time_slot,
                is_colored,
                work_date, company, corp_name, time_slot, is_colored
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"특수 시간 저장 오류: {e}")
            self.connection.rollback()
            return False

    def get_special_times(self, work_date, company, corp_name):
        """특정 날짜의 특정 업체+법인명 특수 시간 조회"""
        try:
            query = """
            SELECT time_slot, is_colored
            FROM SpecialTimes
            WHERE work_date = ? AND company = ? AND corp_name = ?
            ORDER BY time_slot
            """
            self.cursor.execute(query, (work_date, company, corp_name))
            rows = self.cursor.fetchall()

            special_times = {}
            for row in rows:
                if row.is_colored:
                    special_times[row.time_slot] = True
            return special_times
        except Exception as e:
            print(f"특수 시간 조회 오류: {e}")
            return {}

    def delete_special_times_by_date(self, work_date, company, corp_name):
        """특정 날짜의 특정 업체+법인명 특수 시간 삭제"""
        try:
            query = """
            DELETE FROM SpecialTimes
            WHERE work_date = ? AND company = ? AND corp_name = ?
            """
            self.cursor.execute(query, (work_date, company, corp_name))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"특수 시간 삭제 오류: {e}")
            self.connection.rollback()
            return False
