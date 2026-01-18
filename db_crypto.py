"""
데이터베이스 설정 암호화/복호화 모듈
"""

import os
import sys
import json
import base64
import hashlib
from pathlib import Path

# cryptography 라이브러리 사용 (설치 필요: pip install cryptography)
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


def get_machine_key():
    """머신 고유 키 생성 (컴퓨터명 + 사용자명 기반)"""
    machine_id = f"{os.environ.get('COMPUTERNAME', 'PC')}_{os.environ.get('USERNAME', 'USER')}"
    # 32바이트 키 생성
    key_hash = hashlib.sha256(machine_id.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)


def get_config_path():
    """암호화된 설정 파일 경로"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 실행 파일
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent
    return base_path / 'db_config.enc'


def encrypt_config(config_dict):
    """설정 딕셔너리 암호화"""
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography 라이브러리가 필요합니다. pip install cryptography")

    key = get_machine_key()
    fernet = Fernet(key)

    json_data = json.dumps(config_dict, ensure_ascii=False)
    encrypted = fernet.encrypt(json_data.encode('utf-8'))
    return encrypted


def decrypt_config(encrypted_data):
    """암호화된 데이터 복호화"""
    if not CRYPTO_AVAILABLE:
        raise ImportError("cryptography 라이브러리가 필요합니다. pip install cryptography")

    key = get_machine_key()
    fernet = Fernet(key)

    decrypted = fernet.decrypt(encrypted_data)
    return json.loads(decrypted.decode('utf-8'))


def save_encrypted_config(config_dict, file_path=None):
    """암호화된 설정을 파일로 저장"""
    if file_path is None:
        file_path = get_config_path()

    encrypted = encrypt_config(config_dict)

    with open(file_path, 'wb') as f:
        f.write(encrypted)

    print(f"암호화된 설정이 저장되었습니다: {file_path}")
    return True


def load_encrypted_config(file_path=None):
    """암호화된 설정 파일 로드"""
    if file_path is None:
        file_path = get_config_path()

    if not os.path.exists(file_path):
        return None

    with open(file_path, 'rb') as f:
        encrypted = f.read()

    return decrypt_config(encrypted)


def get_db_config():
    """DB 설정 가져오기 (암호화 파일 우선, 없으면 일반 파일)"""
    # 1. 암호화된 설정 파일 확인
    enc_path = get_config_path()
    if os.path.exists(enc_path):
        try:
            config = load_encrypted_config(enc_path)
            if config:
                return config
        except Exception as e:
            print(f"암호화된 설정 로드 실패: {e}")

    # 2. 일반 db_config.py 파일에서 로드
    try:
        from db_config import DB_CONFIG
        return DB_CONFIG
    except ImportError:
        return None


def migrate_to_encrypted():
    """기존 db_config.py를 암호화된 파일로 마이그레이션"""
    try:
        from db_config import DB_CONFIG

        # 암호화 저장
        save_encrypted_config(DB_CONFIG)

        print("\n기존 설정이 암호화되었습니다.")
        print("보안을 위해 db_config.py 파일의 비밀번호를 삭제하거나")
        print("파일 자체를 삭제하는 것을 권장합니다.")
        return True
    except ImportError:
        print("db_config.py 파일을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"마이그레이션 실패: {e}")
        return False


def create_encrypted_config_interactive():
    """대화형으로 암호화된 설정 생성"""
    print("\n=== DB 설정 암호화 ===\n")

    server = input("서버 주소 (예: localhost,1433): ").strip()
    database = input("데이터베이스 이름: ").strip()

    auth_type = input("인증 방식 (1: SQL Server 인증, 2: Windows 인증): ").strip()

    if auth_type == "2":
        config = {
            'server': server,
            'database': database,
            'trusted_connection': 'yes',
            'driver': '{ODBC Driver 18 for SQL Server}'
        }
    else:
        username = input("사용자명: ").strip()
        password = input("비밀번호: ").strip()
        config = {
            'server': server,
            'database': database,
            'username': username,
            'password': password,
            'driver': '{ODBC Driver 18 for SQL Server}'
        }

    save_encrypted_config(config)
    print("\n설정이 암호화되어 저장되었습니다.")
    return config


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='DB 설정 암호화 도구')
    parser.add_argument('--migrate', action='store_true', help='기존 db_config.py를 암호화')
    parser.add_argument('--create', action='store_true', help='새 암호화 설정 생성')
    parser.add_argument('--test', action='store_true', help='현재 설정 테스트')

    args = parser.parse_args()

    if args.migrate:
        migrate_to_encrypted()
    elif args.create:
        create_encrypted_config_interactive()
    elif args.test:
        config = get_db_config()
        if config:
            print("\n현재 DB 설정:")
            print(f"  서버: {config.get('server')}")
            print(f"  DB: {config.get('database')}")
            print(f"  사용자: {config.get('username', 'Windows 인증')}")
            print(f"  드라이버: {config.get('driver')}")
        else:
            print("설정을 찾을 수 없습니다.")
    else:
        parser.print_help()
