# -*- coding: utf-8 -*-
"""
DefaultTasks 테이블의 PRIMARY KEY 변경
time_slot -> display_order로 변경하고 UNIQUE 제약조건 추가
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def update_primary_key():
    """DefaultTasks 테이블의 PRIMARY KEY 변경"""
    print("=" * 60)
    print("DefaultTasks 테이블 PRIMARY KEY 변경")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. 기존 UNIQUE 제약조건 확인 및 삭제
    print("\n[2단계] 기존 UNIQUE 제약조건 확인 및 삭제...")
    try:
        # UNIQUE 제약조건 찾기
        check_query = """
        SELECT CONSTRAINT_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_NAME = 'DefaultTasks' AND CONSTRAINT_TYPE = 'UNIQUE'
        """
        db.cursor.execute(check_query)
        constraints = db.cursor.fetchall()

        for constraint in constraints:
            constraint_name = constraint.CONSTRAINT_NAME
            drop_query = f"ALTER TABLE DefaultTasks DROP CONSTRAINT {constraint_name}"
            db.cursor.execute(drop_query)
            print(f"[OK] UNIQUE 제약조건 '{constraint_name}' 삭제 완료!")

        db.connection.commit()
    except Exception as e:
        print(f"[WARN] UNIQUE 제약조건 삭제 중 오류: {e}")

    # 3. display_order가 NULL인 경우 자동 설정
    print("\n[3단계] display_order NULL 값 자동 설정...")
    try:
        update_query = """
        UPDATE DefaultTasks
        SET display_order = (
            SELECT ROW_NUMBER() OVER (ORDER BY time_slot)
            FROM (SELECT 1 AS dummy) AS dummy_table
        )
        WHERE display_order IS NULL
        """
        db.cursor.execute(update_query)
        db.connection.commit()
        print("[OK] NULL 값 자동 설정 완료!")
    except Exception as e:
        print(f"[WARN] NULL 값 설정 중 오류: {e}")

    # 4. display_order를 NOT NULL로 변경
    print("\n[4단계] display_order를 NOT NULL로 변경...")
    try:
        alter_query = """
        ALTER TABLE DefaultTasks
        ALTER COLUMN display_order INT NOT NULL
        """
        db.cursor.execute(alter_query)
        db.connection.commit()
        print("[OK] display_order를 NOT NULL로 변경 완료!")
    except Exception as e:
        print(f"[FAIL] display_order NOT NULL 변경 실패: {e}")
        db.disconnect()
        return False

    # 5. display_order에 UNIQUE 제약조건 추가
    print("\n[5단계] display_order에 UNIQUE 제약조건 추가...")
    try:
        unique_query = """
        ALTER TABLE DefaultTasks
        ADD CONSTRAINT UQ_DefaultTasks_DisplayOrder UNIQUE (display_order)
        """
        db.cursor.execute(unique_query)
        db.connection.commit()
        print("[OK] UNIQUE 제약조건 추가 완료!")
    except Exception as e:
        print(f"[FAIL] UNIQUE 제약조건 추가 실패: {e}")
        db.disconnect()
        return False

    # 6. 테이블 구조 확인
    print("\n[6단계] DefaultTasks 테이블 구조 확인...")
    try:
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query)
        columns = db.cursor.fetchall()

        print("\n[DefaultTasks 테이블 구조]")
        print("-" * 70)
        print(f"{'컬럼명':<20} {'타입':<15} {'길이':<10} {'NULL 허용'}")
        print("-" * 70)
        for col in columns:
            col_name = col.COLUMN_NAME
            data_type = col.DATA_TYPE
            max_length = col.CHARACTER_MAXIMUM_LENGTH if col.CHARACTER_MAXIMUM_LENGTH else '-'
            nullable = col.IS_NULLABLE
            print(f"{col_name:<20} {data_type:<15} {str(max_length):<10} {nullable}")
        print("-" * 70)
    except Exception as e:
        print(f"[FAIL] 테이블 확인 중 오류: {e}")

    # 7. 제약조건 확인
    print("\n[7단계] 제약조건 확인...")
    try:
        query = """
        SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_NAME = 'DefaultTasks'
        """
        db.cursor.execute(query)
        constraints = db.cursor.fetchall()

        print("\n[DefaultTasks 제약조건]")
        print("-" * 50)
        for constraint in constraints:
            print(f"  {constraint.CONSTRAINT_NAME}: {constraint.CONSTRAINT_TYPE}")
        print("-" * 50)
    except Exception as e:
        print(f"[FAIL] 제약조건 확인 중 오류: {e}")

    # 8. 연결 종료
    print("\n[8단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("DefaultTasks 테이블 PRIMARY KEY 변경 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        update_primary_key()
    except Exception as e:
        print(f"\n오류 발생: {e}")
