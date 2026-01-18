# -*- coding: utf-8 -*-
"""
기본 업무 템플릿 확인 스크립트
"""
import sys
import io
from database import Database

# UTF-8 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def check_default_tasks():
    """기본 업무 템플릿 확인"""
    print("=" * 60)
    print("기본 업무 템플릿 확인")
    print("=" * 60)

    db = Database()

    # 1. 데이터베이스 연결
    print("\n[1단계] 데이터베이스 연결 중...")
    if db.connect():
        print("[OK] 데이터베이스 연결 성공!")
    else:
        print("[FAIL] 데이터베이스 연결 실패!")
        return False

    # 2. DefaultTasks 테이블의 모든 데이터 조회
    print("\n[2단계] DefaultTasks 테이블 전체 데이터 조회...")
    try:
        query = """
        SELECT id, display_order, time_slot, task_name, company, end_time, description, is_active
        FROM DefaultTasks
        ORDER BY display_order, time_slot
        """
        db.cursor.execute(query)
        rows = db.cursor.fetchall()

        print(f"\n[DefaultTasks 테이블 전체 데이터] - 총 {len(rows)}개")
        print("-" * 120)
        print(f"{'ID':<5} {'순서':<6} {'시작':<8} {'종료':<8} {'업체명':<12} {'법인명':<15} {'활성':<6} {'설명':<30}")
        print("-" * 120)

        for row in rows:
            row_id = row.id if hasattr(row, 'id') else '-'
            display_order = row.display_order if row.display_order else '-'
            time_slot = row.time_slot if row.time_slot else '-'
            end_time = row.end_time if row.end_time else '-'
            company = row.company if row.company else '-'
            task_name = row.task_name if row.task_name else '-'
            is_active = 'Y' if row.is_active else 'N'
            description = (row.description[:27] + '...') if row.description and len(row.description) > 30 else (row.description if row.description else '-')

            print(f"{row_id:<5} {str(display_order):<6} {time_slot:<8} {end_time:<8} {company:<12} {task_name:<15} {is_active:<6} {description:<30}")
        print("-" * 120)
    except Exception as e:
        print(f"[FAIL] 데이터 조회 오류: {e}")
        db.disconnect()
        return False

    # 3. get_default_tasks() 메서드로 조회
    print("\n[3단계] get_default_tasks() 메서드로 조회...")
    try:
        tasks = db.get_default_tasks()

        print(f"\n[get_default_tasks() 결과] - 총 {len(tasks)}개")
        print("-" * 100)
        print(f"{'순서':<6} {'시작시간':<10} {'종료시간':<10} {'업체명':<12} {'법인명':<15} {'설명':<30}")
        print("-" * 100)

        # display_order 순서대로 정렬
        sorted_tasks = sorted(tasks.items(), key=lambda x: x[0])

        for display_order, task_info in sorted_tasks:
            time_slot = task_info.get('time_slot', '-')
            end_time = task_info.get('end_time', '-')
            company = task_info.get('company', '-')
            task_name = task_info.get('task', '-')
            description = task_info.get('description', '-')
            description = (description[:27] + '...') if len(description) > 30 else description

            print(f"{str(display_order):<6} {time_slot:<10} {end_time:<10} {company:<12} {task_name:<15} {description:<30}")
        print("-" * 100)
    except Exception as e:
        print(f"[FAIL] get_default_tasks() 오류: {e}")

    # 4. 업체별 그룹화 테스트
    print("\n[4단계] 업체별 그룹화 테스트...")
    try:
        tasks = db.get_default_tasks()
        tasks_by_company = {}
        company_display_order = {}

        for time_slot, task_info in tasks.items():
            company = task_info.get("company", "")
            if company:
                if company not in tasks_by_company:
                    tasks_by_company[company] = {}
                    company_display_order[company] = task_info.get("display_order", 999)
                else:
                    current_order = task_info.get("display_order", 999)
                    if current_order < company_display_order[company]:
                        company_display_order[company] = current_order
                tasks_by_company[company][time_slot] = task_info

        print(f"\n[업체별 그룹화 결과] - 총 {len(tasks_by_company)}개 업체")
        print("-" * 80)
        # 업체를 최소 display_order 순서대로 정렬
        sorted_companies = sorted(tasks_by_company.items(), key=lambda x: company_display_order.get(x[0], 999))
        for company, company_tasks in sorted_companies:
            min_order = company_display_order.get(company, 999)
            print(f"\n업체: {company} (최소 순서: {min_order}) - {len(company_tasks)}개 업무")
            print("-" * 80)
            for time_slot, task_info in company_tasks.items():
                print(f"  {time_slot} ~ {task_info.get('end_time', '-')}: {task_info.get('task', '-')} (순서: {task_info.get('display_order', '-')})")
        print("-" * 80)
    except Exception as e:
        print(f"[FAIL] 그룹화 테스트 오류: {e}")

    # 5. 연결 종료
    print("\n[5단계] 데이터베이스 연결 종료...")
    db.disconnect()
    print("[OK] 연결 종료 완료!")

    print("\n" + "=" * 60)
    print("기본 업무 템플릿 확인 완료!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        check_default_tasks()
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
