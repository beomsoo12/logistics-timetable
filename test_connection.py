"""
다양한 연결 방식으로 테스트
"""
import pyodbc

# 테스트할 연결 문자열 리스트
connection_strings = [
    # 1. 기본 포트 명시
    (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=192.168.10.9,1433;"
        "DATABASE=LogisticsDB;"
        "UID=AI;"
        "PWD=20260101!;"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    ),
    # 2. TCP 프로토콜 명시
    (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=tcp:192.168.10.9,1433;"
        "DATABASE=LogisticsDB;"
        "UID=AI;"
        "PWD=20260101!;"
        "TrustServerCertificate=yes;"
        "Encrypt=no;"
    ),
    # 3. ODBC Driver 11 사용
    (
        "DRIVER={ODBC Driver 11 for SQL Server};"
        "SERVER=192.168.10.9;"
        "DATABASE=LogisticsDB;"
        "UID=AI;"
        "PWD=20260101!;"
    ),
    # 4. SQL Server Native Client 사용
    (
        "DRIVER={SQL Server Native Client 11.0};"
        "SERVER=192.168.10.9;"
        "DATABASE=LogisticsDB;"
        "UID=AI;"
        "PWD=20260101!;"
    ),
    # 5. 기본 SQL Server 드라이버
    (
        "DRIVER={SQL Server};"
        "SERVER=192.168.10.9;"
        "DATABASE=LogisticsDB;"
        "UID=AI;"
        "PWD=20260101!;"
    ),
]

print("=" * 70)
print("SQL Server 연결 테스트")
print("=" * 70)

for i, conn_str in enumerate(connection_strings, 1):
    print(f"\n[테스트 {i}] 연결 시도 중...")
    print(f"연결 문자열: {conn_str[:80]}...")

    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        print(f"성공! 이 연결 문자열을 사용하세요.")

        # 서버 정보 확인
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"\nSQL Server 버전:")
        print(version[:100] + "...")

        cursor.close()
        conn.close()

        print("\n" + "=" * 70)
        print("연결 성공! 이 설정을 database.py에 적용하세요.")
        print("=" * 70)
        break

    except Exception as e:
        print(f"실패: {str(e)[:100]}")

else:
    print("\n" + "=" * 70)
    print("모든 연결 시도가 실패했습니다.")
    print("\n다음을 확인해주세요:")
    print("1. SQL Server가 192.168.10.9에서 실행 중인지")
    print("2. SQL Server가 TCP/IP 연결을 허용하도록 설정되어 있는지")
    print("3. 방화벽에서 포트 1433이 열려있는지")
    print("4. 사용자명(AI)과 비밀번호(20260101!)가 정확한지")
    print("5. LogisticsDB 데이터베이스가 존재하는지")
    print("=" * 70)
