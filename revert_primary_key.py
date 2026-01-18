# -*- coding: utf-8 -*-
"""
DefaultTasks 테이블의 PRIMARY KEY 되돌리기
display_order UNIQUE 제약조건 제거
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def revert_primary_key():
    """DefaultTasks 테이블의 UNIQUE 제약조건 제거"""
    print("=" * 60)
    print("DefaultTasks 테이블 UNIQUE 제약조건 제거")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. display_order UNIQUE 제약조건 제거
    print("\n[2단계] display_order UNIQUE 제약조건 제거...")
    try:
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
            print(f"[OK] UNIQUE 제약조건 '{constraint_name}' 제거 완료!")

        db.connection.commit()
    except Exception as e:
        print(f"[FAIL] UNIQUE 제약조건 제거 실패: {e}")
        db.disconnect()
        return False

    # 3. display_order를 NULL 허용으로 변경
    print("\n[3단계] display_order를 NULL 허용으로 변경...")
    try:
        alter_query = """
        ALTER TABLE DefaultTasks
        ALTER COLUMN display_order INT NULL
        """
        db.cursor.execute(alter_query)
        db.connection.commit()
        print("[OK] display_order를 NULL 허용으로 변경 완료!")
    except Exception as e:
        print(f"[WARN] NULL 허용 변경 중 오류: {e}")

    # 4. 테이블 구조 확인
    print("\n[4단계] DefaultTasks 테이블 구조 확인...")
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

    # 5. 제약조건 확인
    print("\n[5단계] 제약조건 확인...")
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

    # 6. 연결 종료
    print("\n[6단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("DefaultTasks 테이블 UNIQUE 제약조건 제거 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        revert_primary_key()
    except Exception as e:
        print(f"\n오류 발생: {e}")
