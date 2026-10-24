#!/usr/bin/env python3
"""
다이어트봇 (DietBot) - 8대 고객 입력값 기반 맞춤 웹사이트 자동 빌더 (개인화 엔진 통합판)
"""

import os
import sys
import json
import argparse
import shutil
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
CLIENTS_DIR = os.path.join(ROOT_DIR, "clients")
GENERATOR_DIR = os.path.join(ROOT_DIR, "generator")

sys.path.insert(0, GENERATOR_DIR)
import recipe_engine
import storage_engine

def get_live_public_url():
    return "https://bohwan100.github.io/zipbab"

def build_client(
    client_id,
    name="고객님",
    age="30대",
    household="1명",
    budget=300000,
    frequency="저녁만 (30끼)",
    goal="다이어트",
    cuisine="한식, 일식",
    exclude="없음",
    pantry="아무것도 없음",
    goal_notes="",
    data_file=None
):
    client_dir = os.path.join(CLIENTS_DIR, client_id)
    os.makedirs(client_dir, exist_ok=True)

    # 확장 프로그램 zip 복사 (상대경로/캐시 접근 100% 방어)
    ext_src = os.path.join(ROOT_DIR, "assets", "extension", "zipbabbot-extension.zip")
    if os.path.exists(ext_src):
        try:
            shutil.copy(ext_src, os.path.join(client_dir, "zipbabbot-extension.zip"))
        except Exception:
            pass

    # 1. 개인화 알고리즘 엔진 실행 (식단 30/60/90끼 편성, 인원수 정량 스케일링, 재료 공제)
    plan = recipe_engine.generate_personalized_plan(
        client_name=name,
        household=household,
        budget=budget,
        frequency=frequency,
        concept=goal,
        cuisine=cuisine,
        exclude=exclude,
        pantry=pantry,
        goal_notes=goal_notes
    )

    theme_title = f"{name}님을 위한 {household} {goal} 맞춤 식단 ({cuisine})"

    # 요리별 통계 계산
    cuisine_counts = {}
    for r in plan["recipes"]:
        c = r.get("cuisine", "기타")
        cuisine_counts[c] = cuisine_counts.get(c, 0) + 1

    flag_map = {"한식": "🇰🇷", "일식": "🇯🇵", "중식": "🇨🇳", "양식": "🇪🇺", "동남아": "🥢"}
    cuisine_card_items = [f"{flag_map.get(c, '🍽️')}{c} {cnt}" for c, cnt in cuisine_counts.items()]
    cuisine_card_str = " · ".join(cuisine_card_items)
    cuisine_stat_str = " · ".join([f"{c} {cnt}끼" for c, cnt in cuisine_counts.items()])

    # 2. 템플릿 복사 및 실시간 맞춤 데이터 주입
    templates = {
        "portal.html": "index.html",
        "cart.html": "cart.html",
        "recipes.html": "recipes.html",
        "storage.html": "storage.html"
    }

    for src_name, dest_name in templates.items():
        src_path = os.path.join(TEMPLATES_DIR, src_name)
        dest_path = os.path.join(client_dir, dest_name)
        if not os.path.exists(src_path):
            print(f"[!] Warning: Template not found: {src_path}")
            continue

        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 공통 링크 정규화
        content = content.replace('recipe_viewer.html', 'recipes.html')
        content = content.replace('cart_dashboard.html', 'cart.html')
        content = content.replace('storage_guide.html', 'storage.html')

        # A. index.html (포털 홈) 개인화 주입
        if dest_name == "index.html":
            content = content.replace('<title>다이어트봇 | 1인 가구 20만원 30일 식단 & 스마트 장보기 포털</title>', f'<title>{name}님 맞춤 30일 식단 & 스마트 장보기 포털 | 다이어트봇</title>')
            content = content.replace('content="다이어트봇 | 1인 가구 20만원 30일 식단 & 스마트 장보기 포털"', f'content="{name}님 {household} 맞춤 식단 & 스마트 장보기 포털 | 다이어트봇"')
            content = content.replace('content="1인 가구 20만원 한 달 식단 & 쿠팡 1초 원클릭 스마트 장바구니 자동화 솔루션"', f'content="{name}님을 위한 {goal} 맞춤 식단과 쿠팡 1초 원클릭 스마트 장바구니"')
            content = content.replace("1인 가구 20만원 식단 & 스마트 장보기", f"{name}님 {household} 맞춤 포털 | {cuisine}")
            content = content.replace("한 달 20만 원으로 누리는", f"{name}님 맞춤 플랜")
            content = content.replace('<p style="font-size: 1.25rem; font-weight: 600; color: #cbd5e1;">배달음식 끊고 집밥 해먹자!!</p>', '')
            content = content.replace("배달음식 끊고 집밥 해먹자!!", "")
            content = content.replace("🌍 4대 요리 조화:", "🍽️ 맞춤 요리 구성:")
            content = content.replace("🌐 4대 요리 조화:", "🍽️ 맞춤 요리 구성:")
            content = content.replace("한식 12 · 일식 6 · 중식 6 · 양식 6", f"{cuisine_stat_str} (맞춤 설계)")
            content = content.replace("🇰🇷한식 12 · 🇯🇵일식 6 · 🇨🇳중식 6 · 🇪🇺양식 6", f"{cuisine_card_str} 맞춤 황금 레시피")
            content = content.replace("단계별 상세 조리법 & 프로 셰프 팁 수록", "단계별 상세 맞춤 조리법 수록")
            content = content.replace("189,700원 실구매 (예산 20만원 이내 100%)", f"{plan['total_spent']:,}원 실구매 (예산 {budget:,}원 대비 {plan['saved_from_budget']:,}원 절약)")
            content = content.replace("1인 가구를 위한 20만원 한 달 식단 & 스마트 장보기 통합 시스템.", "by. 집밥보이 (Zipbaboy)")
            content = content.replace("200,000원", f"{budget:,}원")
            content = content.replace("189,700원", f"{plan['total_spent']:,}원")
            content = content.replace("(+10,300원 절감!)", f"(+{plan['saved_from_budget']:,}원 절약!)")
            content = content.replace("1인 가구", household)

            if plan['total_saved_pantry'] > 0:
                pantry_badge = f'<div class="stat-pill" style="border-color: rgba(16, 185, 129, 0.4); background: rgba(16, 185, 129, 0.1);"><span>🏠 기존 재료 절감:</span><strong style="color: #34d399;">+{plan["total_saved_pantry"]:,}원 세이브!</strong></div>'
                content = content.replace('</div>\n\n    <!-- Program Guide CTA Button', f'  {pantry_badge}\n    </div>\n\n    <!-- Program Guide CTA Button')


            # 4주 분할 주문 로드맵 (strategy-grid) 실시간 동적 주입
            w_totals = plan.get("week_totals", {1: 0, 2: 0, 3: 0, 4: 0})
            products = plan.get("products", [])

            def get_week_summary(w_num):
                w_items = [p["name"].replace(" [🏠 보유 재료 0원 공제]", "") for p in products if p.get("orderWeek") == w_num and p.get("total", 0) > 0]
                clean_names = []
                for n in w_items:
                    base_n = re.sub(r'\(.*?\)', '', n).strip()
                    if base_n not in clean_names:
                        clean_names.append(base_n)
                if not clean_names:
                    return "잔여 식재료 알뜰 소진 및 맞춤 요리"
                return ", ".join(clean_names[:5]) + (" 등" if len(clean_names) > 5 else "")

            strategy_grid_html = f'''<div class="strategy-grid">
        <div class="strategy-col">
          <div class="col-week">1주차 주문</div>
          <div class="col-price">{w_totals.get(1, 0):,}원</div>
          <div class="col-desc">{get_week_summary(1)}</div>
        </div>
        <div class="strategy-col">
          <div class="col-week">2주차 주문</div>
          <div class="col-price">{w_totals.get(2, 0):,}원</div>
          <div class="col-desc">{get_week_summary(2)}</div>
        </div>
        <div class="strategy-col">
          <div class="col-week">3주차 주문</div>
          <div class="col-price">{w_totals.get(3, 0):,}원</div>
          <div class="col-desc">{get_week_summary(3)}</div>
        </div>
        <div class="strategy-col">
          <div class="col-week">4주차 주문</div>
          <div class="col-price">{w_totals.get(4, 0):,}원</div>
          <div class="col-desc">{get_week_summary(4)}</div>
        </div>
      </div>
    </div>'''

            content = re.sub(r'<div class="strategy-grid">[\s\S]*?</div>\s*</div>\s*(?=</main>)', strategy_grid_html, content)

        # B. recipes.html (레시피 뷰어) 실시간 레시피 주입
        elif dest_name == "recipes.html":
            tot_meals = plan["total_meals"]
            content = content.replace('<title>🍳 [1인 가구] 한·일·중·양 4대 요리 30일 황금 레시피 & 영양 매니저</title>', f'<title>🍳 {name}님 전용 {tot_meals}끼 황금 레시피 | 다이어트봇</title>')
            content = content.replace('content="🍳 황금 레시피 & 영양 매니저 | 다이어트봇"', f'content="🍳 {name}님 전용 {tot_meals}끼 황금 레시피 | 다이어트봇"')
            content = content.replace('content="퇴근 후 10분 컷 초간단 원팬 집밥 레시피 & 단백질 맞춤 식단"', f'content="{name}님 맞춤 {cuisine} 10분 컷 초간단 집밥 레시피"')
            content = content.replace("30일 메뉴 구성 (한식 12 · 일식 6 · 중식 6 · 양식 6)", f"{name}님 전용 {tot_meals}끼 식단 ({cuisine_stat_str} · {household} 정량)")
            content = content.replace("1인분 정량 조리", f"{household} 정량 조리 ({plan['people_count']}인분)")
            content = content.replace("1인분 식재료", f"{household} 정량 식재료")
            content = content.replace("퇴근 후 15분 컷", f"목표: {goal}")

            # 필터 버튼 HTML 생성
            filter_buttons_html = f'<button class="btn-filter active" onclick="filterCuisine(\'all\', this)">전체 ({tot_meals}끼)</button>\n'
            for c, cnt in cuisine_counts.items():
                flag = flag_map.get(c, "🍽️")
                filter_buttons_html += f'        <button class="btn-filter" onclick="filterCuisine(\'{c}\', this)">{flag} {c} ({cnt}끼)</button>\n'
            
            content = re.sub(r'<div class="cuisine-filters">[\s\S]*?</div>', f'<div class="cuisine-filters">\n        {filter_buttons_html.strip()}\n      </div>', content)

            # const recipes = [...] 배열 교체
            recipes_json = json.dumps(plan["recipes"], ensure_ascii=False, indent=2)
            content = re.sub(r'const recipes = \[[\s\S]*?\];', f'const recipes = {recipes_json};', content)

        # C. cart.html (장바구니 매니저) 실시간 예산 & 보유 재료 안내 & 주차별 장바구니 주입
        elif dest_name == "cart.html":
            tot_spent = plan["total_spent"]
            content = content.replace('<title>스마트 장바구니 매니저 | 다이어트봇</title>', f'<title>{name}님 스마트 장바구니 매니저 | 다이어트봇</title>')
            content = content.replace('content="스마트 장바구니 매니저 | 다이어트봇"', f'content="{name}님 스마트 장바구니 매니저 | 다이어트봇"')
            content = content.replace('content="4주 분할 장보기 & 쿠팡 로켓배송 1초 원클릭 자동 담기"', f'content="{name}님 4주 분할 장보기 ({tot_spent:,}원) & 쿠팡 1초 원클릭 자동 담기"')
            content = content.replace("1인 가구", household)

            # 주차별 4개 분할 카드 금액 교체
            w_totals = plan.get("week_totals", {1: 0, 2: 0, 3: 0, 4: 0})
            content = re.sub(
                r'<div class="split-amount">105,250원</div>',
                f'<div class="split-amount">{w_totals.get(1, 0):,}원</div>',
                content
            )
            content = re.sub(
                r'<div class="split-amount">39,200원</div>',
                f'<div class="split-amount">{w_totals.get(2, 0):,}원</div>',
                content
            )
            content = re.sub(
                r'<div class="split-amount">16,610원</div>',
                f'<div class="split-amount">{w_totals.get(3, 0):,}원</div>',
                content
            )
            content = re.sub(
                r'<div class="split-amount">25,920원</div>',
                f'<div class="split-amount">{w_totals.get(4, 0):,}원</div>',
                content
            )

            # 액션 배너 총액 & 절약금액 교체
            banner_html = f'<p>💡 <strong>4주 총 구매액</strong>: <strong>{plan["total_spent"]:,}원</strong> (예산 {budget:,}원 대비 <strong style="color: #34d399;">+{plan["saved_from_budget"]:,}원</strong> 절감 성공, 4회 배송비 전액 0원, 잔여 쓰레기 0%)</p>'
            content = re.sub(r'<p>💡 <strong>4주 총 구매액</strong>:[\s\S]*?</p>', banner_html, content)

            # const allProducts = [...] 동적 품목 주입
            if "products" in plan:
                products_json = json.dumps(plan["products"], ensure_ascii=False, indent=2)
                content = re.sub(r'const allProducts = \[[\s\S]*?\];', f'const allProducts = {products_json};', content)

            # const weekData = {...} 동적 주차별 식단 주입
            if "week_data" in plan:
                week_data_json = json.dumps(plan["week_data"], ensure_ascii=False, indent=2)
                content = re.sub(r'const weekData = \{[\s\S]*?\n    \};', f'const weekData = {week_data_json};', content)

            if plan['total_saved_pantry'] > 0:
                pantry_banner = f'''
                <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 12px; padding: 14px 18px; margin: 12px 0 16px; display: flex; align-items: center; gap: 10px;">
                  <span style="font-size: 1.5rem;">🏠</span>
                  <div>
                    <strong style="color: #34d399; font-size: 0.95rem;">보유 식재료 0원 공제 완료:</strong>
                    <div style="color: #cbd5e1; font-size: 0.85rem; margin-top: 2px;">
                      집에 보유 중인 식재료(<strong>{pantry}</strong>)를 장바구니에서 0원 처리하여 <strong>총 {plan['total_saved_pantry']:,}원의 장보기 비용을 절약</strong>했습니다!
                    </div>
                  </div>
                </div>
                '''
                if '<!-- Pantry Banner Anchor -->' in content:
                    content = content.replace('<!-- Pantry Banner Anchor -->', f'{pantry_banner}\n      <!-- Pantry Banner Anchor -->')
                elif '<!-- Coupang Partners Status & FTC Disclosure Notice -->' in content:
                    content = content.replace('<!-- Coupang Partners Status & FTC Disclosure Notice -->', f'{pantry_banner}\n      <!-- Coupang Partners Status & FTC Disclosure Notice -->')

        # D. storage.html (고객 맞춤 실제 구매 식재료 100% 동적 보관 가이드)
        elif dest_name == "storage.html":
            storage_cards = storage_engine.generate_storage_data_for_products(plan.get("products", []))
            storage_json = json.dumps(storage_cards, ensure_ascii=False, indent=2)

            fresh_cnt = len([c for c in storage_cards if c['category'] == 'fresh'])
            frozen_cnt = len([c for c in storage_cards if c['category'] == 'frozen'])
            seasoning_cnt = len([c for c in storage_cards if c['category'] == 'seasoning'])
            total_cnt = len(storage_cards)

            content = content.replace('<title>1인 가구 37종 식재료 보관 & 소분 백과 | 다이어트봇</title>', f'<title>{name}님 맞춤 식재료 보관 & 소분 백과 | 다이어트봇</title>')
            content = content.replace('content="식재료 소분 & 신선 보관 백과 | 다이어트봇"', f'content="{name}님 맞춤 식재료 보관 & 소분 백과 | 다이어트봇"')
            content = content.replace('content="1인 가구 소형 냉장고 맞춤 식재료 완벽 소분 & 신선도 극대화 보관법"', f'content="{name}님 구매 식재료 100% 맞춤 신선도 극대화 보관법"')
            content = content.replace("1인 가구 37종 식재료 보관 & 소분 백과", f"{name}님 {household} 맞춤 {total_cnt}종 식재료 보관 & 소분 백과")
            content = content.replace("1인 가구 소형 냉장고 맞춤 솔루션", f"{name}님 {household} 구매 식재료 100% 맞춤 보관법")
            content = content.replace("❄️ 37종 식재료 완벽 소분 & 신선 보관 백과", f"❄️ {total_cnt}종 맞춤 식재료 완벽 소분 & 신선 보관 백과")
            content = content.replace("전체 37종", f"전체 ({total_cnt}종)")
            content = content.replace("🥬 신선식품 (냉장 14종)", f"🥬 신선식품 (냉장 {fresh_cnt}종)")
            content = content.replace("❄️ 냉동식품 (소형 냉동실 7종)", f"❄️ 냉동식품 (냉동 {frozen_cnt}종)")
            content = content.replace("🧂 조미료 & 팬트리 (16종)", f"🧂 조미료 & 팬트리 ({seasoning_cnt}종)")

            # JavaScript storageData 배열 동적 교체
            content = re.sub(r'const storageData = \[[\s\S]*?\n    \];', f'const storageData = {storage_json};', content)

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✓ 개인화 생성됨: {dest_name}")

    # 3. 메타데이터 JSON 저장
    import time, datetime
    reg_now_ts = int(time.time())
    reg_now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    info = {
        "client_id": client_id,
        "client_name": name,
        "client_age": age,
        "household_size": household,
        "people_count": plan["people_count"],
        "budget": budget,
        "total_spent": plan["total_spent"],
        "saved_from_budget": plan["saved_from_budget"],
        "total_saved_pantry": plan["total_saved_pantry"],
        "meal_frequency": frequency,
        "total_meals": plan["total_meals"],
        "goal": goal,
        "cuisine": cuisine,
        "excluded_foods": exclude,
        "pantry_items": pantry,
        "goal_notes": goal_notes,
        "theme": theme_title,
        "created_at": reg_now_str,
        "created_timestamp": reg_now_ts,
        "recipes_summary": [r["title"] for r in plan["recipes"][:5]],
        "pages": {
            "portal": f"clients/{client_id}/index.html",
            "cart": f"clients/{client_id}/cart.html",
            "recipes": f"clients/{client_id}/recipes.html",
            "storage": f"clients/{client_id}/storage.html"
        }
    }

    info_path = os.path.join(client_dir, "client_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 메타데이터: client_info.json")

    # 3-1. clients_registry.json에 영구 등록 (최신순 불변 정렬 보장)
    try:
        reg_file = os.path.join(ROOT_DIR, "data", "clients_registry.json")
        reg_data = {}
        if os.path.exists(reg_file):
            with open(reg_file, "r", encoding="utf-8") as f:
                reg_data = json.load(f)
        reg_data[client_id] = {
            "client_id": client_id,
            "client_name": name,
            "registered_at": reg_now_str,
            "timestamp": reg_now_ts,
            "pinned": ("최종본" in client_id)
        }
        with open(reg_file, "w", encoding="utf-8") as f:
            json.dump(reg_data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 영구 레지스트리 등록: data/clients_registry.json")
    except Exception as e:
        print(f"  [-] 레지스트리 등록 생략: {e}")


    # 4. 모바일 QR 생성
    try:
        import qrcode
        from urllib.parse import quote
        cloud_base_url = get_live_public_url()
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        target_link = f"{cloud_base_url}/clients/{quote(client_id)}/index.html"
        qr.add_data(target_link)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1e293b", back_color="white")
        qr_path = os.path.join(client_dir, "qr_mobile.png")
        img.save(qr_path)
        print(f"  ✓ 모바일 QR 생성: qr_mobile.png")
    except Exception as e:
        print(f"  [-] QR 생성 생략: {e}")

    print("\n" + "="*65)
    print(f"🎉 [{name}] ({household} / {budget:,}원 / {frequency}) 맞춤 웹사이트 생성 완료!")
    print(f"📁 폴더: clients/{client_id}/")
    print(f"🍽️ 레시피 편성: {cuisine} ({plan['total_meals']}끼 플랜, {plan['people_count']}인분 정량)")
    print(f"💰 총 구매액: {plan['total_spent']:,}원 (예산 절약: {plan['saved_from_budget']:,}원 | 기존 재료 절감: {plan['total_saved_pantry']:,}원)")
    print(f"🚫 제외 식품: {exclude} | 🏠 보유 재료: {pantry}")
    print("="*65 + "\n")

    return info

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="다이어트봇 개인화 엔진 통합 빌더")
    parser.add_argument("--id", required=True, help="고객 식별 ID")
    parser.add_argument("--name", default="고객님", help="성함")
    parser.add_argument("--age", default="30대", help="나이")
    parser.add_argument("--household", default="1명", help="구성 인원")
    parser.add_argument("--budget", type=int, default=300000, help="한 달 예산")
    parser.add_argument("--frequency", default="저녁만 (30끼)", help="식사 횟수")
    parser.add_argument("--goal", default="다이어트", help="목표/콘셉트")
    parser.add_argument("--cuisine", default="한식, 일식", help="음식 취향")
    parser.add_argument("--exclude", default="없음", help="알레르기·제외 식품")
    parser.add_argument("--pantry", default="아무것도 없음", help="집에 있는 재료")

    args = parser.parse_args()
    build_client(
        client_id=args.id,
        name=args.name,
        age=args.age,
        household=args.household,
        budget=args.budget,
        frequency=args.frequency,
        goal=args.goal,
        cuisine=args.cuisine,
        exclude=args.exclude,
        pantry=args.pantry
    )
