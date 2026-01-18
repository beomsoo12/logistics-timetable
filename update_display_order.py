# -*- coding: utf-8 -*-
"""
DefaultTasks 테이블에 표시 순서(display_order) 컬럼 추가
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def update_display_order_column():
    """DefaultTasks 테이블에 display_order 컬럼 추가"""
    print("=" * 60)
    print("DefaultTasks 테이블에 표시 순서 컬럼 추가")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. display_order 컬럼 추가
    print("\n[2단계] DefaultTasks에 표시순서(display_order) 컬럼 추가...")
    try:
        check_query = """
        SELECT COUNT(*) as cnt
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'DefaultTasks' AND COLUMN_NAME = 'display_order'
        """
        db.cursor.execute(check_query)
        result = db.cursor.fetchone()

        if result.cnt == 0:
            alter_query = """
            ALTER TABLE DefaultTasks
            ADD display_order INT NULL
            """
            db.cursor.execute(alter_query)
            db.connection.commit()
            print("[OK] display_order 컬럼 추가 완료!")

            # 기존 데이터에 기본 순서 설정 (업체명 알파벳 순서)
            print("\n[3단계] 기존 데이터에 기본 순서 설정 중...")
            update_query = """
            WITH OrderedTasks AS (
                SELECT
                    time_slot,
                    ROW_NUMBER() OVER (ORDER BY
                        CASE company
                            WHEN '롯데마트' THEN 1
                            WHEN '롯데슈퍼' THEN 2
                            WHEN '지에스' THEN 3
                            WHEN '이마트' THEN 4
                            WHEN '홈플러스' THEN 5
                            WHEN '코스트코' THEN 6
                            ELSE 99
                        END,
                        time_slot
                    ) as row_num
                FROM DefaultTasks
            )
            UPDATE DefaultTasks
            SET display_order = (SELECT row_num FROM OrderedTasks WHERE OrderedTasks.time_slot = DefaultTasks.time_slot)
            """
            db.cursor.execute(update_query)
            db.connection.commit()
            print("[OK] 기본 순서 설정 완료!")
        else:
            print("[INFO] display_order 컬럼이 이미 존재합니다.")
    except Exception as e:
        print(f"[FAIL] display_order 컬럼 추가 실패: {e}")
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
    print("DefaultTasks 테이블 업데이트 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        update_display_order_column()
    except Exception as e:
        print(f"\n오류 발생: {e}")
