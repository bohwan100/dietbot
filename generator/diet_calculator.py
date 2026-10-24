# -*- coding: utf-8 -*-
"""
다이어트봇 (DietBot) - 정밀 신체 대사량 & 탄단지 매크로 및 원물 식단 추천 계산기
"""

def calculate_diet_macro(age, gender, height_cm, weight_kg, target_weight_kg,
                         activity_level, workout_type, workout_freq, workout_duration,
                         meal_change_target, budget=250000, allergies=""):
    """
    고객 신체 및 생활 패턴 데이터를 기반으로 BMR, TDEE, 목표 섭취 칼로리, 탄단지 매크로 및 맞춤 원물 식단을 계산합니다.
    """
    try:
        age = float(age)
        height_cm = float(height_cm)
        weight_kg = float(weight_kg)
        target_weight_kg = float(target_weight_kg) if target_weight_kg else weight_kg - 5.0
    except Exception:
        age, height_cm, weight_kg, target_weight_kg = 30.0, 170.0, 70.0, 65.0

    # 1. BMR 계산 (Mifflin-St Jeor 식)
    is_male = (gender.strip().lower() in ['남', '남성', 'male', 'm'])
    if is_male:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    bmr = round(bmr)

    # 2. 활동량 계수
    act_str = str(activity_level).lower()
    if '좌식' in act_str or '앉아' in act_str:
        act_factor = 1.2
    elif '가벼운' in act_str:
        act_factor = 1.375
    elif '활동적인' in act_str or '현장' in act_str:
        act_factor = 1.55
    elif '매우' in act_str:
        act_factor = 1.725
    else:
        act_factor = 1.3

    # 운동 빈도 보정 (+0.05 ~ +0.15)
    freq_str = str(workout_freq)
    if '5회' in freq_str:
        act_factor += 0.15
    elif '3~4회' in freq_str or '3' in freq_str or '4' in freq_str:
        act_factor += 0.10
    elif '1~2회' in freq_str or '1' in freq_str or '2' in freq_str:
        act_factor += 0.05

    tdee = round(bmr * act_factor)

    # 3. 목표 섭취 칼로리 (Target Calories)
    weight_diff = weight_kg - target_weight_kg
    if weight_diff > 0:
        # 체중 감량: 일일 400~500 kcal 결손 (체지방 0.5kg/주 감량)
        target_cal = tdee - 480
        # 안전 하한선: BMR 아래로 급격히 떨어지지 않도록 보장
        if target_cal < bmr:
            target_cal = max(bmr, target_cal + 150)
    elif weight_diff < 0:
        # 근육 증량 / 린매스업: +250 kcal
        target_cal = tdee + 250
    else:
        target_cal = tdee

    target_cal = round(target_cal)

    # 4. 탄·단·지 매크로 배분 (g 및 %)
    # 단백질: 체중당 1.8g (체지방 감량기 근손실 방어 최적 수치)
    protein_g = round(weight_kg * 1.8)
    protein_cal = protein_g * 4

    # 지방: 총 칼로리의 23%
    fat_cal = round(target_cal * 0.23)
    fat_g = round(fat_cal / 9)

    # 탄수화물: 나머지 칼로리
    carbs_cal = max(0, target_cal - protein_cal - fat_cal)
    carbs_g = round(carbs_cal / 4)

    # 비율 계산 (%)
    protein_pct = round((protein_cal / target_cal) * 100)
    fat_pct = round((fat_cal / target_cal) * 100)
    carbs_pct = max(0, 100 - protein_pct - fat_pct)

    # 5. 맞춤 원물 식단 조합 라이브러리 (피그인더가든 샐러드, 스팀 닭가슴살, 매일두유 고단백 등)
    raw_food_combos = [
        {
            "id": "combo_salad_chicken_soymilk",
            "name": "🥗 타임핏 샐러드 & 스팀닭 & 고단백 두유 세트 (시그니처)",
            "desc": "피그인더가든 샐러드(식이섬유 6g) + 착한 닭가슴살(단백질 23g) + 매일두유 고단백(단백질 12g)",
            "calories": 325,
            "protein": 43,
            "carbs": 24,
            "fat": 7,
            "items": [
                {"name": "피그인더가든 타임핏 스모키포크/닭가슴살 샐러드", "spec": "1팩 (드레싱 포함)", "cal": 120, "protein": 8, "coupang_keyword": "피그인더가든 샐러드"},
                {"name": "착한 닭가슴살 블랙페퍼/오리지널", "spec": "1팩 100g", "cal": 115, "protein": 23, "coupang_keyword": "착한닭가슴살 100g"},
                {"name": "매일두유 플레인 고단백 190ml", "spec": "1팩 (설탕무첨가)", "cal": 90, "protein": 12, "coupang_keyword": "매일두유 고단백"}
            ]
        },
        {
            "id": "combo_sweetpotato_egg_salad",
            "name": "🍠 꿀고구마 & 구운란 & 믹스 샐러드 볼 세트",
            "desc": "자연 복합 탄수화물 고구마(120g) + 훈제란 2알 + 신선 샐러드 채소 + 발사믹 드레싱",
            "calories": 290,
            "protein": 19,
            "carbs": 42,
            "fat": 6,
            "items": [
                {"name": "한끼 군고구마/호박고구마 파우치", "spec": "1팩 120g", "cal": 140, "protein": 2, "coupang_keyword": "아이스 군고구마 120g"},
                {"name": "무항생제 신선 구운란", "spec": "2개 (100g)", "cal": 110, "protein": 13, "coupang_keyword": "구운란 소포장"},
                {"name": "데일리 컷팅 샐러드믹스 + 발사믹", "spec": "1팩 80g", "cal": 40, "protein": 4, "coupang_keyword": "로켓프레시 샐러드 채소"}
            ]
        },
        {
            "id": "combo_tofu_steak_oatmeal",
            "name": "🌱 고단백 두부 스테이크 & 오트밀 리조또 세트",
            "desc": "속 편한 100% 식물성 클린 식단: 두부 스테이크 + 롤드오츠 30g + 방울토마토",
            "calories": 310,
            "protein": 24,
            "carbs": 33,
            "fat": 8,
            "items": [
                {"name": "풀무원 직화 두부 스테이크", "spec": "1팩 100g", "cal": 145, "protein": 15, "coupang_keyword": "두부 스테이크"},
                {"name": "퀘이커 퀵오트밀 (온수 2분)", "spec": "30g", "cal": 115, "protein": 4, "coupang_keyword": "오트밀 소용량"},
                {"name": "신선 대추방울토마토", "spec": "1컵 (120g)", "cal": 50, "protein": 5, "coupang_keyword": "대추방울토마토 500g"}
            ]
        },
        {
            "id": "combo_beef_brownrice_veggie",
            "name": "🥩 소고기 우둔살 슬라이스 & 발아현미밥 팩",
            "desc": "양질의 크레아틴과 철분: 지방 2% 소고기 우둔살 100g + 1/2 공기 현미밥 + 쌈채소",
            "calories": 340,
            "protein": 31,
            "carbs": 35,
            "fat": 6,
            "items": [
                {"name": "맛있닭 소고기 우둔살 볼/슬라이스", "spec": "1팩 100g", "cal": 135, "protein": 24, "coupang_keyword": "소우둔살 슬라이스 100g"},
                {"name": "햇반 발아현미밥 작은공기", "spec": "130g (1/2 분량)", "cal": 170, "protein": 4, "coupang_keyword": "발아현미밥 작은공기"},
                {"name": "모둠 쌈채소 믹스 (깻잎/상추/치커리)", "spec": "1팩 60g", "cal": 35, "protein": 3, "coupang_keyword": "모둠 쌈채소 로켓프레시"}
            ]
        }
    ]

    # 끼니별 편성
    target_meals = str(meal_change_target)
    recommended_plan = {}
    if '아침' in target_meals or '전체' in target_meals:
        recommended_plan['아침'] = raw_food_combos[1]
    if '점심' in target_meals or '전체' in target_meals or '점심+저녁' in target_meals:
        recommended_plan['점심'] = raw_food_combos[0]
    if '저녁' in target_meals or '전체' in target_meals or '점심+저녁' in target_meals:
        recommended_plan['저녁'] = raw_food_combos[3]

    if not recommended_plan:
        recommended_plan['점심'] = raw_food_combos[0]
        recommended_plan['저녁'] = raw_food_combos[1]

    return {
        "bmr": bmr,
        "tdee": tdee,
        "target_calories": target_cal,
        "calorie_deficit": tdee - target_cal,
        "protein_g": protein_g,
        "protein_cal": protein_cal,
        "protein_pct": protein_pct,
        "carbs_g": carbs_g,
        "carbs_cal": carbs_cal,
        "carbs_pct": carbs_pct,
        "fat_g": fat_g,
        "fat_cal": fat_cal,
        "fat_pct": fat_pct,
        "recommended_combos": raw_food_combos,
        "meal_plan": recommended_plan
    }

if __name__ == '__main__':
    # 간단 검증 테스트 (30세 남성, 175cm, 75kg -> 68kg 목표, 좌식+주3회 운동)
    res = calculate_diet_macro(30, "남성", 175, 75, 68, "좌식 생활", "웨이트", "주 3~4회", "1시간", "점심+저녁")
    print(f"BMR: {res['bmr']} kcal | TDEE: {res['tdee']} kcal | Target: {res['target_calories']} kcal")
    print(f"단백질: {res['protein_g']}g ({res['protein_pct']}%) | 탄수화물: {res['carbs_g']}g ({res['carbs_pct']}%) | 지방: {res['fat_g']}g ({res['fat_pct']}%)")
    print("추천 끼니:", list(res['meal_plan'].keys()))
