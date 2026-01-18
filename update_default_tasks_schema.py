# -*- coding: utf-8 -*-
"""
DefaultTasks 테이블 스키마 업데이트
- company (업체명) 컬럼 추가
- end_time (종료시간) 컬럼 추가
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def update_default_tasks_schema():
    """DefaultTasks 테이블 스키마 업데이트"""
    print("=" * 60)
    print("DefaultTasks 테이블 스키마 업데이트")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. company 컬럼 추가
    print("\n[2단계] DefaultTasks에 업체명(company) 컬럼 추가...")
    try:
        check_query = """
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks' AND COLUMN_NAME = 'company'
        """
        db.cursor.execute(check_query)
        result = db.cursor.fetchone()

        if result.cnt == 0:
            alter_query = """
            ALTER TABLE DefaultTasks
            ADD company NVARCHAR(50) NULL
            """
            db.cursor.execute(alter_query)
            db.connection.commit()
            print("[OK] company 컬럼 추가 완료!")
        else:
            print("[INFO] company 컬럼이 이미 존재합니다.")
    except Exception as e:
        print(f"[FAIL] company 컬럼 추가 실패: {e}")
        db.disconnect()
        return False

    # 3. end_time 컬럼 추가
    print("\n[3단계] DefaultTasks에 종료시간(end_time) 컬럼 추가...")
    try:
        check_query = """
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks' AND COLUMN_NAME = 'end_time'
        """
        db.cursor.execute(check_query)
        result = db.cursor.fetchone()

        if result.cnt == 0:
            alter_query = """
            ALTER TABLE DefaultTasks
            ADD end_time VARCHAR(10) NULL
            """
            db.cursor.execute(alter_query)
            db.connection.commit()
            print("[OK] end_time 컬럼 추가 완료!")
        else:
            print("[INFO] end_time 컬럼이 이미 존재합니다.")
    except Exception as e:
        print(f"[FAIL] end_time 컬럼 추가 실패: {e}")
        db.disconnect()
        return False

    # 4. 테이블 구조 확인
    print("\n[4단계] DefaultTasks 테이블 구조 확인...")
    try:
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query)
        columns = db.cursor.fetchall()

        print("\n[DefaultTasks 테이블 구조]")
        print("-" * 60)
        for col in columns:
            col_name = col.COLUMN_NAME
            data_type = col.DATA_TYPE
            max_length = col.CHARACTER_MAXIMUM_LENGTH if col.CHARACTER_MAXIMUM_LENGTH else '-'
            print(f"  {col_name:<20} {data_type:<15} {str(max_length)}")
        print("-" * 60)
    except Exception as e:
        print(f"[FAIL] 테이블 확인 중 오류: {e}")

    # 5. 연결 종료
    print("\n[5단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("DefaultTasks 테이블 스키마 업데이트 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        update_default_tasks_schema()
    except Exception as e:
        print(f"\n오류 발생: {e}")
