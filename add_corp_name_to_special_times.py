# -*- coding: utf-8 -*-
"""
SpecialTimes 테이블에 corp_name 컬럼 추가
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def add_corp_name_column():
    """SpecialTimes 테이블에 corp_name 컬럼 추가"""
    print("=" * 60)
    print("SpecialTimes 테이블에 corp_name 컬럼 추가")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. corp_name 컬럼이 이미 있는지 확인
    print("\n[2단계] corp_name 컬럼 존재 확인...")
    try:
        check_query = """
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'SpecialTimes' AND COLUMN_NAME = 'corp_name'
        """
        db.cursor.execute(check_query)
        result = db.cursor.fetchone()

        if result.cnt > 0:
            print("[INFO] corp_name 컬럼이 이미 존재합니다.")
        else:
            print("[INFO] corp_name 컬럼이 없습니다. 추가합니다...")

            # 3. 기존 UNIQUE 제약조건 삭제
            print("\n[3단계] 기존 UNIQUE 제약조건 확인 및 삭제...")
            constraint_query = """
            SELECT CONSTRAINT_NAME
            FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
            WHERE TABLE_NAME = 'SpecialTimes' AND CONSTRAINT_TYPE = 'UNIQUE'
            """
            db.cursor.execute(constraint_query)
            constraints = db.cursor.fetchall()

            for constraint in constraints:
                constraint_name = constraint.CONSTRAINT_NAME
                drop_query = f"ALTER TABLE SpecialTimes DROP CONSTRAINT {constraint_name}"
                db.cursor.execute(drop_query)
                print(f"[OK] UNIQUE 제약조건 '{constraint_name}' 삭제 완료!")

            db.connection.commit()

            # 4. corp_name 컬럼 추가
            print("\n[4단계] corp_name 컬럼 추가...")
            add_column_query = """
            ALTER TABLE SpecialTimes
            ADD corp_name NVARCHAR(50) NULL
            """
            db.cursor.execute(add_column_query)
            db.connection.commit()
            print("[OK] corp_name 컬럼 추가 완료!")

            # 5. 새로운 UNIQUE 제약조건 추가 (work_date, company, corp_name, time_slot)
            print("\n[5단계] 새로운 UNIQUE 제약조건 추가...")
            add_constraint_query = """
            ALTER TABLE SpecialTimes
            ADD CONSTRAINT UQ_SpecialTimes_Date_Company_Corp_Time
            UNIQUE(work_date, company, corp_name, time_slot)
            """
            db.cursor.execute(add_constraint_query)
            db.connection.commit()
            print("[OK] UNIQUE 제약조건 추가 완료!")

    except Exception as e:
        print(f"[FAIL] 작업 실패: {e}")
        db.connection.rollback()
        db.disconnect()
        return False

    # 6. 테이블 구조 확인
    print("\n[6단계] SpecialTimes 테이블 구조 확인...")
    try:
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'SpecialTimes'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query)
        columns = db.cursor.fetchall()

        print("\n[SpecialTimes 테이블 구조]")
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

    # 7. 연결 종료
    print("\n[7단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("SpecialTimes 테이블 업데이트 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        add_corp_name_column()
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
