# -*- coding: utf-8 -*-
"""
데이터베이스 스키마 업데이트 스크립트
- TimeTable에 special_note 컬럼 추가
- DefaultTasks 테이블 생성 (기본 업무 템플릿)
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def update_database():
    """데이터베이스 스키마 업데이트"""
    print("=" * 60)
    print("데이터베이스 스키마 업데이트")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. TimeTable에 special_note 컬럼 추가
    print("\n[2단계] TimeTable에 특수상황 컬럼 추가...")
    try:
        # 컬럼이 이미 존재하는지 확인
        check_query = """
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'TimeTable' AND COLUMN_NAME = 'special_note'
        """
        db.cursor.execute(check_query)
        result = db.cursor.fetchone()

        if result.cnt == 0:
            # 컬럼 추가
            alter_query = """
            ALTER TABLE TimeTable
            ADD special_note NVARCHAR(MAX) NULL
            """
            db.cursor.execute(alter_query)
            db.connection.commit()
            print("[OK] special_note 컬럼 추가 완료!")
        else:
            print("[INFO] special_note 컬럼이 이미 존재합니다.")

    except Exception as e:
        print(f"[FAIL] 컬럼 추가 실패: {e}")
        db.disconnect()
        return False

    # 3. DefaultTasks 테이블 생성 (기본 업무 템플릿)
    print("\n[3단계] 기본 업무 템플릿 테이블 생성...")
    try:
        create_default_tasks_query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='DefaultTasks' AND xtype='U')
        CREATE TABLE DefaultTasks (
            id INT IDENTITY(1,1) PRIMARY KEY,
            time_slot VARCHAR(10) NOT NULL UNIQUE,
            task_name NVARCHAR(200),
            description NVARCHAR(MAX),
            is_active BIT DEFAULT 1,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE()
        )
        """
        db.cursor.execute(create_default_tasks_query)
        db.connection.commit()
        print("[OK] DefaultTasks 테이블 생성 완료!")

    except Exception as e:
        print(f"[FAIL] 테이블 생성 실패: {e}")
        db.disconnect()
        return False

    # 4. 테이블 구조 확인
    print("\n[4단계] 테이블 구조 확인...")
    try:
        # TimeTable 구조
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'TimeTable'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query)
        columns = db.cursor.fetchall()

        print("\n[TimeTable 테이블 구조]")
        print("-" * 60)
        for col in columns:
            col_name = col.COLUMN_NAME
            data_type = col.DATA_TYPE
            max_length = col.CHARACTER_MAXIMUM_LENGTH if col.CHARACTER_MAXIMUM_LENGTH else '-'
            print(f"  {col_name:<20} {data_type:<15} {str(max_length)}")
        print("-" * 60)

        # DefaultTasks 구조
        query2 = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query2)
        columns2 = db.cursor.fetchall()

        print("\n[DefaultTasks 테이블 구조]")
        print("-" * 60)
        for col in columns2:
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
    print("데이터베이스 스키마 업데이트 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        update_database()
    except Exception as e:
        print(f"\n오류 발생: {e}")
