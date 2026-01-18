# -*- coding: utf-8 -*-
"""
SpecialTimes 테이블 생성 스크립트
특수 업무 시간 정보를 저장하는 테이블
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def create_special_times_table():
    """SpecialTimes 테이블 생성"""
    print("=" * 60)
    print("SpecialTimes 테이블 생성")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. SpecialTimes 테이블 생성
    print("\n[2단계] SpecialTimes 테이블 생성 중...")
    try:
        create_table_query = """
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SpecialTimes' AND xtype='U')
        CREATE TABLE SpecialTimes (
            id INT IDENTITY(1,1) PRIMARY KEY,
            work_date DATE NOT NULL,
            company NVARCHAR(50) NOT NULL,
            time_slot VARCHAR(10) NOT NULL,
            is_colored BIT DEFAULT 0,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT UQ_SpecialTimes_Date_Company_Time UNIQUE(work_date, company, time_slot)
        )
        """
        db.cursor.execute(create_table_query)
        db.connection.commit()
        print("[OK] SpecialTimes 테이블 생성 완료!")
    except Exception as e:
        print(f"[FAIL] 테이블 생성 실패: {e}")
        db.disconnect()
        return False

    # 3. 테이블 구조 확인
    print("\n[3단계] SpecialTimes 테이블 구조 확인...")
    try:
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'SpecialTimes'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query)
        columns = db.cursor.fetchall()

        print("\n[SpecialTimes 테이블 구조]")
        print("-" * 60)
        for col in columns:
            col_name = col.COLUMN_NAME
            data_type = col.DATA_TYPE
            max_length = col.CHARACTER_MAXIMUM_LENGTH if col.CHARACTER_MAXIMUM_LENGTH else '-'
            print(f"  {col_name:<20} {data_type:<15} {str(max_length)}")
        print("-" * 60)
    except Exception as e:
        print(f"[FAIL] 테이블 확인 중 오류: {e}")

    # 4. 연결 종료
    print("\n[4단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("SpecialTimes 테이블 생성 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        create_special_times_table()
    except Exception as e:
        print(f"\n오류 발생: {e}")
