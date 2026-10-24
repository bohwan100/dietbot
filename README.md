# 🥗 다이어트봇 (diet_bot) - 개인 맞춤 식단 & 장바구니 자동화 봇

> **다이어트·체중 감량·식단 관리 특화 자동화 솔루션**  
> 고객 설문 조사 기반 30일/60일/90일 맞춤 식단 설계 및 쿠팡 로켓프레시 100% 최적화 장바구니 자동 편성 엔진.

---

## 📁 디렉토리 구조

```
diet_bot/
├── generator/                 # 🧠 개인화 식단 & 장바구니 생성 알고리즘 엔진
│   ├── recipe_engine.py       # 107종 레시피 풀, 식재료 시너지 소진, 제로웨이스트 엔진
│   ├── build_client.py        # 8대 입력값 기반 맞춤 웹 포털 빌더
│   └── storage_engine.py      # 주차별 식재료 보관 가이드 생성기
├── templates/                 # 🎨 고객 제공용 웹페이지 템플릿
│   ├── portal.html            # 메인 식단 관리 허브
│   ├── recipes.html           # 30일 인터리빙 레시피 & 조리법
│   ├── cart.html              # 4주 분할 쿠팡 로켓프레시 장바구니
│   └── storage.html           # 신선도 200% 식재료 보관 꿀팁
├── data/                      # 💾 고객 레지스트리 및 초대코드 DB
│   ├── clients_registry.json  # 등록 고객 명부
│   └── invitation_codes.json  # 발급된 일회성 초대코드 목록
├── clients/                   # 👥 생성된 고객별 독립 포털 디렉토리
├── assets/                    # 📦 CSS, JS, 폰트, 아이콘 등 정적 에셋
├── zipbabbot-extension/       # 🛒 쿠팡 장바구니 1초 자동 담기 크롬 확장 프로그램
├── server.py                  # 🚀 설문 접수, 토큰 인증, 웹서버 (기본 포트: 8081)
├── survey.html                # 📋 신규 고객 설문지 (일회성 토큰 인증 연동)
├── clients.html               # 📊 관리자 통합 고객 관리 매니저 대시보드
├── requirements.txt           # 🐍 필수 패키지 목록
└── Procfile / render.yaml     # ☁️ 클라우드(Render) 배포 설정
```

---

## 🚀 빠른 시작 (Quick Start)

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. 로컬 서버 실행
```bash
python3 server.py
```
* **서버 주소**: `http://localhost:8081`
* **설문지**: `http://localhost:8081/survey.html`
* **고객 관리 매니저**: `http://localhost:8081/clients.html`

### 3. CLI로 직접 고객 페이지 생성
```bash
python3 generator/build_client.py   --id "고객_홍길동_01"   --name "홍길동"   --age "20대"   --household "1명"   --budget 250000   --frequency "저녁만 (30끼)"   --goal "다이어트"   --cuisine "한식, 일식"   --exclude "없음"   --pantry "간장, 참기름"
```
