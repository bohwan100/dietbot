import os
import json
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cdn_base = "https://bohwan100.github.io/zipbab"
render_base = "https://dietbot.onrender.com"

clients_dir = os.path.join(BASE_DIR, 'clients')
registry_file = os.path.join(BASE_DIR, 'data', 'clients_registry.json')

registry = {}
if os.path.exists(registry_file):
    try:
        with open(registry_file, 'r', encoding='utf-8') as f:
            registry = json.load(f)
    except Exception:
        registry = {}

clients_data = []

if os.path.exists(clients_dir):
    reg_updated = False
    for c in sorted(os.listdir(clients_dir)):
        c_path = os.path.join(clients_dir, c)
        if not os.path.isdir(c_path):
            continue
        info_file = os.path.join(c_path, 'client_info.json')
        
        reg_item = registry.get(c, {})
        reg_ts = reg_item.get('timestamp')
        reg_dt = reg_item.get('registered_at')
        is_pinned = reg_item.get('pinned', False) or ('최종본' in c)

        if not reg_ts:
            reg_ts = int(os.path.getmtime(c_path))
            import datetime
            reg_dt = datetime.datetime.fromtimestamp(reg_ts).strftime("%Y-%m-%d %H:%M:%S")
            registry[c] = {
                "client_id": c,
                "client_name": c,
                "registered_at": reg_dt,
                "timestamp": reg_ts,
                "pinned": is_pinned
            }
            reg_updated = True

        if os.path.exists(info_file):
            try:
                with open(info_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['folder_name'] = c
                    data['reg_timestamp'] = reg_ts
                    data['reg_date'] = reg_dt or data.get('created_at', '')
                    data['is_pinned'] = is_pinned
                    clients_data.append(data)
            except Exception:
                pass
        else:
            clients_data.append({
                'client_id': c,
                'client_name': c,
                'folder_name': c,
                'reg_timestamp': reg_ts,
                'reg_date': reg_dt,
                'is_pinned': is_pinned,
                'household_size': '1명',
                'budget': 300000,
                'goal': '일반식',
                'cuisine': '한식, 일식',
                'pages': {
                    'portal': f'clients/{c}/index.html',
                    'cart': f'clients/{c}/cart.html',
                    'recipes': f'clients/{c}/recipes.html',
                    'storage': f'clients/{c}/storage.html'
                }
            })

    if reg_updated:
        try:
            os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

# 1. '최종본 !!!'은 무조건 맨 첫 번째(왼쪽 상단 0순위) 고정
# 2. 그 뒤로는 영구 등록 타임스탬프(reg_timestamp) 최신순(내림차순) 정렬
# 3. 파일 삭제/컨테이너 재시작에도 순서가 절대 섞이지 않는 불변(Deterministic) 정렬
def get_sort_key(item):
    fname = item.get('folder_name', item.get('client_id', ''))
    cname = item.get('client_name', '')
    if item.get('is_pinned') or '최종본' in fname or '최종본' in cname:
        return (0, 0, fname)
    ts = item.get('reg_timestamp', 0)
    return (1, -ts, fname)

clients_data.sort(key=get_sort_key)

total_clients = len(clients_data)
avg_budget = int(sum(c.get('budget', 300000) for c in clients_data) / max(total_clients, 1))
total_meals = sum(c.get('total_meals', 30) for c in clients_data)

html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🥗 다이어트봇 회원/고객 관리 매니저</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: rgba(18, 24, 38, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #38bdf8;
      --accent: #f97316;
      --danger: #ef4444;
      --success: #34d399;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; }}
    body {{
      background-color: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 30px 20px 80px;
      min-height: 100vh;
    }}
    .container {{
      max-width: 1280px;
      margin: 0 auto;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 20px;
      margin-bottom: 30px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
    }}
    .brand-title {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .brand-icon {{
      font-size: 2.2rem;
      background: rgba(56, 189, 248, 0.15);
      width: 56px;
      height: 56px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}
    h1 {{
      font-size: 1.7rem;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}
    .header-desc {{
      color: var(--text-muted);
      font-size: 0.9rem;
      margin-top: 4px;
    }}
    .header-actions {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .btn {{
      padding: 10px 18px;
      border-radius: 12px;
      font-size: 0.92rem;
      font-weight: 700;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all 0.2s;
    }}
    .btn-orange {{
      background: linear-gradient(135deg, #f97316, #ea580c);
      color: #fff;
      box-shadow: 0 4px 14px rgba(249, 115, 22, 0.4);
    }}
    .btn-orange:hover {{
      background: linear-gradient(135deg, #ea580c, #c2410c);
      transform: translateY(-2px);
    }}
    .btn-ghost {{
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.15);
      color: #cbd5e1;
    }}
    .btn-ghost:hover {{
      background: rgba(255, 255, 255, 0.1);
      color: #fff;
    }}

    /* Stats Overview */
    .stats-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 26px;
    }}
    .stat-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 16px;
      padding: 20px;
    }}
    .stat-label {{
      font-size: 0.82rem;
      color: var(--text-muted);
      font-weight: 600;
    }}
    .stat-val {{
      font-size: 1.8rem;
      font-weight: 800;
      color: #fff;
      margin-top: 6px;
    }}

    /* Filter & Batch Action Bar */
    .filter-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 24px;
      flex-wrap: wrap;
      background: rgba(18, 24, 38, 0.6);
      padding: 16px 20px;
      border-radius: 16px;
      border: 1px solid var(--card-border);
    }}
    .search-input {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 10px 16px;
      font-size: 0.95rem;
      color: #fff;
      width: 280px;
      outline: none;
      transition: all 0.2s;
    }}
    .search-input:focus {{
      border-color: var(--primary);
      background: rgba(255, 255, 255, 0.08);
    }}

    /* Batch Selection & Delete Controls */
    .batch-controls {{
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .select-all-label {{
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      user-select: none;
      font-size: 0.88rem;
      font-weight: 700;
      color: #cbd5e1;
      background: rgba(255, 255, 255, 0.05);
      padding: 9px 14px;
      border-radius: 10px;
      border: 1px solid var(--card-border);
      transition: all 0.2s;
    }}
    .select-all-label:hover {{
      background: rgba(255, 255, 255, 0.09);
      color: #fff;
    }}
    .select-all-chk {{
      width: 18px;
      height: 18px;
      cursor: pointer;
      accent-color: var(--danger);
    }}
    .btn-batch-delete {{
      background: rgba(239, 68, 68, 0.15);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #94a3b8;
      padding: 9px 16px;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 700;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: not-allowed;
      transition: all 0.2s;
    }}
    .btn-batch-delete:not(:disabled) {{
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: #fff;
      border-color: #dc2626;
      box-shadow: 0 4px 14px rgba(239, 68, 68, 0.35);
      cursor: pointer;
    }}
    .btn-batch-delete:not(:disabled):hover {{
      background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
      transform: translateY(-1px);
    }}

    /* Quick Filter Chips */
    .quick-filters {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }}
    .q-filter {{
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #cbd5e1;
      padding: 7px 15px;
      border-radius: 9999px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }}
    .q-filter:hover {{
      background: rgba(255, 255, 255, 0.12);
      color: #fff;
    }}
    .q-filter.active {{
      background: #38bdf8;
      border-color: #38bdf8;
      color: #0b0f19;
      font-weight: 800;
      box-shadow: 0 2px 10px rgba(56, 189, 248, 0.35);
    }}

    /* Clients Grid */
    .client-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 20px;
    }}
    .client-card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 24px;
      backdrop-filter: blur(12px);
      transition: all 0.25s ease;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      position: relative;
    }}
    .client-card:hover {{
      border-color: rgba(56, 189, 248, 0.4);
      transform: translateY(-4px);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
    }}
    .client-card.is-selected {{
      border-color: rgba(239, 68, 68, 0.6) !important;
      background: rgba(239, 68, 68, 0.06) !important;
      box-shadow: 0 0 24px rgba(239, 68, 68, 0.2) !important;
    }}
    .client-head {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 16px;
      gap: 10px;
    }}
    .client-select-chk {{
      width: 20px;
      height: 20px;
      margin-top: 3px;
      cursor: pointer;
      accent-color: var(--danger);
      flex-shrink: 0;
    }}
    .client-name {{
      font-size: 1.3rem;
      font-weight: 800;
      color: #fff;
    }}
    .client-meta {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 3px;
    }}
    .head-right-tools {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .badge-goal {{
      background: rgba(249, 115, 22, 0.15);
      color: #fb923c;
      border: 1px solid rgba(249, 115, 22, 0.3);
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
    }}
    .btn-card-delete {{
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.3);
      color: #fca5a5;
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.2s;
    }}
    .btn-card-delete:hover {{
      background: #ef4444;
      color: #fff;
      border-color: #ef4444;
      transform: scale(1.08);
      box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
    }}

    .client-details {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 0.88rem;
      color: #cbd5e1;
      margin-bottom: 20px;
      background: rgba(0, 0, 0, 0.2);
      padding: 14px;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.04);
    }}
    .detail-row {{
      display: flex;
      justify-content: space-between;
    }}
    .detail-row span.k {{
      color: var(--text-muted);
    }}
    .detail-row span.v {{
      font-weight: 600;
      color: #f1f5f9;
    }}
    .client-actions {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}
    .action-link {{
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 0.92rem;
      font-weight: 700;
      text-align: center;
      text-decoration: none;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}
    .btn-kakao-copy {{
      background: linear-gradient(135deg, #fee500 0%, #facc15 100%);
      color: #1e1b4b;
      font-weight: 800;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(250, 204, 21, 0.35);
    }}
    .btn-kakao-copy:hover {{
      background: linear-gradient(135deg, #facc15 0%, #eab308 100%);
      transform: translateY(-1px);
    }}
    .action-portal {{
      background: linear-gradient(135deg, #0284c7, #0369a1);
      color: #fff;
      box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
    }}
    .action-portal:hover {{
      background: linear-gradient(135deg, #0369a1, #075985);
      transform: translateY(-1px);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand-title">
        <div class="brand-icon">🥗</div>
        <div>
          <h1>🥗 다이어트봇 고객 & 회원 전용 관리 매니저</h1>
          <div class="header-desc">다이어트·체중 감량 30일/60일 맞춤 식단 & 로켓프레시 장바구니 전용 관리</div>
          <div style="display: flex; align-items: center; gap: 8px; margin-top: 6px;">
            <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(52, 211, 153, 0.4); color: #34d399; font-size: 0.78rem; font-weight: 700; padding: 3px 10px; border-radius: 999px; display: inline-flex; align-items: center; gap: 5px;">
              <span style="width: 7px; height: 7px; background: #34d399; border-radius: 50%;"></span>
              🌐 무료 분산 CDN 호스팅 활성화 (GitHub Pages / Fastly Edge 망 · 10만 명 무제한 트래픽)
            </span>
          </div>
        </div>
      </div>
      <div class="header-actions">
        <a href="https://zipbabot.onrender.com/clients" target="_blank" class="btn btn-ghost" style="border-color: rgba(249, 115, 22, 0.5); color: #fb923c; background: rgba(249, 115, 22, 0.1);">👥 기존 집밥봇 관리자 (8080)</a>
        <button type="button" onclick="triggerManualGitSync(this)" class="btn btn-ghost" style="border-color: rgba(56, 189, 248, 0.4); color: #38bdf8;">☁️ GitHub 영구 저장 (Sync)</button>
        <a href="survey.html" class="btn btn-orange">➕ 신규 다이어트 고객 (설문)</a>
        <a href="index.html" class="btn btn-ghost">🏠 다이어트봇 홈</a>
      </div>
    </header>

    <!-- 📢 고객 전달용 설문지 배포 배너 (스마트폰 카톡 전송 가능) -->
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%); border: 1.5px solid #eab308; border-radius: 16px; padding: 18px 24px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 14px;">
      <div style="display: flex; align-items: center; gap: 14px;">
        <span style="font-size: 2rem;">🎟️</span>
        <div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <strong style="color: #facc15; font-size: 1.05rem;">1회용 고객 설문 초대 링크 발급 센터</strong>
            <span style="background: #10b981; color: #fff; font-size: 0.72rem; font-weight: 800; padding: 2px 7px; border-radius: 6px;">무한 재작성 원천 차단</span>
          </div>
          <div style="color: #94a3b8; font-size: 0.86rem; margin-top: 3px;">
            고객 1명당 1회만 제출 가능한 1회용 링크를 1초 만에 발급합니다. 제출 즉시 코드가 영구 소멸되어 중복 작성이 불가능합니다.
          </div>
        </div>
      </div>
      <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
        <button type="button" onclick="createOneTimeSurveyLink()" id="btn-create-token" style="background: linear-gradient(135deg, #fee500 0%, #facc15 100%); color: #1e1b4b; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 800; font-size: 0.88rem; cursor: pointer; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 10px rgba(250, 204, 21, 0.35);">
          ⚡ 1회용 설문 링크 1초 발급 & 복사
        </button>
        <button type="button" onclick="openTokenManagerModal()" style="background: rgba(255, 255, 255, 0.08); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.2); padding: 10px 16px; border-radius: 10px; font-weight: 700; font-size: 0.85rem; cursor: pointer;">
          📊 발급/사용 현황
        </button>
        <a href="survey.html?admin=true" target="_blank" style="background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.4); padding: 10px 14px; border-radius: 10px; font-weight: 700; font-size: 0.85rem; text-decoration: none;">
          👑 관리자 직접 등록 ➔
        </a>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">등록된 고객 수</div>
        <div class="stat-val"><span id="stat-total-clients">{total_clients}</span><span style="font-size: 1rem; color: var(--text-muted); font-weight: normal;"> 명</span></div>
      </div>
      <div class="stat-card">
        <div class="stat-label">평균 식비 예산</div>
        <div class="stat-val">{avg_budget:,}<span style="font-size: 1rem; color: var(--text-muted); font-weight: normal;"> 원</span></div>
      </div>
    </div>

    <!-- Filter & Batch Action Bar -->
    <div class="filter-bar">
      <div class="batch-controls">
        <input type="text" class="search-input" id="search" placeholder="🔍 고객 성함 또는 키워드 검색..." onkeyup="filterClients()">
        <label class="select-all-label">
          <input type="checkbox" id="select-all-chk" class="select-all-chk" onchange="toggleSelectAll(this)">
          <span>전체 선택</span>
        </label>
        <button type="button" id="btn-batch-delete" onclick="deleteSelectedClients()" disabled class="btn-batch-delete">
          🗑️ 선택 고객 삭제 (<span id="selected-count">0</span>)
        </button>
      </div>
      <div style="color: var(--text-muted); font-size: 0.88rem;">
        총 <strong style="color: #fff;" id="client-count">{total_clients}</strong>명의 고객이 등록되어 있습니다.
      </div>
    </div>

    <!-- Quick Filter Chips -->
    <div class="quick-filters">
      <button type="button" class="q-filter active" onclick="setQuickFilter('all', this)">전체 ({total_clients}명)</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('한식', this)">🇰🇷 한식</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('일식', this)">🇯🇵 일식</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('양식', this)">🇪🇺 양식</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('중식', this)">🇨🇳 중식</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('단백질', this)">💪 고단백/벌크업</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('다이어트', this)">🥗 다이어트</button>
      <button type="button" class="q-filter" onclick="setQuickFilter('최종본', this)">📌 검증용 고정</button>
    </div>

    <!-- Grid -->
    <div class="client-grid" id="grid">
"""

for c in clients_data:
    cid = c.get('folder_name', c.get('client_id'))
    name = c.get('client_name', cid)
    age = c.get('client_age', '')
    household = c.get('household_size', '1명')
    budget = c.get('budget', 300000)
    spent = c.get('total_spent', budget)
    goal = c.get('goal', '일반식')
    cuisine = c.get('cuisine', '한식, 일식')
    goal_notes = c.get('goal_notes', '')
    version_ts = int(c.get('reg_timestamp', 1792628000))
    portal_link = f"clients/{cid}/index.html?v={version_ts}"
    recipe_link = f"clients/{cid}/recipes.html?v={version_ts}"
    cart_link = f"clients/{cid}/cart.html?v={version_ts}"
    storage_link = f"clients/{cid}/storage.html?v={version_ts}"

    reg_date_str = c.get('reg_date', '')
    reg_date_badge = f'<span style="color: #64748b; font-size: 0.76rem; font-weight: 500;">· 🕒 {reg_date_str[:16]}</span>' if reg_date_str else ''

    goal_notes_html = ""
    if goal_notes and goal_notes.strip():
        goal_notes_html = f"""            <div class="detail-row" style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; border-radius: 6px; padding: 8px 10px; margin-top: 8px; flex-direction: column; align-items: flex-start; gap: 4px;">
              <span class="k" style="color: #38bdf8; font-weight: 800; font-size: 0.78rem;">🎯 고객 목표 (설문 6번)</span>
              <span class="v" style="color: #f1f5f9; font-size: 0.84rem; max-width: 100%; white-space: normal; line-height: 1.45; font-weight: 500;">"{goal_notes}"</span>
            </div>"""

    is_pinned = ('최종본' in cid or '최종본' in name)
    pinned_badge = '<span style="background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; font-size: 0.75rem; font-weight: 800; padding: 3px 8px; border-radius: 6px; box-shadow: 0 2px 8px rgba(245, 158, 11, 0.35); display: inline-flex; align-items: center; gap: 4px;">📌 고정 검증용</span>' if is_pinned else ''
    card_custom_style = 'style="border: 2px solid #f59e0b; background: rgba(26, 20, 10, 0.85); box-shadow: 0 6px 24px rgba(245, 158, 11, 0.18);"' if is_pinned else ''
    chk_disabled = 'disabled title="검증 전용 포털은 삭제할 수 없습니다"' if is_pinned else 'title="삭제 대상 선택"'
    del_btn = '<span style="font-size: 1rem; opacity: 0.6;" title="검증 전용 마스터 포털 (삭제 불가)">🔒</span>' if is_pinned else f"""<button type="button" onclick="deleteSingleClient('{cid}', '{name}')" class="btn-card-delete" title="[{name}] 고객 폴더 및 파일 영구 삭제">🗑️</button>"""

    html_content += f"""      <div class="client-card" id="card-{cid}" data-name="{name} {cid} {goal} {cuisine} {goal_notes}" {card_custom_style}>
        <div>
          <div class="client-head">
            <div style="display: flex; align-items: flex-start; gap: 12px;">
              <input type="checkbox" class="client-select-chk" value="{cid}" data-name="{name}" onchange="onSelectionChange(this)" {chk_disabled}>
              <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <div class="client-name">{name}</div>
                  {pinned_badge}
                </div>
                <div class="client-meta">📁 {cid} {reg_date_badge}</div>
              </div>
            </div>
            <div class="head-right-tools">
              <span class="badge-goal">{goal}</span>
              {del_btn}
            </div>
          </div>

          <div class="client-details">
            <div class="detail-row">
              <span class="k">구성 인원</span>
              <span class="v">{household} ({age})</span>
            </div>
            <div class="detail-row">
              <span class="k">한 달 예산</span>
              <span class="v">{budget:,}원 (실구매 {spent:,}원)</span>
            </div>
            <div class="detail-row">
              <span class="k">선호 취향</span>
              <span class="v">{cuisine}</span>
            </div>
{goal_notes_html}
          </div>
        </div>

        <div class="client-actions">
          <button type="button" onclick="copyKakaoLink('{name}', '{cid}', this)" class="action-link btn-kakao-copy">
            💬 카톡 전송용 맞춤 링크 복사 (CDN 분산)
          </button>
          <a href="{portal_link}" target="_blank" class="action-link action-portal" style="padding: 12px; font-size: 0.9rem; justify-content: center;">
            🏠 맞춤 포털 열기
          </a>
        </div>
      </div>
"""

html_content += f"""    </div>
  </div>

  <!-- 🎟️ 1회용 설문 초대 코드 관리 모달 -->
  <div id="token-modal" style="display: none; position: fixed; inset: 0; background: rgba(0, 0, 0, 0.75); backdrop-filter: blur(8px); z-index: 9999; align-items: center; justify-content: center; padding: 20px;">
    <div style="background: #0f172a; border: 1.5px solid rgba(250, 204, 21, 0.4); border-radius: 20px; width: 100%; max-width: 760px; max-height: 85vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 50px rgba(0, 0, 0, 0.8);">
      <div style="padding: 20px 24px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: space-between; align-items: center;">
        <div style="font-size: 1.25rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px;">
          <span>🎟️</span> 1회용 설문 초대장 발급 & 실시간 현황
        </div>
        <button type="button" onclick="closeTokenModal()" style="background: rgba(255, 255, 255, 0.1); border: none; color: #94a3b8; font-size: 1.2rem; width: 32px; height: 32px; border-radius: 50%; cursor: pointer;">✕</button>
      </div>
      
      <!-- 발급 컨트롤러 -->
      <div style="padding: 16px 24px; background: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.08); display: flex; gap: 10px; align-items: center;">
        <input type="text" id="token-note-input" placeholder="고객 메모 (예: 홍길동 님)" style="flex: 1; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #fff; padding: 10px 14px; border-radius: 10px; font-size: 0.9rem; outline: none;">
        <button type="button" onclick="createOneTimeSurveyLink(document.getElementById('token-note-input').value)" style="background: #eab308; color: #1e1b4b; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 800; font-size: 0.88rem; cursor: pointer; white-space: nowrap;">
          + 1회용 링크 발급
        </button>
      </div>

      <!-- 토큰 목록 테이블 -->
      <div style="padding: 20px 24px; overflow-y: auto; flex: 1;">
        <div id="token-list-container">
          <div style="text-align: center; padding: 40px; color: #94a3b8;">불러오는 중...</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    // file:// 로 직접 열었을 경우 자동으로 온라인 CDN 주소로 즉시 전환
    if (window.location.protocol === 'file:') {{
      window.location.replace('https://bohwan100.github.io/zipbab/clients.html');
    }}

    const cdnBase = '{cdn_base}';
    const renderBase = '{render_base}';

    // 🎟️ 1회용 설문 링크 즉시 발급 및 복사
    async function createOneTimeSurveyLink(note = '') {{
      const btn = document.getElementById('btn-create-token');
      if (btn) btn.disabled = true;
      try {{
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const apiBase = isLocal ? '' : renderBase;
        const res = await fetch(apiBase + '/api/tokens/generate', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ note: note || '1회용 맞춤 식단 초대장' }})
        }});
        const data = await res.json();
        if (data.success && data.token) {{
          const fullLink = `${{renderBase}}/survey.html?token=${{data.token.token}}`;
          await navigator.clipboard.writeText(fullLink);
          showCopyToast(`🎟️ [1회용 초대 링크 발급 & 복사 완료!]\\n코드: ${{data.token.token}}\\n\\n카톡에 바로 붙여넣어 전송하세요!\\n(고객이 1회 제출 시 즉시 영구 소멸되어 재작성이 차단됩니다)`);
          
          const noteInput = document.getElementById('token-note-input');
          if (noteInput) noteInput.value = '';
          
          const modal = document.getElementById('token-modal');
          if (modal && modal.style.display === 'flex') {{
            loadAndRenderTokens();
          }}
        }} else {{
          alert('1회용 링크 발급 실패: ' + (data.error || '오류 발생'));
        }}
      }} catch (err) {{
        alert('발급 통신 오류: ' + err.message);
      }} finally {{
        if (btn) btn.disabled = false;
      }}
    }}

    function openTokenManagerModal() {{
      const modal = document.getElementById('token-modal');
      modal.style.display = 'flex';
      loadAndRenderTokens();
    }}

    function closeTokenModal() {{
      document.getElementById('token-modal').style.display = 'none';
    }}

    async function loadAndRenderTokens() {{
      const container = document.getElementById('token-list-container');
      container.innerHTML = '<div style="text-align: center; padding: 30px; color: #94a3b8;">⏳ 토큰 목록 동기화 중...</div>';
      try {{
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const apiBase = isLocal ? '' : renderBase;
        const res = await fetch(apiBase + '/api/tokens/list');
        const data = await res.json();
        if (data.success && data.tokens) {{
          renderTokensTable(data.tokens);
        }} else {{
          container.innerHTML = '<div style="text-align: center; padding: 30px; color: #ef4444;">목록을 불러오지 못했습니다.</div>';
        }}
      }} catch (err) {{
        container.innerHTML = `<div style="text-align: center; padding: 30px; color: #ef4444;">통신 오류: ${{err.message}}</div>`;
      }}
    }}

    function renderTokensTable(tokens) {{
      const container = document.getElementById('token-list-container');
      if (!tokens || tokens.length === 0) {{
        container.innerHTML = '<div style="text-align: center; padding: 40px; color: #64748b;">아직 발급된 1회용 초대 코드가 없습니다.<br>상단 [+ 1회용 링크 발급] 버튼을 눌러보세요!</div>';
        return;
      }}
      let html = `
        <table style="width: 100%; border-collapse: collapse; font-size: 0.88rem; text-align: left;">
          <thead>
            <tr style="border-bottom: 1.5px solid rgba(255, 255, 255, 0.1); color: #94a3b8;">
              <th style="padding: 10px 8px;">초대 코드</th>
              <th style="padding: 10px 8px;">상태</th>
              <th style="padding: 10px 8px;">메모 / 고객</th>
              <th style="padding: 10px 8px;">발급일시</th>
              <th style="padding: 10px 8px; text-align: right;">관리</th>
            </tr>
          </thead>
          <tbody>
      `;
      for (const t of tokens) {{
        const isUsed = t.status === 'used';
        const statusBadge = isUsed 
          ? `<span style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.75rem;">🔴 작성완료 (소멸)</span>`
          : `<span style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 0.75rem;">🟢 미사용 (유효)</span>`;
        
        let clientInfo = t.note || '-';
        if (isUsed && t.client_name) {{
          clientInfo = `<strong>${{t.client_name}}님</strong>` + (t.portal_url ? ` (<a href="${{t.portal_url}}" target="_blank" style="color: #38bdf8; text-decoration: underline;">포털열기</a>)` : '');
        }}

        const linkUrl = `${{renderBase}}/survey.html?token=${{t.token}}`;

        html += `
          <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
            <td style="padding: 12px 8px; font-family: monospace; font-weight: 700; color: #facc15;">${{t.token}}</td>
            <td style="padding: 12px 8px;">${{statusBadge}}</td>
            <td style="padding: 12px 8px; color: #cbd5e1;">${{clientInfo}}</td>
            <td style="padding: 12px 8px; color: #64748b; font-size: 0.8rem;">${{t.created_at || '-'}}</td>
            <td style="padding: 12px 8px; text-align: right; white-space: nowrap;">
              ${{!isUsed 
                ? `<button type="button" onclick="navigator.clipboard.writeText('${{linkUrl}}').then(()=>showCopyToast('📋 링크 복사 완료: ${{t.token}}'))" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); color: #fff; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; cursor: pointer; margin-right: 6px;">복사</button>` 
                : `<button type="button" onclick="resetTokenItem('${{t.token}}')" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 5px 10px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; cursor: pointer; margin-right: 6px;" title="고객이 기존 링크로 다시 설문 작성 가능">🔄 재작성 허용</button>`
              }}
              <button type="button" onclick="deleteTokenItem('${{t.token}}')" style="background: transparent; border: none; color: #ef4444; font-size: 0.85rem; cursor: pointer;" title="삭제">🗑️</button>
            </td>
          </tr>
        `;
      }}
      html += '</tbody></table>';
      container.innerHTML = html;
    }}

    async function resetTokenItem(token) {{
      if (!confirm(`[${{token}}] 초대 코드를 초기화하시겠습니까?\\n\\n고객이 기존에 받았던 동일한 링크에서 설문을 다시 작성할 수 있게 됩니다.`)) return;
      try {{
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const apiBase = isLocal ? '' : renderBase;
        const res = await fetch(apiBase + '/api/tokens/reset', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ token }})
        }});
        const data = await res.json();
        if (data.success) {{
          showCopyToast(`✅ [${{token}}] 초대 코드가 초기화되었습니다!\\n고객이 기존 링크로 다시 설문 작성이 가능합니다.`);
          loadAndRenderTokens();
        }} else {{
          alert('초기화 실패');
        }}
      }} catch (err) {{
        alert('초기화 오류: ' + err.message);
      }}
    }}

    async function deleteTokenItem(token) {{
      if (!confirm(`[${{token}}] 초대 코드를 삭제하시겠습니까?\\n\\n주의: 코드를 완전히 삭제하면 해당 링크는 '유효하지 않은 코드'가 되어 접속이 차단됩니다.`)) return;
      try {{
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const apiBase = isLocal ? '' : renderBase;
        const res = await fetch(apiBase + '/api/tokens/delete', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ token }})
        }});
        if (!res.ok) {{
          throw new Error(`서버 응답 오류 (상태: ${{res.status}})`);
        }}
        showCopyToast(`🗑️ [${{token}}] 초대 코드가 삭제되었습니다.`);
        loadAndRenderTokens();
      }} catch (err) {{
        alert('삭제 안내: ' + err.message);
      }}
    }}

    function copySurveyLink() {{
      const surveyUrl = `${{cdnBase}}/survey.html`;
      navigator.clipboard.writeText(surveyUrl).then(() => {{
        showCopyToast(`📋 고객 배포용 설문지 링크가 복사되었습니다!\\n전 세계 무료 CDN 초고속 배포망으로 10만 명도 즉시 접속됩니다.\\n\\n${{surveyUrl}}`);
      }}).catch(() => {{
        prompt('아래 설문 링크를 복사하여 고객에게 전송해 주세요:', surveyUrl);
      }});
    }}

    function copyKakaoLink(name, cid, btn) {{
      const mobileUrl = `${{cdnBase}}/clients/${{encodeURIComponent(cid)}}/index.html?v=${{Date.now()}}`;
      navigator.clipboard.writeText(mobileUrl).then(() => {{
        if (btn) {{
          const origHtml = btn.innerHTML;
          btn.style.background = '#10b981';
          btn.style.color = '#fff';
          btn.innerHTML = '<span>✅ 링크 복사 완료!</span>';
          setTimeout(() => {{
            btn.style.background = '';
            btn.style.color = '';
            btn.innerHTML = origHtml;
          }}, 2000);
        }}
        showCopyToast(`💬 [${{name}}]님의 맞춤 링크가 복사되었습니다!\\nPC(크롬 & 네이버 웨일 브라우저) 및 모바일 완벽 지원\\n\\n${{mobileUrl}}`);
      }}).catch(() => {{
        prompt('아래 링크를 복사하여 카카오톡에 전송해 주세요:', mobileUrl);
      }});
    }}

    function showCopyToast(msg) {{
      let toast = document.getElementById('copy-toast');
      if (!toast) {{
        toast = document.createElement('div');
        toast.id = 'copy-toast';
        toast.style.cssText = 'position: fixed; bottom: 30px; right: 30px; background: #0f172a; border: 1.5px solid #eab308; color: #fff; padding: 14px 22px; border-radius: 12px; font-weight: 700; font-size: 0.92rem; z-index: 9999; box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; align-items: center; gap: 8px; white-space: pre-line;';
        document.body.appendChild(toast);
      }}
      toast.innerText = msg;
      toast.style.display = 'flex';
      setTimeout(() => {{ toast.style.display = 'none'; }}, 3500);
    }}

    async function triggerManualGitSync(btn) {{
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '<span>⏳ GitHub 저장 중...</span>';
      try {{
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const apiBase = isLocal ? '' : window.location.origin;
        const res = await fetch(apiBase + '/api/sync-github');
        const data = await res.json();
        if (data.success) {{
          showCopyToast('✅ 모든 고객 데이터가 GitHub에 영구 보존(커밋 & 푸시)되었습니다!');
        }} else {{
          alert('GitHub 동기화 안내: ' + (data.message || '완료'));
        }}
      }} catch (err) {{
        alert('동기화 통신 오류: ' + err.message + '\\n\\n로컬 서버가 실행 중인지 확인해 주세요.');
      }} finally {{
        btn.disabled = false;
        btn.innerHTML = originalText;
      }}
    }}

    let currentQuickFilter = 'all';

    function setQuickFilter(keyword, btn) {{
      currentQuickFilter = keyword;
      document.querySelectorAll('.q-filter').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      filterClients();
    }}

    function filterClients() {{
      const q = document.getElementById('search').value.toLowerCase().trim();
      const cards = document.querySelectorAll('.client-card');
      let visible = 0;
      cards.forEach(c => {{
        const text = c.getAttribute('data-name').toLowerCase();
        const matchSearch = !q || text.includes(q);
        const matchQuick = (currentQuickFilter === 'all') || text.includes(currentQuickFilter.toLowerCase());

        if (matchSearch && matchQuick) {{
          c.style.display = 'flex';
          visible++;
        }} else {{
          c.style.display = 'none';
        }}
      }});
      document.getElementById('client-count').innerText = visible;
    }}

    /* Selection & Delete Logic */
    function onSelectionChange(chk) {{
      const card = chk.closest('.client-card');
      if (chk.checked) {{
        card.classList.add('is-selected');
      }} else {{
        card.classList.remove('is-selected');
      }}
      updateBatchButtonState();
    }}

    function toggleSelectAll(masterChk) {{
      const visibleCards = Array.from(document.querySelectorAll('.client-card')).filter(c => c.style.display !== 'none');
      visibleCards.forEach(card => {{
        const chk = card.querySelector('.client-select-chk');
        if (chk) {{
          chk.checked = masterChk.checked;
          if (masterChk.checked) {{
            card.classList.add('is-selected');
          }} else {{
            card.classList.remove('is-selected');
          }}
        }}
      }});
      updateBatchButtonState();
    }}

    function updateBatchButtonState() {{
      const checked = document.querySelectorAll('.client-select-chk:checked');
      const countEl = document.getElementById('selected-count');
      const btn = document.getElementById('btn-batch-delete');
      const masterChk = document.getElementById('select-all-chk');
      
      const count = checked.length;
      if (countEl) countEl.innerText = count;
      if (btn) btn.disabled = (count === 0);

      const allChks = document.querySelectorAll('.client-select-chk');
      if (masterChk && allChks.length > 0) {{
        masterChk.checked = (count === allChks.length && count > 0);
      }}
    }}

    async function deleteSingleClient(cid, name) {{
      if (!confirm(`⚠️ 정말 [${{name}}] 고객 데이터를 영구 삭제하시겠습니까?\\n\\n- clients/${{cid}} 폴더 및 모든 맞춤 페이지(식단/장바구니/보관법) 파일이 실제 컴퓨터에서 영구 삭제됩니다.\\n- 삭제 후 복구할 수 없습니다.`)) {{
        return;
      }}
      await sendDeleteRequest([cid], [name]);
    }}

    async function deleteSelectedClients() {{
      const checked = Array.from(document.querySelectorAll('.client-select-chk:checked'));
      if (checked.length === 0) return;

      const cids = checked.map(c => c.value);
      const names = checked.map(c => c.getAttribute('data-name') || c.value);

      if (!confirm(`⚠️ 정말 선택한 ${{cids.length}}명의 고객 데이터를 영구 삭제하시겠습니까?\\n\\n삭제 대상: ${{names.join(', ')}}\\n\\n실제 폴더와 파일이 영구 삭제되며 복구할 수 없습니다.`)) {{
        return;
      }}
      await sendDeleteRequest(cids, names);
    }}

    async function sendDeleteRequest(cids, names) {{
      const btn = document.getElementById('btn-batch-delete');
      const originalText = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = '⏳ 실제 파일 삭제 중...';

      // 로컬이 아니면 Render 온라인 백엔드로 직접 API 호출
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const apiBase = isLocal ? '' : window.location.origin;
      const endpoint = apiBase + '/api/delete-client';

      try {{
        const res = await fetch(endpoint, {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ client_ids: cids }})
        }});
        if (!res.ok) {{
          throw new Error(`서버 응답 오류 (상태 코드: ${{res.status}}). 잠시 후 다시 시도해 주세요.`);
        }}
        const result = await res.json();
        if (result.success) {{
          showCopyToast(`🗑️ ${{result.deleted.length}}명의 고객 데이터가 실제 파일에서 완전히 삭제되었습니다!`);
          setTimeout(() => {{
            window.location.reload();
          }}, 600);
        }} else {{
          alert('삭제 중 오류가 발생했습니다: ' + (result.errors || []).join(', '));
          btn.disabled = false;
          btn.innerHTML = originalText;
        }}
      }} catch (err) {{
        console.error('Delete request error:', err);
        alert('⚠️ 삭제 요청 중 안내: ' + err.message);
        btn.disabled = false;
        btn.innerHTML = originalText;
      }}
    }}
  </script>
</body>
</html>
"""

out_html = os.path.join(BASE_DIR, 'clients.html')
with open(out_html, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f'Successfully generated clients.html at {out_html}')

