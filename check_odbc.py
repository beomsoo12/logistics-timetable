"""
설치된 ODBC 드라이버 확인 스크립트
"""
import pyodbc

print("=" * 60)
print("설치된 ODBC 드라이버 목록")
print("=" * 60)

drivers = pyodbc.drivers()

if drivers:
    for i, driver in enumerate(drivers, 1):
        print(f"{i}. {driver}")
else:
    print("설치된 ODBC 드라이버가 없습니다.")

print("=" * 60)
print("\nSQL Server용 드라이버를 찾아 db_config.py에 설정하세요.")
print("예: 'driver': '{ODBC Driver 17 for SQL Server}'")
