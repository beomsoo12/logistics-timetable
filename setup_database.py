# -*- coding: utf-8 -*-
"""
데이터베이스 연결 테스트 및 테이블 생성 스크립트
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def setup_database():
    """데이터베이스 연결 및 테이블 생성"""
    print("=" * 60)
    print("견우물류 타임테이블 데이터베이스 설정")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        print("\ndb_config.py 파일의 설정을 확인해주세요:")
        print("  - server: SQL Server 주소")
        print("  - database: 데이터베이스 이름")
        print("  - username: 사용자명")
        print("  - password: 비밀번호")
        return False

    # 2. 테이블 생성
    print("\n[2단계] TimeTable 테이블 생성 중...")
    if db.create_table():
        print("[OK] 테이블 생성 성공!")
    else:
        print("[FAIL] 테이블 생성 실패!")
        db.disconnect()
        return False

    # 3. 테이블 확인
    print("\n[3단계] 테이블 구조 확인 중...")
    try:
        query = """
        SELECT
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'TimeTable'
        ORDER BY ORDINAL_POSITION
        """
        db.cursor.execute(query)
        columns = db.cursor.fetchall()

        print("\n[OK] TimeTable 테이블 구조:")
        print("-" * 60)
        print(f"{'컬럼명':<20} {'데이터타입':<15} {'길이':<10} {'NULL허용'}")
        print("-" * 60)
        for col in columns:
            col_name = col.COLUMN_NAME
            data_type = col.DATA_TYPE
            max_length = col.CHARACTER_MAXIMUM_LENGTH if col.CHARACTER_MAXIMUM_LENGTH else '-'
            nullable = col.IS_NULLABLE
            print(f"{col_name:<20} {data_type:<15} {str(max_length):<10} {nullable}")
        print("-" * 60)

    except Exception as e:
        print(f"[FAIL] 테이블 확인 중 오류: {e}")

    # 4. 연결 종료
    print("\n[4단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("데이터베이스 설정이 완료되었습니다!")
    print("이제 main.py를 실행하여 프로그램을 사용할 수 있습니다.")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"\n오류 발생: {e}")
        print("\n문제가 지속되면 다음을 확인해주세요:")
        print("1. SQL Server가 실행 중인지 확인")
        print("2. 방화벽에서 SQL Server 포트 허용 확인")
        print("3. db_config.py의 연결 정보 확인")
        print("4. ODBC Driver 설치 확인")
