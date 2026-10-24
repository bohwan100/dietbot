#!/usr/bin/env python3
"""
다이어트봇 (DietBot) - 식재료 맞춤 보관 & 소분 가이드 엔진 (storage_engine.py)
- 구매하는 식재료(products)를 기반으로 유동적 보관 가이드 실시간 생성
- 브랜드명(풀무원, 오뚜기 등) 및 불필요한 수식어/형용사(신선한, 손질 깐 등) 완전 배제
- 1인 가구 소형 냉장고/자취생 맞춤형 실전 소분 꿀팁 & 상함 판별법 제공
"""

import re
import json

# 제거 대상 브랜드명 리스트
BRANDS = [
    '순창', '샘표', '백설', '청정원', '오뚜기', 'CJ', '해찬들', '곰곰', '하림', '동원',
    '목우촌', '이금기', '종가집', '롯데', '풀무원', '한돈', '도드람한돈', '도드람',
    '기꼬만', '바릴라', '폰타나', '데체코', '스키피', '하이디라오', '자연담은', '속초',
    '천일식품', '삼립', '삼광', '사비니 타르투피', '사비니', '크래프트', 'S&B', '사옹원', '노르웨이',
    '용수당면', '칠레산', '호주산', '미국산', '국산', '국내산', '친환경', '해태',
    '피코크', '노브랜드', '비비고', '오리온', '매일', '서울우유', '루어팍', '임금님표이천', '임금님표', '이탈리아'
]

# 제거 대상 형용사 및 수식어 리스트 (브랜드/품질 마케팅 수식어)
ADJECTIVES = [
    '무항생제 신선', '시원하고 깔끔한', '신선하고 깔끔한', '손질 깐', '튀겨나온 바삭',
    '신선한', '신선', '싱싱한', '맛있는', '알찬', '생생', '깔끔한', '정성가득',
    '손질', '절단', '깐', '햇', '무항생제', '인큐', '부침찌개', '찰', '태양초',
    '금F3', '금F', '신안섬보배', '고소한', '클래식', '팬더', '농축', '사과',
    '하얀', '엑스트라버진', '저염', '바삭', '크리미', '정통', '참깨', '골드',
    '약간매운맛', '1등급', '1인분', '바로구이', '가염', '홀', '다듬은', '세척',
    '흙', '생', '횟감/구이용', '구이용', '에어프라이어', '생면식감', '999', '상등급',
    '2024년', '햅', '재래식', '혼'
]

# 식재료 정밀 마스터 보관 사전 (78종 전 식재료 커버)
STORAGE_KNOWLEDGE_BASE = {
    # 🥬 1. 신선 채소 & 두부 & 계란
    '대파': {
        'name': '대파',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉동실 소분 / 야채칸',
        'duration': '냉동 1~2개월 / 냉장 7일',
        'tip': '세척 후 키친타월로 물기를 완전히 말린 뒤 송송 썰어 밀폐용기에 담아 냉동실에 얼려두면, 요리할 때 한 줌씩 바로 꺼내 파기름과 찌개에 쓰기 가장 좋습니다.',
        'spoilage': '진액 발생, 시큼한 냄새, 잎이 누렇게 물러짐'
    },
    '양파': {
        'name': '양파',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '서늘한 상온 / 냉장 야채실',
        'duration': '상온 2~3주 / 냉장 10일',
        'tip': '통풍이 잘되는 그늘진 곳에 서로 닿지 않게 보관하세요. 껍질을 깐 양파는 키친타월로 감싼 뒤 랩으로 밀봉해 냉장 야채실에 넣으면 물러지지 않습니다.',
        'spoilage': '속이 검게 변색, 물렁거리며 쉰내 발생'
    },
    '감자': {
        'name': '감자',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '상온 그늘 (절대 냉장 금지!)',
        'duration': '상온 3~4주',
        'tip': '★감자는 절대 냉장고에 넣지 마세요★ (저온에서 녹말이 당분화되어 조리 시 발암물질 생성). 박스에 신문지를 깔고 사과 1알을 넣어두면 싹트는 것을 방지합니다.',
        'spoilage': '표면 초록 변색(솔라닌 독소), 싹 자람 및 쭈글거림'
    },
    '두부': {
        'name': '두부',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 안쪽',
        'duration': '개봉 후 7~10일 (생수 침지 시)',
        'tip': '남은 두부는 밀폐용기에 담고 두부가 잠길 정도로 깨끗한 생수를 부은 뒤 소금 0.3t를 살짝 섞어주세요. 2일에 한 번 물을 갈아주면 10일 넘게 처음 맛 그대로 신선합니다.',
        'spoilage': '표면 미끌거리는 점액질, 시큼한 신맛과 악취'
    },
    '순두부': {
        'name': '순두부',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 안쪽',
        'duration': '유통기한 준수 (약 2주)',
        'tip': '튜브 형태 그대로 차가운 냉장실 안쪽에 보관하세요. 충격을 받으면 튜브가 터질 수 있으니 벽면에 안전하게 눕혀둡니다.',
        'spoilage': '포장 튜브 팽창, 국물 탁해짐 및 시큼한 냄새'
    },
    '계란': {
        'name': '계란 (달걀)',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 안쪽 (문쪽 X)',
        'duration': '냉장 30~40일',
        'tip': '계란은 물로 씻으면 보호막(큐티클)이 파괴되므로 씻지 말고, 뾰족한 쪽이 아래로 둥근 쪽(숨구멍)이 위로 향하게 보관하세요. 문쪽 선반은 흔들림과 온도 변화가 심하므로 냉장실 안쪽에 두는 것이 좋습니다.',
        'spoilage': '물에 둥둥 뜨거나 노른자가 퍼져 악취 발생'
    },
    '애호박': {
        'name': '애호박',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 7~10일',
        'tip': '비닐을 벗기지 않은 상태로 키친타월에 한 번 감싸서 야채실에 보관하세요. 쓰고 남은 단면은 랩으로 공기가 통하지 않게 팽팽하게 감싸서 산화 방지합니다.',
        'spoilage': '씨 부분이 갈색으로 물러지며 표면 끈적임'
    },
    '양배추': {
        'name': '양배추',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 3~4주 (심지 제거 시)',
        'tip': '양배추 가운데 딱딱한 심지를 칼로 도려내고, 그 자리에 물에 젖은 키친타월을 채워 넣은 뒤 랩으로 꽁꽁 싸면 한 달 내내 시들지 않고 갓 산 것처럼 아삭합니다.',
        'spoilage': '잎이 검게 변색되고 시큼하고 퀴퀴한 냄새'
    },
    '알배기배추': {
        'name': '알배기배추',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 2~3주',
        'tip': '밑동을 자르지 말고 겉잎부터 한 장씩 뜯어 쓰며, 신문지나 키친타월로 감싸 비닐팩에 넣어 세워서 보관하세요.',
        'spoilage': '잎 끝이 갈색으로 마르고 물러짐'
    },
    '청경채': {
        'name': '청경채',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 5~7일',
        'tip': '씻지 않은 상태로 키친타월로 감싸 지퍼백에 넣어 야채실에 세워 보관하세요. 조리 직전에 씻어 밑동을 자릅니다.',
        'spoilage': '잎이 누렇게 변색되고 줄기가 물러짐'
    },
    '콩나물': {
        'name': '콩나물',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실',
        'duration': '냉장 5~7일 (물 침지 시)',
        'tip': '봉지째 두면 3일 만에 상합니다! 밀폐용기에 콩나물을 담고 찬물을 가득 채워 냉장 보관하며, 2일마다 물을 갈아주세요.',
        'spoilage': '줄기가 갈색으로 무르고 물 생기며 악취'
    },
    '숙주나물': {
        'name': '숙주나물',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실',
        'duration': '냉장 3~4일',
        'tip': '수분이 많아 콩나물보다 쉽게 상하므로 구매 후 3일 내 우선 조리하세요. 밀폐용기에 찬물을 붓고 담가두면 신선도가 2일 더 연장됩니다.',
        'spoilage': '갈색으로 변색, 퀴퀴한 냄새 및 짓무름'
    },
    '팽이버섯': {
        'name': '팽이버섯',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 10~14일',
        'tip': '포장을 뜯지 않은 상태로 보관하세요. 물에 절대 씻지 말고, 조리 직전 밑동만 잘라내어 사용합니다.',
        'spoilage': '포장 내 수분이 고이고 갈색 변색 및 끈적임'
    },
    '표고버섯': {
        'name': '표고버섯',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실 / 냉동',
        'duration': '냉장 7일 / 냉동 1개월',
        'tip': '기둥을 떼어내고 갓의 주름이 아래로 향하게 키친타월을 깐 밀폐용기에 담아 보관하세요. 썰어서 냉동 보관해도 좋습니다.',
        'spoilage': '표면이 검게 변하고 끈적이는 점액질 발생'
    },
    '가지': {
        'name': '가지',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '서늘한 상온 / 냉장 야채실',
        'duration': '상온 3~4일 / 냉장 5일',
        'tip': '가지는 저온 장애를 겪기 쉬우므로 키친타월로 1개씩 감싼 뒤 비닐팩에 넣어 야채실에 보관하세요.',
        'spoilage': '표면이 쭈글거리고 물러지며 속이 갈색 변색'
    },
    '파프리카': {
        'name': '파프리카',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 10~14일',
        'tip': '물기를 완전히 닦고 꼭지를 떼지 않은 채 랩으로 1개씩 밀착 포장해 보관합니다.',
        'spoilage': '표면이 쭈글쭈글해지고 꼭지 주변 곰팡이'
    },
    '샐러드 채소': {
        'name': '샐러드 채소',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 5~7일',
        'tip': '밀폐용기 바닥에 키친타월을 깔고 잎채소를 넣은 뒤 뚜껑을 닫아 냉장 보관하면 습기가 흡수되어 짓무르지 않습니다.',
        'spoilage': '잎이 투명하게 물러지고 진액 발생'
    },
    '무': {
        'name': '무',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 야채실',
        'duration': '냉장 2주',
        'tip': '자른 단면에서 수분이 증발하면 바람이 들므로, 단면에 키친타월을 대고 랩으로 단단히 밀착 포장하여 야채칸에 세워서 보관합니다.',
        'spoilage': '스펀지처럼 푸석해지거나 무르고 곰팡이 발생'
    },
    '마늘': {
        'name': '마늘 (깐마늘/통마늘)',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 밀폐 / 다져서 냉동',
        'duration': '냉장 2주 / 냉동 6개월',
        'tip': '밀폐용기 바닥에 설탕이나 키친타월을 깔고 깐마늘을 넣으면 수분이 차단되어 싹이 나지 않습니다. 남으면 다져서 냉동 소분하세요.',
        'spoilage': '물렁거림, 곰팡이 및 변색'
    },
    '김치': {
        'name': '김치 (배추김치)',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 가장 차가운 안쪽',
        'duration': '냉장 2~3개월',
        'tip': '김치는 공기와 닿으면 하얀 골마지가 생기므로, 숟가락으로 꾹꾹 눌러 김치 국물 속에 잠기게 하고 표면을 위생 비닐로 밀착 덮어주세요.',
        'spoilage': '두꺼운 흰 골마지, 톡 쏘는 부패성 악취'
    },

    # 🥩 2. 신선 육류 & 생선 & 빵
    '돼지 등심': {
        'name': '돼지 등심',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 2일 / 장기 시 냉동',
        'duration': '냉장 2~3일 / 냉동 2개월',
        'tip': '키친타월로 핏물을 닦고 1회분씩 랩으로 밀착 포장하여 보관하세요.',
        'spoilage': '회갈색 변색, 시큼한 악취, 끈적임'
    },
    '통삼겹살': {
        'name': '통삼겹살',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 3일 / 냉동실 소분',
        'duration': '냉장 3일 / 냉동 2~3개월',
        'tip': '겉면 핏물을 닦은 후 식용유나 올리브유를 겉에 살짝 바르고 랩으로 팽팽하게 감싸면 냉동 번(동결건조 현상)이 방지됩니다.',
        'spoilage': '악취, 끈적이는 진액, 누런 변색'
    },
    '소고기 부채살': {
        'name': '소고기 부채살',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 2~3일 / 냉동실 소분',
        'duration': '냉장 2~3일 / 냉동 2개월',
        'tip': '핏물을 꼼꼼히 닦고 올리브유를 겉면에 얇게 발라 랩으로 밀착 포장하면 산화와 수분 손실을 완벽 차단합니다.',
        'spoilage': '시큼하고 쉰 냄새, 표면 끈적임'
    },
    '생연어': {
        'name': '생연어',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 가장 차가운 곳',
        'duration': '냉장 1~2일 (즉시 섭취 권장)',
        'tip': '도착 당일이나 다음 날까지 드시고, 남은 것은 미림과 소금으로 살짝 간하여 랩핑 후 냉동실에 얼려 구이용으로 쓰세요.',
        'spoilage': '비린내 심화, 살이 부서지고 점액질'
    },
    '베이컨': {
        'name': '베이컨',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장 5일 / 냉동 2개월',
        'duration': '개봉 후 냉장 5일 / 냉동 2개월',
        'tip': '종이호일 위에 베이컨을 1~2줄씩 얹고 돌돌 말아서 지퍼백에 넣어 냉동하면 필요할 때 한 줄씩 쏙쏙 빠집니다.',
        'spoilage': '끈적임, 쉰 냄새, 회색 변색'
    },
    '바게트': {
        'name': '바게트 빵',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉동실 밀폐 (절대 냉장 금지!)',
        'duration': '냉동 1개월',
        'tip': '빵은 냉장실에 넣으면 노화(수분 증발)가 급속도로 일어납니다! 먹을 만큼만 남기고 즉시 1회분씩 랩핑하여 냉동실에 얼리세요.',
        'spoilage': '푸른 곰팡이, 쉰내, 딱딱해짐'
    },
    '햄버거번': {
        'name': '햄버거번',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉동실 밀폐',
        'duration': '냉동 1개월',
        'tip': '1개씩 랩으로 감싸 지퍼백에 넣어 냉동실에 보관하고, 먹기 전 실온에 20분 꺼내두거나 마른 팬에 살짝 구워드세요.',
        'spoilage': '표면 곰팡이, 퀴퀴한 냄새'
    },
    '꽃빵': {
        'name': '꽃빵',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉동실 밀폐',
        'duration': '냉동 2개월',
        'tip': '남은 꽃빵은 지퍼백에 밀봉해 냉동 보관하고, 찜기에 5분간 찌거나 전자레인지에 물 한 컵과 함께 1분 돌리면 갓 찐 것처럼 촉촉합니다.',
        'spoilage': '곰팡이, 반죽 변색'
    },
    '중화 생면': {
        'name': '생면 (중화면/라멘)',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 / 냉동실',
        'duration': '냉장 유통기한 준수 / 냉동 1개월',
        'tip': '생면은 덧가루가 묻어있어 습기에 약합니다. 미개봉 상태로 냉장 보관하고, 장기 보관 시 1인분씩 밀봉해 냉동실에 얼립니다.',
        'spoilage': '표면 곰팡이, 반죽이 축축하게 뭉개짐'
    },

    # ❄️ 3. 냉동 육류 & 해물 & 냉동 간편식
    '돼지 앞다리살': {
        'name': '돼지 앞다리살 (불고기용)',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '도착 즉시 키친타월로 가볍게 핏물을 닦은 뒤, 1회분(120~150g)씩 랩 위에 얇게 펴서 쌉니다. 지퍼백에 책처럼 세워 꽂으면 찾기 쉽고 해동이 초고속입니다.',
        'spoilage': '해동 시 시큼한 악취, 끈적이는 점액질'
    },
    '우삼겹': {
        'name': '우삼겹',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '돌돌 말린 채 뭉쳐 얼리면 떼어내기 힘듭니다. 1회분(120g)씩 소분해 납작하게 얼려두면 조리 시 팬에 바로 털어 넣을 수 있습니다.',
        'spoilage': '누런 기름 산패, 역한 쩐내'
    },
    '돼지고기 다짐육': {
        'name': '돼지고기 다짐육',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 2개월',
        'tip': '지퍼백에 얇고 넓적하게 편 뒤 젓가락으로 4등분 바둑판 격자를 눌러 얼리세요. 요리할 때 필요한 조각만 똑똑 부러뜨려 쓰면 최고입니다.',
        'spoilage': '검붉거나 회색 변색, 시큼한 부패취'
    },
    '소고기 다짐육': {
        'name': '소고기 다짐육',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 2개월',
        'tip': '지퍼백에 얇게 펴서 젓가락으로 격자를 내어 냉동실에 얼리면 해동 없이 볶음밥과 파스타에 바로 투입 가능합니다.',
        'spoilage': '시큼한 냄새, 미끌거리는 점액질'
    },
    '닭다리살': {
        'name': '닭다리살 (순살)',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '도착 즉시 키친타월로 물기를 닦은 뒤, 1장씩 랩으로 꼼꼼히 싸서 냉동 보관하세요. 조리 전날 냉장실로 옮겨 저온 해동하면 육즙 손실이 없습니다.',
        'spoilage': '미끌거리는 점액질, 시큼한 닭 비린내'
    },
    '닭가슴살': {
        'name': '닭가슴살',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '1덩이씩 랩으로 밀착 포장해 지퍼백에 보관하세요. 조리 30분 전 찬물에 담가 해동하면 촉촉함을 유지할 수 있습니다.',
        'spoilage': '표면 끈적임, 황변 및 쉰내'
    },
    '해물 믹스': {
        'name': '해물 모둠믹스',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '해동 후 재냉동하면 비린내가 심해집니다. 냉동 상태 그대로 지퍼백에 보관하고, 조리 직전 찬물에 2분간 헹궈 바로 조리하세요.',
        'spoilage': '누런 변색, 심한 비린 악취'
    },
    '새우살': {
        'name': '새우살 (칵테일새우)',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '얼어있는 상태 그대로 보관하고 필요한 알수만큼만 꺼내 찬물에 1분간 담가 해동 후 키친타월로 물기를 닦고 쓰세요.',
        'spoilage': '살이 물러지고 심한 암모니아 악취'
    },
    '바지락살': {
        'name': '자숙 바지락살',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '냉동 보관하며 찌개나 파스타 조리 시 해동 없이 그대로 넣어 끓입니다.',
        'spoilage': '살이 흐물거리고 역한 비린내'
    },
    '우동면': {
        'name': '우동면 (냉동 사누끼)',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '냉동실',
        'duration': '냉동 6개월',
        'tip': '해동할 필요 없이 끓는 물에 냉동 상태 그대로 넣어 1분만 저어주면 탱글탱글하게 풀립니다.',
        'spoilage': '성에가 두껍게 끼고 면이 바스러짐'
    },
    '등심 돈까스': {
        'name': '등심 돈까스',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '지퍼백에 겹치지 않게 보관하고, 에어프라이어에 해동 없이 냉동 상태 그대로 180도 12~15분 조리하면 가장 바삭합니다.',
        'spoilage': '기름 쩐내, 성에 과다 발생'
    },
    '치킨텐더': {
        'name': '치킨텐더',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '개봉 후 지퍼백에 밀봉해 냉동 보관하고, 에어프라이어에 180도 10분 조리합니다.',
        'spoilage': '기름 쩐내, 튀김옷 눅눅함'
    },
    '새우튀김': {
        'name': '왕새우튀김',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '소형 냉동실',
        'duration': '냉동 3개월',
        'tip': '지퍼백에 담아 냉동실에 보관하고 에어프라이어 180도 10~12분 조리합니다.',
        'spoilage': '기름 쩐내, 성에 누적'
    },
    '명란젓': {
        'name': '명란젓',
        'category': 'frozen',
        'categoryLabel': '❄️ 냉동식품',
        'location': '냉동실 소분',
        'duration': '냉동 3개월 / 냉장 5일',
        'tip': '1개씩 랩으로 개별 포장하여 지퍼백에 담아 냉동 보관하세요. 조리 10분 전 실온에 꺼내두면 칼로 껍질만 쏙 벗기기 쉽습니다.',
        'spoilage': '시큼한 냄새, 표면 끈적이는 진액'
    },

    # 🧂 4. 조미료 & 가루류 & 소스 & 팬트리
    '고추장': {
        'name': '고추장',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 1년',
        'tip': '물 묻은 숟가락이 닿으면 곰팡이가 피어납니다. 항상 마른 숟가락으로 퍼내고, 윗면을 평평하게 다진 뒤 랩을 표면에 밀착시켜 덮어두면 오랫동안 깔끔합니다.',
        'spoilage': '표면 푸른·검은 곰팡이, 퀴퀴한 변질 악취'
    },
    '된장': {
        'name': '된장',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 1년',
        'tip': '마른 숟가락으로 사용하고 표면을 비닐이나 랩으로 꼭 밀착하여 덮어주면 마르거나 곰팡이가 피지 않습니다.',
        'spoilage': '표면 검은 곰팡이, 퀴퀴한 군내'
    },
    '진간장': {
        'name': '진간장',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 권장',
        'duration': '개봉 후 6개월~1년',
        'tip': '간장은 개봉 후 공기와 접촉하면 맛과 향이 산화됩니다. 냉장고 문쪽이나 서늘한 곳에 두고 뚜껑을 꼭 닫아 보관하세요.',
        'spoilage': '표면 흰색 막 형성, 퀴퀴한 군내 및 침전물'
    },
    '굴소스': {
        'name': '굴소스',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 즉시 100% 냉장실 필수',
        'duration': '개봉 후 냉장 6개월',
        'tip': '★굴소스는 개봉 전엔 상온이지만 개봉 즉시 100% 냉장 보관해야 합니다★ 방부제가 거의 없어 상온에 두면 곰팡이가 쉽게 핍니다. 입구를 키친타월로 닦아 뚜껑을 닫으세요.',
        'spoilage': '병 입구 흰 곰팡이, 물 분리 및 신 냄새'
    },
    '고춧가루': {
        'name': '고춧가루',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '냉동실 / 냉장실 밀폐',
        'duration': '냉동 1년 / 냉장 6개월',
        'tip': '고춧가루를 상온에 두면 곰팡이(아플라톡신 발암물질)가 번식하기 쉽습니다. 지퍼백에 담아 냉동실에 얼려두면 붉은 색감과 매콤한 풍미가 1년 내내 그대로 유지됩니다.',
        'spoilage': '검붉은 변색, 덩어리 굳음 및 곰팡이 냄새'
    },
    '식용유': {
        'name': '식용유',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 어두운 곳 (가스레인지 옆 X)',
        'duration': '상온 1년',
        'tip': '가스레인지 열기 바로 옆에 두면 기름이 쉽게 산패됩니다. 열기와 햇빛이 닿지 않는 싱크대 하부장에 보관하세요.',
        'spoilage': '끈적거림 심화, 역한 쩐내 및 거품 발생'
    },
    '올리브유': {
        'name': '올리브유',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 그늘 (절대 냉장 금지!)',
        'duration': '개봉 후 6개월~1년',
        'tip': '올리브유를 냉장고에 넣으면 버터처럼 하얗게 굳어버립니다. 서늘하고 어두운 상온 찬장에 보관하세요.',
        'spoilage': '역한 산패 쩐내, 색상 탁해짐'
    },
    '참기름': {
        'name': '참기름',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 그늘 (절대 냉장 금지!)',
        'duration': '상온 6~9개월',
        'tip': '참기름은 냉장 보관하면 고소한 향이 날아가고 굳어버립니다. 신문지나 은박지로 병을 감싸 싱크대 안쪽에 보관하세요.',
        'spoilage': '기름 쩐내, 고소한 풍미 상실'
    },
    '설탕': {
        'name': '설탕',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 무기한 (수분 차단)',
        'tip': '습기를 먹으면 단단하게 굳습니다. 밀폐용기에 담아 수분을 차단해 보관하세요.',
        'spoilage': '수분 침투로 굳음, 이물질 유입'
    },
    '소금': {
        'name': '소금 (꽃소금)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 무기한 (수분 차단)',
        'tip': '습기를 먹으면 굳습니다. 볶은 쌀알 몇 알이나 실리카겔을 함께 넣어두면 보송보송하게 유지됩니다.',
        'spoilage': '수분 침투로 굳음'
    },
    '후추': {
        'name': '후추',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 1~2년',
        'tip': '가스레인지 열기와 수증기가 닿지 않는 건조한 양념장에 보관하세요.',
        'spoilage': '향 소실, 눅눅함'
    },
    '스팸': {
        'name': '스팸',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 서랍 / 개봉 후 밀폐용기 냉장',
        'duration': '상온 3~5년 (개봉 후 냉장 3일)',
        'tip': '개봉하지 않은 캔은 상온 보관 최강입니다. 캔을 따고 남은 것은 캔 채로 두지 말고 유리/플라스틱 밀폐용기로 옮겨 담아 냉장 보관하세요.',
        'spoilage': '캔 팽창, 녹 발생, 개봉 시 시큼한 악취'
    },
    '참치캔': {
        'name': '참치캔',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 서랍 / 개봉 후 밀폐용기 냉장',
        'duration': '상온 3~5년 (개봉 후 즉시 소진)',
        'tip': '남은 참치는 기름째 밀폐용기에 담아 냉장 보관하고 2일 내 드세요.',
        'spoilage': '캔 변형 및 개봉 시 시큼한 악취'
    },
    '케첩': {
        'name': '토마토 케첩',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 3~6개월',
        'tip': '개봉 후에는 뚜껑을 아래로 향하게 세워 냉장 보관하면 짤 때 붉은 물이 튀지 않고 내용물이 깔끔하게 나옵니다.',
        'spoilage': '물 분리, 갈색 변색 및 톡 쏘는 신 냄새'
    },
    '마요네즈': {
        'name': '마요네즈',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 문쪽 선반',
        'duration': '개봉 후 냉장 2~3개월',
        'tip': '너무 차가운 곳에 두면 기름과 식초가 분리되므로 냉장고 문쪽 선반에 보관하세요.',
        'spoilage': '기름 분리, 시큼한 변질 악취'
    },
    '스파게티면': {
        'name': '스파게티면 (파스타면)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 1~2년',
        'tip': '개봉 후 전용 파스타 보관통이나 지퍼백에 밀봉해 습기를 차단하여 보관하세요.',
        'spoilage': '벌레 침투, 눅눅함 및 곰팡이'
    },
    '중국당면': {
        'name': '중국당면',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 1년',
        'tip': '개봉 후 집게로 집어 상온에 보관하며, 조리 전 최소 6시간 찬물에 불려 사용합니다.',
        'spoilage': '벌레 유입, 곰팡이'
    },
    '파스타소스': {
        'name': '파스타 소스 (토마토/볼로네제)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 5~7일',
        'tip': '토마토 소스는 개봉 후 곰팡이가 매우 빨리 핍니다. 남은 소스는 1회분씩 지퍼백에 담아 냉동실에 얼려두면 한 달간 안전합니다.',
        'spoilage': '표면 흰 곰팡이, 톡 쏘는 신 냄새'
    },
    '카레가루': {
        'name': '카레가루',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '밀봉 후 냉장 / 냉동',
        'duration': '개봉 후 밀봉 6개월',
        'tip': '쓰고 남은 봉지는 입구를 꼭 집은 뒤 지퍼백에 한 번 더 넣어 냉장 보관하면 습기로 굳지 않습니다.',
        'spoilage': '습기로 돌처럼 굳음 및 눅눅한 냄새'
    },
    '카레': {
        'name': '고형 카레',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 밀폐 냉장실',
        'duration': '개봉 후 냉장 3개월',
        'tip': '남은 조각은 랩으로 감싼 뒤 밀폐용기에 담아 냉장 보관하세요.',
        'spoilage': '표면 기름 산화, 곰팡이'
    },
    '감자전분': {
        'name': '감자전분',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 1년',
        'tip': '지퍼백에 밀봉해 습기가 없는 싱크대 안쪽에 보관하세요.',
        'spoilage': '습기로 굳음, 벌레 유입'
    },
    '맛술': {
        'name': '맛술 (미림)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 서늘한 곳 / 개봉 후 냉장',
        'duration': '상온 1년',
        'tip': '직사광선을 피해 서늘한 곳에 보관하고 뚜껑을 꼭 닫아 알코올 증발을 막으세요.',
        'spoilage': '부유물 발생, 변색'
    },
    '식초': {
        'name': '식초',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 서늘한 곳',
        'duration': '상온 1~2년',
        'tip': '산도가 높아 상온에서 변질되지 않습니다. 뚜껑만 잘 닫아두세요.',
        'spoilage': '침전물 및 혼탁'
    },
    '쯔유': {
        'name': '쯔유',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 2~3개월',
        'tip': '가쓰오부시 육수가 들어가 개봉 후 상온에 두면 상합니다. 반드시 냉장실에 두고 뚜껑을 꼭 닫아주세요.',
        'spoilage': '거품 발생, 신 냄새, 침전물'
    },
    '치킨스톡': {
        'name': '치킨스톡',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 6개월',
        'tip': '입구를 깨끗이 닦아 뚜껑을 닫고 냉장 보관하세요.',
        'spoilage': '병 입구 곰팡이, 분리'
    },
    '돈까스 소스': {
        'name': '돈까스 소스 (스테이크소스)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실',
        'duration': '개봉 후 냉장 6개월',
        'tip': '개봉 후 뚜껑을 꼭 닫아 냉장실 문쪽에 보관하세요.',
        'spoilage': '표면 곰팡이, 시큼한 냄새'
    },
    '데미글라스 소스': {
        'name': '데미글라스 소스',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실',
        'duration': '개봉 후 냉장 1개월 / 소분 냉동',
        'tip': '남은 소스는 얼음틀이나 지퍼백에 1회분씩 소분해 냉동하면 오래 쓸 수 있습니다.',
        'spoilage': '곰팡이, 쉰내'
    },
    '마라샹궈 소스': {
        'name': '마라샹궈 소스',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 밀봉 냉장',
        'duration': '개봉 후 냉장 1개월',
        'tip': '개봉한 팩은 밀폐용기에 담아 냉장 보관하고 1개월 내 사용하세요.',
        'spoilage': '기름 산패, 곰팡이'
    },
    '버터': {
        'name': '버터',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '냉장실 / 소분 냉동',
        'duration': '냉장 1개월 / 냉동 6개월',
        'tip': '10g씩 큐브 모양으로 썰어 종이호일로 싼 뒤 밀폐용기에 담아 냉동실에 얼려두면 요리할 때 1알씩 꺼내 쓰기 최고입니다.',
        'spoilage': '표면 진노란색 산화 변색, 퀴퀴한 냄새'
    },
    '바질페스토': {
        'name': '바질페스토',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실',
        'duration': '개봉 후 냉장 1~2주',
        'tip': '올리브유가 윗면을 덮도록 평평하게 누르고 올리브유 1스푼을 덧뿌려 산소를 차단하면 곰팡이를 완벽 차단합니다.',
        'spoilage': '표면 곰팡이, 거무스름한 변색'
    },
    '파마산 치즈가루': {
        'name': '파마산 치즈가루',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 / 냉동실',
        'duration': '개봉 후 냉장 3개월 / 냉동 6개월',
        'tip': '습기를 흡수하면 굳으므로 뚜껑을 꼭 닫고 냉장 보관하세요.',
        'spoilage': '곰팡이 발생, 덩어리 굳음'
    },
    '생와사비': {
        'name': '생와사비',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실',
        'duration': '개봉 후 냉장 6개월',
        'tip': '뚜껑을 꽉 닫아 냉장 보관하고 공기 접촉을 최소화하세요.',
        'spoilage': '매운 향 소실, 변색'
    },
    '땅콩버터': {
        'name': '땅콩버터',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 서늘한 곳 / 개봉 후 냉장',
        'duration': '개봉 후 6개월',
        'tip': '기름이 뜰 수 있으니 깨끗한 숟가락으로 저어서 사용하세요.',
        'spoilage': '기름 쩐내, 곰팡이'
    },
    '페페론치노': {
        'name': '페페론치노',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 건조한 곳',
        'duration': '상온 1~2년',
        'tip': '건조 고추이므로 습기만 차단하면 오래 보관됩니다.',
        'spoilage': '곰팡이, 변색'
    },
    '트러플 오일': {
        'name': '트러플 오일',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 어두운 찬장',
        'duration': '개봉 후 6개월',
        'tip': '향이 날아가지 않게 뚜껑을 꼭 닫고 직사광선을 피해 보관하세요.',
        'spoilage': '트러플 향 소실, 기름 쩐내'
    },
    '갈아만든 배': {
        'name': '갈아만든 배 (배 음료)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '상온 서랍 / 개봉 후 냉장',
        'duration': '상온 1년 (개봉 후 즉시 소진)',
        'tip': '고기 연육 및 양념용입니다. 남은 음료는 컵에 따라 즉시 마시거나 밀폐용기에 냉장 보관하세요.',
        'spoilage': '캔 팽창, 신맛'
    },
    '크림 파스타소스': {
        'name': '크림 파스타소스',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '개봉 후 냉장실 필수',
        'duration': '개봉 후 냉장 3~5일',
        'tip': '유제품이 포함되어 있어 개봉 후 빠르게 상합니다. 3일 내 소진하거나 1회분씩 소분하여 냉동 보관하세요.',
        'spoilage': '표면 곰팡이, 쉰내, 유청 분리 현상'
    },
    '쌀': {
        'name': '쌀 (백미)',
        'category': 'seasoning',
        'categoryLabel': '🧂 조미료 & 팬트리',
        'location': '서늘한 상온 / 냉장 야채실',
        'duration': '상온 3~6개월 (직사광선 차단)',
        'tip': '포대째 두면 쌀벌레가 생길 수 있습니다. 밀폐용기나 페트병에 담아 서늘한 그늘에 보관하거나 냉장고 야채칸에 넣으면 쌀벌레와 산화를 완벽 차단합니다.',
        'spoilage': '쌀벌레 발생, 곰팡이 및 묵은 쩐내'
    },
    '라멘': {
        'name': '생라멘 (돈코츠라면)',
        'category': 'fresh',
        'categoryLabel': '🥬 신선식품',
        'location': '냉장실 / 냉동실',
        'duration': '유통기한 준수 / 냉동 1개월',
        'tip': '생면은 덧가루가 있어 습기에 약하므로 미개봉 상태로 냉장 보관하고, 오래 둘 경우 면을 지퍼백에 밀봉해 냉동실에 얼려두세요.',
        'spoilage': '면 표면 곰팡이, 끈적임 및 쉰내'
    }
}

def clean_ingredient_name(raw_name):
    """
    브랜드명, 형용사, 수식어, 중량 괄호, 주차 태그, 보유재료 공제 태그를 완벽하게 제거하여
    순수 핵심 식재료명만 반환
    """
    s = raw_name.replace('[🏠 보유 재료 0원 공제]', '')
    # [1주차 신선보충], [4주차 파이널 보충] 등 제거
    s = re.sub(r'\[.*?\]', '', s)
    # 괄호 안 중량/수량 제거 (500g, 1kg 등)
    s = re.sub(r'\(.*?\)', '', s)

    # 브랜드명 제거 (긴 것부터)
    for b in sorted(BRANDS, key=len, reverse=True):
        s = s.replace(b, '')

    # 형용사 및 수식어 제거
    for a in sorted(ADJECTIVES, key=len, reverse=True):
        s = s.replace(a, '')

    # '순후추' -> '후추'
    s = s.replace('순후추', '후추')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def resolve_storage_entry(raw_name, cat_hint='fresh'):
    """
    구매 식재료명(raw_name)을 정밀 분석하여
    STORAGE_KNOWLEDGE_BASE 내의 최적 보관 카드 엔트리 매칭
    (브랜드명/형용사 제거 및 오매칭 방지 로직 적용)
    """
    n = raw_name

    # 1. 특정 소스류 & 팬트리 조미료 복합어 우선 매칭
    if '돈까스소스' in n or '돈까스 소스' in n: return STORAGE_KNOWLEDGE_BASE['돈까스 소스']
    if '마라샹궈' in n: return STORAGE_KNOWLEDGE_BASE['마라샹궈 소스']
    if '볼로네제' in n: return STORAGE_KNOWLEDGE_BASE['파스타소스']
    if '베이컨크림' in n: return STORAGE_KNOWLEDGE_BASE['크림 파스타소스']
    if '데미글라스' in n: return STORAGE_KNOWLEDGE_BASE['데미글라스 소스']
    if '갈아만든배' in n or '갈아만든 배' in n: return STORAGE_KNOWLEDGE_BASE['갈아만든 배']
    if '감자전분' in n or '전분' in n: return STORAGE_KNOWLEDGE_BASE['감자전분']
    if '스파게티' in n or '파스타면' in n: return STORAGE_KNOWLEDGE_BASE['스파게티면']
    if ('중국' in n and '당면' in n) or '넓적당면' in n: return STORAGE_KNOWLEDGE_BASE['중국당면']
    if '골든카레' in n or ('고형' in n and '카레' in n): return STORAGE_KNOWLEDGE_BASE['카레']
    if '카레' in n: return STORAGE_KNOWLEDGE_BASE['카레가루']
    if '와사비' in n: return STORAGE_KNOWLEDGE_BASE['생와사비']
    if '땅콩버터' in n: return STORAGE_KNOWLEDGE_BASE['땅콩버터']
    if '트러플' in n: return STORAGE_KNOWLEDGE_BASE['트러플 오일']
    if '올리브유' in n or '올리브 오일' in n: return STORAGE_KNOWLEDGE_BASE['올리브유']
    if '바질페스토' in n: return STORAGE_KNOWLEDGE_BASE['바질페스토']
    if '파마산' in n: return STORAGE_KNOWLEDGE_BASE['파마산 치즈가루']
    if '페페론치노' in n: return STORAGE_KNOWLEDGE_BASE['페페론치노']
    if '치킨스톡' in n: return STORAGE_KNOWLEDGE_BASE['치킨스톡']
    if '굴소스' in n: return STORAGE_KNOWLEDGE_BASE['굴소스']
    if '케첩' in n: return STORAGE_KNOWLEDGE_BASE['케첩']
    if '마요네즈' in n: return STORAGE_KNOWLEDGE_BASE['마요네즈']
    if '순후추' in n or '후추' in n: return STORAGE_KNOWLEDGE_BASE['후추']
    if '참기름' in n: return STORAGE_KNOWLEDGE_BASE['참기름']
    if '꽃소금' in n or '소금' in n: return STORAGE_KNOWLEDGE_BASE['소금']
    if '설탕' in n: return STORAGE_KNOWLEDGE_BASE['설탕']
    if '고춧가루' in n: return STORAGE_KNOWLEDGE_BASE['고춧가루']
    if '진간장' in n or '간장' in n: return STORAGE_KNOWLEDGE_BASE['진간장']
    if '고추장' in n: return STORAGE_KNOWLEDGE_BASE['고추장']
    if '된장' in n: return STORAGE_KNOWLEDGE_BASE['된장']
    if '식초' in n: return STORAGE_KNOWLEDGE_BASE['식초']
    if '쯔유' in n or '혼쯔유' in n: return STORAGE_KNOWLEDGE_BASE['쯔유']
    if '맛술' in n or '미림' in n: return STORAGE_KNOWLEDGE_BASE['맛술']
    if '버터' in n: return STORAGE_KNOWLEDGE_BASE['버터']
    if '스팸' in n: return STORAGE_KNOWLEDGE_BASE['스팸']
    if '참치' in n: return STORAGE_KNOWLEDGE_BASE['참치캔']
    if '쌀' in n or '햅쌀' in n: return STORAGE_KNOWLEDGE_BASE['쌀']

    # 2. 냉동 육류 & 해물 & 냉동 간편식 우선 매칭
    if '돈까스' in n: return STORAGE_KNOWLEDGE_BASE['등심 돈까스']
    if '치킨텐더' in n: return STORAGE_KNOWLEDGE_BASE['치킨텐더']
    if '새우튀김' in n: return STORAGE_KNOWLEDGE_BASE['새우튀김']
    if '앞다리' in n: return STORAGE_KNOWLEDGE_BASE['돼지 앞다리살']
    if '우삼겹' in n: return STORAGE_KNOWLEDGE_BASE['우삼겹']
    if '닭다리' in n: return STORAGE_KNOWLEDGE_BASE['닭다리살']
    if '닭가슴' in n: return STORAGE_KNOWLEDGE_BASE['닭가슴살']
    if '해물' in n: return STORAGE_KNOWLEDGE_BASE['해물 믹스']
    if '새우살' in n or '새우' in n: return STORAGE_KNOWLEDGE_BASE['새우살']
    if '바지락' in n: return STORAGE_KNOWLEDGE_BASE['바지락살']
    if '사누끼' in n or '우동' in n: return STORAGE_KNOWLEDGE_BASE['우동면']
    if '명란' in n: return STORAGE_KNOWLEDGE_BASE['명란젓']
    if '돼지' in n and '다짐육' in n: return STORAGE_KNOWLEDGE_BASE['돼지고기 다짐육']
    if '소고기' in n and '다짐육' in n or '다짐육' in n: return STORAGE_KNOWLEDGE_BASE['소고기 다짐육']

    # 3. 신선 채소 & 가공 & 생육/생선/빵 매칭 (긴 단어 우선)
    if '대란' in n or '계란' in n or '달걀' in n: return STORAGE_KNOWLEDGE_BASE['계란']
    if '순두부' in n: return STORAGE_KNOWLEDGE_BASE['순두부']
    if '두부' in n: return STORAGE_KNOWLEDGE_BASE['두부']
    if '파프리카' in n: return STORAGE_KNOWLEDGE_BASE['파프리카']
    if '양파' in n: return STORAGE_KNOWLEDGE_BASE['양파']
    if '대파' in n or '쪽파' in n: return STORAGE_KNOWLEDGE_BASE['대파']
    if '감자' in n: return STORAGE_KNOWLEDGE_BASE['감자']
    if '애호박' in n or '호박' in n: return STORAGE_KNOWLEDGE_BASE['애호박']
    if '양배추' in n: return STORAGE_KNOWLEDGE_BASE['양배추']
    if '알배기' in n or ('배추' in n and '김치' not in n): return STORAGE_KNOWLEDGE_BASE['알배기배추']
    if '청경채' in n: return STORAGE_KNOWLEDGE_BASE['청경채']
    if '콩나물' in n: return STORAGE_KNOWLEDGE_BASE['콩나물']
    if '숙주' in n: return STORAGE_KNOWLEDGE_BASE['숙주나물']
    if '팽이' in n: return STORAGE_KNOWLEDGE_BASE['팽이버섯']
    if '표고' in n: return STORAGE_KNOWLEDGE_BASE['표고버섯']
    if '가지' in n: return STORAGE_KNOWLEDGE_BASE['가지']
    if '샐러드' in n: return STORAGE_KNOWLEDGE_BASE['샐러드 채소']
    if '마늘' in n: return STORAGE_KNOWLEDGE_BASE['마늘']
    if '김치' in n: return STORAGE_KNOWLEDGE_BASE['김치']
    if '돼지' in n and '등심' in n or '등심' in n: return STORAGE_KNOWLEDGE_BASE['돼지 등심']
    if '삼겹' in n: return STORAGE_KNOWLEDGE_BASE['통삼겹살']
    if '부채살' in n or '소고기' in n: return STORAGE_KNOWLEDGE_BASE['소고기 부채살']
    if '연어' in n: return STORAGE_KNOWLEDGE_BASE['생연어']
    if '베이컨' in n: return STORAGE_KNOWLEDGE_BASE['베이컨']
    if '바게트' in n: return STORAGE_KNOWLEDGE_BASE['바게트']
    if '햄버거번' in n: return STORAGE_KNOWLEDGE_BASE['햄버거번']
    if '꽃빵' in n: return STORAGE_KNOWLEDGE_BASE['꽃빵']
    if '라멘' in n or '돈코츠' in n: return STORAGE_KNOWLEDGE_BASE['라멘']
    if '생면' in n: return STORAGE_KNOWLEDGE_BASE['중화 생면']

    # 4. 정제 후 직접 매칭 시도
    cleaned = clean_ingredient_name(raw_name)
    if cleaned in STORAGE_KNOWLEDGE_BASE:
        return STORAGE_KNOWLEDGE_BASE[cleaned]

    for key, data in STORAGE_KNOWLEDGE_BASE.items():
        if key in cleaned or cleaned in key:
            return data

    # 5. 최종 폴백
    cat_label = '🥬 신선식품' if cat_hint == 'fresh' else ('❄️ 냉동식품' if cat_hint == 'frozen' else '🧂 조미료 & 팬트리')
    loc = '냉장실 보관' if cat_hint == 'fresh' else ('냉동실 밀폐 보관' if cat_hint == 'frozen' else '상온 건조한 곳')
    dur = '냉장 7일' if cat_hint == 'fresh' else ('냉동 2~3개월' if cat_hint == 'frozen' else '상온 6개월~1년')
    return {
        'name': cleaned,
        'category': cat_hint,
        'categoryLabel': cat_label,
        'location': loc,
        'duration': dur,
        'tip': f'직사광선과 공기 접촉을 피해 밀폐용기 또는 지퍼백에 소분하여 {loc}하세요.',
        'spoilage': '이취, 변색, 끈적임 및 곰팡이 발생 시 즉시 폐기'
    }

def generate_storage_data_for_products(products):
    """
    클라이언트 맞춤 장바구니 품목(products) 목록을 순회하여
    중복 없이 브랜드명과 형용사가 완전히 배제된 순수 식재료 보관 카드 데이터 목록 생성
    """
    seen_names = set()
    result = []

    for p in products:
        raw_name = p.get('name', '')
        spec = p.get('spec', '')
        cat_hint = p.get('storage', 'fresh')

        base_entry = resolve_storage_entry(raw_name, cat_hint)
        display_name = base_entry['name']

        if display_name in seen_names:
            continue
        seen_names.add(display_name)

        card = {
            'name': display_name,
            'category': base_entry['category'],
            'categoryLabel': base_entry['categoryLabel'],
            'location': base_entry['location'],
            'duration': base_entry['duration'],
            'spec': spec or '1회 구매 분량',
            'tip': base_entry['tip'],
            'spoilage': base_entry['spoilage']
        }
        result.append(card)

    # 카테고리 정렬: fresh -> frozen -> seasoning, 그 후 가나다 순
    cat_order = {'fresh': 1, 'frozen': 2, 'seasoning': 3}
    result.sort(key=lambda x: (cat_order.get(x['category'], 4), x['name']))
    return result
