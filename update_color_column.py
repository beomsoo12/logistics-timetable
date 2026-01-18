"""
DefaultTasks 테이블에 색상(color) 컬럼 추가
"""

import sys
sys.path.append('.')

from database import Database

def update_color_column():
    """DefaultTasks 테이블에 color 컬럼 추가"""

    print("DefaultTasks 테이블에 색상 컬럼 추가")
    print("=" * 50)

    db = Database()
    if not db.connect():
        print("[ERROR] 데이터베이스 연결 실패")
        return

    try:
        # 1. color 컬럼 존재 확인
        print("\n[1단계] color 컬럼 존재 확인...")
        check_query = """
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks' AND COLUMN_NAME = 'color'
        """
        db.cursor.execute(check_query)
        result = db.cursor.fetchone()

        if result.cnt == 0:
            # 2. color 컬럼 추가
            print("\n[2단계] color 컬럼 추가 중...")
            alter_query = """
            ALTER TABLE DefaultTasks
            ADD color NVARCHAR(20) NULL
            """
            db.cursor.execute(alter_query)
            db.connection.commit()
            print("[OK] color 컬럼 추가 완료!")
        else:
            print("[OK] color 컬럼이 이미 존재합니다.")

        # 3. 테이블 구조 확인
        print("\n[3단계] DefaultTasks 테이블 구조 확인...")
        structure_query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(structure_query)
        rows = db.cursor.fetchall()

        print("\n[DefaultTasks 테이블 구조]")
        print("-" * 60)
        print(f"{'컬럼명':<20} {'타입':<15} {'길이':<10} {'NULL허용':<10}")
        print("-" * 60)
        for row in rows:
            length = str(row.CHARACTER_MAXIMUM_LENGTH) if row.CHARACTER_MAXIMUM_LENGTH else '-'
            print(f"{row.COLUMN_NAME:<20} {row.DATA_TYPE:<15} {length:<10} {row.IS_NULLABLE:<10}")

    except Exception as e:
        print(f"[ERROR] 오류 발생: {e}")
        db.connection.rollback()
    finally:
        db.disconnect()

    print("\n" + "=" * 50)
    print("DefaultTasks 테이블 색상 컬럼 추가 완료!")

if __name__ == "__main__":
    try:
        update_color_column()
    except Exception as e:
        print(f"오류: {e}")
