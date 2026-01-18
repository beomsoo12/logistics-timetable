import pyodbc

# 암호화된 설정 우선 사용
try:
    from db_crypto import get_db_config
    DB_CONFIG = get_db_config()
    if DB_CONFIG is None:
        from db_config import DB_CONFIG
except ImportError:
    from db_config import DB_CONFIG


class Database:
    """MSSQL 데이터베이스 연결 및 관리 클래스"""

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.db_config = DB_CONFIG

    def connect(self):
        """데이터베이스 연결"""
        try:
            # 연결 문자열 생성
            if 'username' in self.db_config:
                # SQL Server 인증
                conn_str = (
                    f"DRIVER={self.db_config['driver']};"
                    f"SERVER={self.db_config['server']};"
                    f"DATABASE={self.db_config['database']};"
                    f"UID={self.db_config['username']};"
                    f"PWD={self.db_config['password']};"
                    f"TrustServerCertificate=yes;"  # ODBC Driver 18에서 SSL 인증서 검증 비활성화
                    f"Encrypt=no;"  # 암호화 비활성화 (선택사항)
                )
            else:
                # Windows 인증
                conn_str = (
                    f"DRIVER={self.db_config['driver']};"
                    f"SERVER={self.db_config['server']};"
                    f"DATABASE={self.db_config['database']};"
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

    # === 사용자 인증 관련 메서드 ===

    def create_users_table(self):
        """사용자 테이블 생성"""
        try:
            create_table_query = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
            CREATE TABLE Users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username NVARCHAR(50) NOT NULL UNIQUE,
                password NVARCHAR(255) NOT NULL,
                display_name NVARCHAR(100),
                is_active BIT DEFAULT 1,
                is_admin BIT DEFAULT 0,
                created_at DATETIME DEFAULT GETDATE(),
                last_login DATETIME,
                CONSTRAINT UQ_Users_Username UNIQUE(username)
            )
            """
            self.cursor.execute(create_table_query)
            self.connection.commit()

            # 기본 관리자 계정이 없으면 생성
            self.create_default_admin()
            return True
        except Exception as e:
            print(f"사용자 테이블 생성 오류: {e}")
            return False

    def create_default_admin(self):
        """기본 관리자 계정 생성"""
        try:
            # 관리자 계정이 있는지 확인
            check_query = "SELECT COUNT(*) as cnt FROM Users WHERE username = 'admin'"
            self.cursor.execute(check_query)
            result = self.cursor.fetchone()

            if result.cnt == 0:
                # 기본 관리자 계정 생성 (비밀번호: admin123)
                import hashlib
                password_hash = hashlib.sha256('admin123'.encode()).hexdigest()

                insert_query = """
                INSERT INTO Users (username, password, display_name, is_active, is_admin)
                VALUES ('admin', ?, N'관리자', 1, 1)
                """
                self.cursor.execute(insert_query, (password_hash,))
                self.connection.commit()
                print("기본 관리자 계정이 생성되었습니다. (ID: admin, PW: admin123)")
            return True
        except Exception as e:
            print(f"기본 관리자 계정 생성 오류: {e}")
            return False

    def authenticate_user(self, username, password):
        """사용자 인증"""
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query = """
            SELECT id, username, display_name, is_admin
            FROM Users
            WHERE username = ? AND password = ? AND is_active = 1
            """
            self.cursor.execute(query, (username, password_hash))
            row = self.cursor.fetchone()

            if row:
                # 마지막 로그인 시간 업데이트
                update_query = "UPDATE Users SET last_login = GETDATE() WHERE id = ?"
                self.cursor.execute(update_query, (row.id,))
                self.connection.commit()

                return {
                    'id': row.id,
                    'username': row.username,
                    'display_name': row.display_name if row.display_name else row.username,
                    'is_admin': row.is_admin
                }
            return None
        except Exception as e:
            print(f"사용자 인증 오류: {e}")
            return None

    def get_user_by_username(self, username):
        """사용자명으로 사용자 정보 조회 (자동 로그인용 - 비밀번호 확인 없음)"""
        try:
            query = """
            SELECT id, username, display_name, is_admin
            FROM Users
            WHERE username = ? AND is_active = 1
            """
            self.cursor.execute(query, (username,))
            row = self.cursor.fetchone()

            if row:
                # 마지막 로그인 시간 업데이트
                update_query = "UPDATE Users SET last_login = GETDATE() WHERE id = ?"
                self.cursor.execute(update_query, (row.id,))
                self.connection.commit()

                return {
                    'id': row.id,
                    'username': row.username,
                    'display_name': row.display_name if row.display_name else row.username,
                    'is_admin': row.is_admin
                }
            return None
        except Exception as e:
            print(f"사용자 조회 오류: {e}")
            return None

    def get_all_users(self):
        """모든 사용자 조회"""
        try:
            query = """
            SELECT id, username, display_name, is_active, is_admin, created_at, last_login
            FROM Users
            ORDER BY username
            """
            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            users = []
            for row in rows:
                users.append({
                    'id': row.id,
                    'username': row.username,
                    'display_name': row.display_name if row.display_name else '',
                    'is_active': row.is_active,
                    'is_admin': row.is_admin,
                    'created_at': row.created_at,
                    'last_login': row.last_login
                })
            return users
        except Exception as e:
            print(f"사용자 조회 오류: {e}")
            return []

    def add_user(self, username, password, display_name='', is_admin=False):
        """사용자 추가"""
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query = """
            INSERT INTO Users (username, password, display_name, is_active, is_admin)
            VALUES (?, ?, ?, 1, ?)
            """
            self.cursor.execute(query, (username, password_hash, display_name, 1 if is_admin else 0))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"사용자 추가 오류: {e}")
            self.connection.rollback()
            return False

    def update_user(self, user_id, display_name=None, is_active=None, is_admin=None):
        """사용자 정보 수정"""
        try:
            updates = []
            params = []

            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)
            if is_admin is not None:
                updates.append("is_admin = ?")
                params.append(1 if is_admin else 0)

            if not updates:
                return True

            params.append(user_id)
            query = f"UPDATE Users SET {', '.join(updates)} WHERE id = ?"
            self.cursor.execute(query, params)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"사용자 수정 오류: {e}")
            self.connection.rollback()
            return False

    def change_password(self, user_id, new_password):
        """비밀번호 변경"""
        try:
            import hashlib
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()

            query = "UPDATE Users SET password = ? WHERE id = ?"
            self.cursor.execute(query, (password_hash, user_id))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"비밀번호 변경 오류: {e}")
            self.connection.rollback()
            return False

    def delete_user(self, user_id):
        """사용자 삭제"""
        try:
            query = "DELETE FROM Users WHERE id = ? AND username != 'admin'"
            self.cursor.execute(query, (user_id,))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"사용자 삭제 오류: {e}")
            self.connection.rollback()
            return False

    # === 변경 로그 관련 메서드 ===

    def create_change_log_table(self):
        """변경 로그 테이블 생성"""
        try:
            create_table_query = """
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ChangeLogs' AND xtype='U')
            CREATE TABLE ChangeLogs (
                id INT IDENTITY(1,1) PRIMARY KEY,
                log_type NVARCHAR(50) NOT NULL,
                work_date DATE,
                company NVARCHAR(100),
                corp_name NVARCHAR(100),
                time_slot VARCHAR(10),
                action NVARCHAR(50),
                old_value NVARCHAR(MAX),
                new_value NVARCHAR(MAX),
                user_id INT,
                username NVARCHAR(50),
                display_name NVARCHAR(100),
                created_at DATETIME DEFAULT GETDATE(),
                ip_address NVARCHAR(50)
            )
            """
            self.cursor.execute(create_table_query)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"변경 로그 테이블 생성 오류: {e}")
            return False

    def add_change_log(self, log_type, work_date, company, corp_name, time_slot, action,
                       old_value, new_value, user_id, username, display_name):
        """변경 로그 추가"""
        try:
            query = """
            INSERT INTO ChangeLogs (log_type, work_date, company, corp_name, time_slot,
                                   action, old_value, new_value, user_id, username, display_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                log_type, work_date, company, corp_name, time_slot,
                action, old_value, new_value, user_id, username, display_name
            ))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"변경 로그 추가 오류: {e}")
            self.connection.rollback()
            return False

    def get_change_logs(self, start_date=None, end_date=None, log_type=None,
                        company=None, username=None, limit=500):
        """변경 로그 조회"""
        try:
            conditions = []
            params = []

            # created_at 기준으로 날짜 필터 (로그 생성 시간)
            if start_date:
                conditions.append("CAST(created_at AS DATE) >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("CAST(created_at AS DATE) <= ?")
                params.append(end_date)
            if log_type:
                conditions.append("log_type = ?")
                params.append(log_type)
            if company:
                conditions.append("company = ?")
                params.append(company)
            if username:
                conditions.append("username LIKE ?")
                params.append(f"%{username}%")

            where_clause = ""
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
            SELECT TOP {limit} id, log_type, work_date, company, corp_name, time_slot,
                   action, old_value, new_value, user_id, username, display_name, created_at
            FROM ChangeLogs
            {where_clause}
            ORDER BY created_at DESC
            """
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            logs = []
            for row in rows:
                logs.append({
                    'id': row.id,
                    'log_type': row.log_type,
                    'work_date': row.work_date,
                    'company': row.company if row.company else '',
                    'corp_name': row.corp_name if row.corp_name else '',
                    'time_slot': row.time_slot if row.time_slot else '',
                    'action': row.action,
                    'old_value': row.old_value if row.old_value else '',
                    'new_value': row.new_value if row.new_value else '',
                    'user_id': row.user_id,
                    'username': row.username,
                    'display_name': row.display_name if row.display_name else row.username,
                    'created_at': row.created_at
                })
            return logs
        except Exception as e:
            print(f"변경 로그 조회 오류: {e}")
            return []

    def get_logs_by_date_range(self, start_date, end_date, limit=1000):
        """날짜 범위로 로그 조회"""
        return self.get_change_logs(start_date=start_date, end_date=end_date, limit=limit)

    def get_logs_by_user(self, username, limit=500):
        """사용자별 로그 조회"""
        return self.get_change_logs(username=username, limit=limit)

    def delete_old_logs(self, days_to_keep=90):
        """오래된 로그 삭제"""
        try:
            query = f"""
            DELETE FROM ChangeLogs
            WHERE created_at < DATEADD(day, -{days_to_keep}, GETDATE())
            """
            self.cursor.execute(query)
            deleted_count = self.cursor.rowcount
            self.connection.commit()
            return deleted_count
        except Exception as e:
            print(f"로그 삭제 오류: {e}")
            self.connection.rollback()
            return 0
