import os
import sys
import time
import json
import urllib.parse
import subprocess

def ensure_chrome_window(activate: bool = False):
    """크롬 창이 모두 닫혀있는 경우 새 창 생성. activate가 True일 때만 전면 활성화"""
    if not activate:
        as_check = '''
        tell application "Google Chrome"
            if (count of windows) is 0 then
                make new window with properties {URL:"https://www.coupang.com"}
            end if
        end tell
        '''
    else:
        as_check = '''
        tell application "Google Chrome"
            activate
            if (count of windows) is 0 then
                make new window with properties {URL:"https://www.coupang.com"}
                delay 0.5
            end if
        end tell
        '''
    try:
        subprocess.run(['osascript', '-'], input=as_check, text=True, capture_output=True, check=True)
    except Exception:
        pass

def run_chrome_js(raw_js: str, url_match: str = "coupang.com", background: bool = True) -> str:
    """Chrome의 url_match 탭을 찾아 자바스크립트를 안전하게 실행 (eval 없이 CSP 준수).
    background=True인 경우 창을 띄우거나 탭을 바꾸지 않고 백그라운드 탭에서 조용히 무간섭 실행.
    """
    ensure_chrome_window(activate=not background)
    js_literal = json.dumps(raw_js, ensure_ascii=False)
    
    if background:
        # 백그라운드 무간섭 모드:
        # 1) activate, set active tab index, set index of w to 1 일체 호출 없음
        # 2) 매칭 탭이 없더라도 다른 탭이나 창을 건드리지 않도록 front window로 절대 폴백하지 않음
        # 3) 사용자의 현재 활성 프로세스(frontApp) 보존
        as_code = f'''
        tell application "Google Chrome"
            if (count of windows) is 0 then return "NO_WINDOWS"
            repeat with w in windows
                repeat with i from 1 to count of tabs of w
                    set t to tab i of w
                    if URL of t contains "{url_match}" then
                        return execute t javascript {js_literal}
                    end if
                end repeat
            end repeat
            return "TAB_NOT_FOUND"
        end tell
        '''
    else:
        # 포그라운드 모드 (창 및 탭 활성화)
        as_code = f'''
        tell application "Google Chrome"
            activate
            if (count of windows) is 0 then return "NO_WINDOWS"
            repeat with w in windows
                repeat with i from 1 to count of tabs of w
                    set t to tab i of w
                    if URL of t contains "{url_match}" then
                        set active tab index of w to i
                        set index of w to 1
                        delay 0.05
                        return execute t javascript {js_literal}
                    end if
                end repeat
            end repeat
            tell front window to return execute active tab javascript {js_literal}
        end tell
        '''
    try:
        proc = subprocess.run(['osascript', '-'], input=as_code, text=True, capture_output=True, check=True)
        return proc.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.stderr.strip()}"

def navigate_coupang_tab(url: str, background: bool = True):
    """쿠팡 탭을 특정 URL로 이동하거나 없으면 새 탭 생성.
    background=True인 경우 창을 띄우거나 다른 프로그램/창의 포커스를 뺏지 않고 백그라운드 탭에서 조용히 URL만 변경.
    """
    ensure_chrome_window(activate=not background)
    url_literal = json.dumps(url, ensure_ascii=False)
    
    if background:
        # 100% 무간섭 백그라운드 모드:
        # 1) 현재 사용자가 활성화해 둔 최상위 프로세스(frontApp)를 감지
        # 2) coupang.com 탭의 URL을 탐색 및 변경 (활성 탭 인덱스 불변)
        # 3) 'tell application frontApp' 대신 'System Events의 process'를 사용하여 Electron 등 가상 프로세스 앱 선택창 팝업 원천 차단!
        as_nav = f'''
        tell application "System Events" to set frontApp to name of first process whose frontmost is true
        set navResult to "NAV_FAILED"
        tell application "Google Chrome"
            repeat with w in windows
                repeat with i from 1 to count of tabs of w
                    set t to tab i of w
                    if URL of t contains "coupang.com" then
                        set URL of t to {url_literal}
                        set navResult to "NAVIGATED_BACKGROUND"
                        exit repeat
                    end if
                end repeat
                if navResult is not "NAV_FAILED" then exit repeat
            end repeat
            if navResult is "NAV_FAILED" then
                if (count of windows) > 0 then
                    set origActive to active tab index of window 1
                    tell window 1 to make new tab with properties {{URL:{url_literal}}}
                    set active tab index of window 1 to origActive
                    set navResult to "CREATED_BACKGROUND"
                else
                    make new window with properties {{URL:{url_literal}}}
                    set navResult to "CREATED_WINDOW"
                end if
            end if
        end tell
        if frontApp is not "Google Chrome" and frontApp is not "" then
            tell application "System Events"
                try
                    if exists (process frontApp) then
                        set frontmost of process frontApp to true
                    end if
                end try
            end tell
        end if
        return navResult
        '''
    else:
        # 포그라운드 모드
        as_nav = f'''
        tell application "Google Chrome"
            activate
            repeat with w in windows
                repeat with i from 1 to count of tabs of w
                    set t to tab i of w
                    if URL of t contains "coupang.com" then
                        set active tab index of w to i
                        set index of w to 1
                        set URL of t to {url_literal}
                        return "NAVIGATED"
                    end if
                end repeat
            end repeat
            tell front window to make new tab with properties {{URL:{url_literal}}}
            return "CREATED_NEW"
        end tell
        '''
    try:
        proc = subprocess.run(['osascript', '-'], input=as_nav, text=True, capture_output=True, check=True)
        return proc.stdout.strip()
    except Exception as e:
        return str(e)

def clear_akamai_cookies():
    """쿠팡 Akamai 방화벽 봇 플래그 쿠키를 Chrome DB에서 안전하게 삭제하여 접근 권한 복구"""
    import sqlite3
    cookie_path = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies')
    try:
        conn = sqlite3.connect(cookie_path, timeout=2.0)
        c = conn.cursor()
        c.execute("DELETE FROM cookies WHERE host_key LIKE '%coupang%' AND (name LIKE 'bm_%' OR name LIKE '%abck%' OR name LIKE 'ak_%')")
        conn.commit()
        conn.close()
        print("[Engine] 🛡️ Akamai 봇 플래그 쿠키 초기화 완료!")
        return True
    except Exception as e:
        print(f"[Engine] Cookie cleanup warning: {e}")
        return False

def add_single_item(query: str, item_name: str = "", target_qty: int = 1, spec: str = "", background: bool = True):
    """쿠팡 검색 ➔ 스마트 필요 용량/개수 파악(1개, 2개 등) ➔ 대용량 벌크 배제 ➔ 필요 수량 자동 설정 후 [장바구니 담기]"""
    try:
        import coupang_partners
        search_url = coupang_partners.get_deeplink_for_query(query)
        if not search_url:
            search_url = f"https://www.coupang.com/np/search?q={urllib.parse.quote(query)}&channel=user"
    except Exception:
        search_url = f"https://www.coupang.com/np/search?q={urllib.parse.quote(query)}&channel=user"

    print(f"[Engine] Navigating via Coupang Partners URL: {search_url}")
    navigate_coupang_tab(search_url, background=background)

    # 1. 검색 페이지 로딩 확인 & 스마트 단품/소용량 스코어링 추출
    find_js = f"""(() => {{
      try {{
        if (document.title.includes('Access Denied') || document.body.innerText.includes('Access Denied') || document.body.innerText.includes('edgesuite.net')) {{
          return 'ACCESS_DENIED';
        }}
        if (!window.location.href.includes('/np/search')) return 'WAITING_PAGE';
        const links = Array.from(document.links)
          .filter(a => a.href.includes('/vp/products/')
                    && !a.href.includes('recently_viewed') 
                    && !a.href.includes('view_together') 
                    && !a.closest('.recently-viewed-item') 
                    && !a.closest('#recent-view') 
                    && a.innerText.length > 5);
        if (!links.length) return 'WAITING_LINKS';

        const targetQty = {target_qty};

        // 1인 가구 최적 단품/용량 정밀 스코어링 함수
        function scoreProduct(a) {{
          const text = a.innerText;
          let score = 0;

          // [대용량 벌크 감점]: 박스, 대용량, 벌크, 업소용, 식자재 강력 감점 (-1000)
          if (text.includes('박스') || text.includes('대용량') || text.includes('벌크') || text.includes('업소용') || text.includes('식자재')) {{
            score -= 1000;
          }}

          // [2kg 이상 거대 중량 감점]: 쌀, 김치, 양파 외에는 2kg 이상 대용량 강력 배제 (-1200)
          if (text.match(/([2-9]|[0-9]{{2,}}) *kg/) && !text.includes('쌀') && !text.includes('김치') && !text.includes('양파')) {{
            score -= 1200;
          }}

          // [과도한 대용량 번들 감점]: 4개 이상 대량 묶음 (8개, 10개, 12개 등) 감점
          const bulkMatch = text.match(/([4-9]|[0-9]{{2,}}) *(개|모|팩|입|봉|구|캔)/);
          if (bulkMatch && targetQty < 4) {{
            score -= 1000;
          }}

          // [목표 수량 및 소용량 매칭 가산점]
          if (targetQty === 1) {{
            if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 500;
            else if (text.match(/[23] *(개|모|단|봉|팩|구|입|캔)/)) score += 100;
          }} else if (targetQty === 2) {{
            // 2개가 필요한 경우: 2개입 묶음 최우선(+600), 1개 단품이어도 2개 담으면 되므로 우수(+500)
            if (text.match(/2 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 600;
            else if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 500;
            else if (text.match(/3 *(개|모|단|봉|팩|구|입|캔)/)) score += 100;
          }} else if (targetQty >= 3) {{
            // 3개 이상 필요한 경우 (예: 두부 3모): 3개입 묶음 최우선(+600), 단품(+400)
            if (text.match(new RegExp(targetQty + ' *(개|모|단|봉|팩|통|병|입|구|캔)'))) score += 600;
            else if (text.match(/1 *(개|모|단|봉|팩|통|병|입|캔)/)) score += 400;
          }}

          // [로켓배송/프레시 가산점]
          if (text.includes('로켓프레시') || text.includes('새벽 도착') || text.includes('새벽도착')) {{
            score += 350;
          }} else if (text.includes('로켓배송') || text.includes('쿠팡추천')) {{
            score += 200;
          }}

          // [광고 감점]
          if (text.includes('광고')) score -= 200;

          // [가격 과다 감점]: 1인분 비고기류 20,000원 이상 번들 배제
          const priceMatch = text.match(/([0-9,]+) *원/);
          if (priceMatch) {{
            const price = parseInt(priceMatch[1].replace(/,/g, ''), 10);
            if (price > 20000 && !text.includes('앞다리') && !text.includes('한돈') && !text.includes('고기') && !text.includes('우삼겹') && !text.includes('오리')) {{
              score -= 700;
            }}
          }}

          return score;
        }}

        const scored = links.map(a => ({{ a: a, score: scoreProduct(a) }}));
        scored.sort((x, y) => y.score - x.score);

        const best = scored[0].a;
        return best.href + '|||' + encodeURIComponent(best.innerText.slice(0, 80));
      }} catch(e) {{
        return 'ERR: ' + e.message;
      }}
    }})()"""

    target_url = None
    prod_name = item_name or query
    for i in range(25):
        time.sleep(0.5)
        find_res = run_chrome_js(find_js, "coupang.com", background=background)
        if find_res == "ACCESS_DENIED":
            print("[Engine] ⚠️ Akamai Access Denied 감지! 자동 봇 쿠키 정리 실행 중...")
            clear_akamai_cookies()
            return {
                "success": False,
                "error": "쿠팡 보안 방화벽(Akamai) 일시 차단 감지 (봇 쿠키 자동 청소 완료. 약 5초 후 다시 시도해주세요)",
                "access_denied": True,
                "query": query
            }

        if i % 3 == 0 or "|||" in find_res:
            print(f"[Engine] Try {i}: find_res={repr(find_res)[:120]}")
        if "|||" in find_res:
            parts = find_res.split("|||", 1)
            target_url = parts[0].strip()
            decoded_name = urllib.parse.unquote(parts[1]).split('\n')[0].strip()
            prod_name = decoded_name or prod_name
            break

    if not target_url:
        return {
            "success": False,
            "error": "로켓배송 적정 용량 상품을 찾을 수 없습니다.",
            "query": query
        }

    # 2. 상품 상세 페이지로 이동
    navigate_coupang_tab(target_url, background=background)

    # 3. 상품 상세 페이지 수량 확인 & [장바구니 담기] 클릭
    click_js = f"""(() => {{
      try {{
        if (!window.location.href.includes("/vp/products/")) return "WAITING_PAGE";
        
        const targetQty = {target_qty};
        
        // 1. 현재 상품 제목에서 기포함된 번들 수량 파악
        const titleEl = document.querySelector('h1.prod-buy-header__title, .prod-title, .title');
        const titleText = titleEl ? titleEl.innerText : '';
        let bundleSize = 1;
        const bundleMatch = titleText.match(/([2-9])\\s*(개|모|팩|봉|입|캔|병|구)/);
        if (bundleMatch) {{
          bundleSize = parseInt(bundleMatch[1], 10);
        }}

        // 2. 실제 장바구니에 담을 최종 수량 계산
        let finalQty = targetQty;
        if (bundleSize >= targetQty) {{
          // 이미 번들에 필요한 수량이 전부 포함되어 있으므로 구매 수량 1
          finalQty = 1;
        }} else if (bundleSize > 1) {{
          finalQty = Math.max(1, Math.ceil(targetQty / bundleSize));
        }}

        // 3. 수량 인풋 조정
        const qtyInput = document.querySelector("input.prod-quantity__input, input.prod-buy-quantity");
        if (qtyInput) {{
          if (parseInt(qtyInput.value, 10) !== finalQty) {{
            qtyInput.value = String(finalQty);
            qtyInput.dispatchEvent(new Event("input", {{ bubbles: true }}));
            qtyInput.dispatchEvent(new Event("change", {{ bubbles: true }}));
          }}
        }}

        // 4. 플러스/마이너스 버튼으로 보조 보정
        const plusBtn = document.querySelector("button.prod-quantity__plus");
        const minusBtn = document.querySelector("button.prod-quantity__minus");
        let cur = parseInt((document.querySelector("input.prod-quantity__input, input.prod-buy-quantity") || {{}}).value || "1", 10);
        let loop = 0;
        while (cur < finalQty && plusBtn && loop < 10) {{
          plusBtn.click();
          cur++;
          loop++;
        }}
        while (cur > finalQty && minusBtn && loop < 10) {{
          minusBtn.click();
          cur--;
          loop++;
        }}

        // 5. 장바구니 담기 버튼 클릭
        const btn = document.querySelector(".prod-cart-btn") || 
                    Array.from(document.querySelectorAll("button")).find(b => b.innerText && b.innerText.includes("장바구니 담기"));
        if (btn) {{
          btn.click();
          return "CLICKED_QTY_" + finalQty;
        }}
        return "WAITING_BTN";
      }} catch(e) {{
        return "ERR: " + e.message;
      }}
    }})()"""

    clicked_ok = False
    for _ in range(20):
        time.sleep(0.5)
        click_res = run_chrome_js(click_js, "coupang.com", background=background)
        if click_res and click_res.startswith("CLICKED"):
            clicked_ok = True
            break

    time.sleep(0.8)
    return {
        "success": clicked_ok,
        "productName": prod_name,
        "query": query,
        "targetQty": target_qty,
        "url": target_url
    }

def audit_and_fix_cart_quantities():
    """장바구니 페이지에서 중복 담김으로 인해 수량이 불어난 품목을 1개로 자동 감량 보정"""
    fix_js = """(() => {
        let adjusted = [];
        const inputs = Array.from(document.querySelectorAll("input.cart-quantity-input, input[class*='quantity-input']"));
        for (const inp of inputs) {
            let val = parseInt(inp.value, 10);
            if (val > 1) {
                const container = inp.closest("div, tr, li");
                const minusBtn = container ? container.querySelector("[class*='minus-icon'], button") : null;
                let clicks = 0;
                while (val > 1 && minusBtn && clicks < 10) {
                    minusBtn.click();
                    val--;
                    clicks++;
                }
                adjusted.push(clicks + "회 감량");
            }
        }
        return adjusted.length ? adjusted.join(", ") : "ALL_CORRECT";
    })()"""
    return run_chrome_js(fix_js, "cart.coupang.com", background=True)

def open_cart_page():
    """전체 품목 담기 완료 후 또는 사용자 요청 시, 쿠팡 장바구니 페이지로 이동하고 수량 정밀 보정 후 크롬 창을 최상위 전면(Foreground)으로 띄움"""
    as_cart = '''
    tell application "Google Chrome"
        activate
        repeat with w in windows
            repeat with i from 1 to count of tabs of w
                set t to tab i of w
                if URL of t contains "coupang.com" then
                    set URL of t to "https://cart.coupang.com/cartView.pang"
                    set active tab index of w to i
                    set index of w to 1
                    return "OPENED_CART_EXISTING"
                end if
            end repeat
        end repeat
        tell front window
            make new tab with properties {URL:"https://cart.coupang.com/cartView.pang"}
            set index of front window to 1
        end tell
        return "OPENED_CART_NEW"
    end tell
    tell application "System Events"
        set frontmost of process "Google Chrome" to true
    end tell
    '''
    try:
        proc = subprocess.run(['osascript', '-'], input=as_cart, text=True, capture_output=True, check=True)
        # 장바구니 페이지 로드 후 수량 자동 감량 보정 수행
        time.sleep(1.0)
        audit_and_fix_cart_quantities()
        return proc.stdout.strip()
    except Exception as e:
        return str(e)

def get_cart_summary():
    """현재 장바구니에 담긴 품목 수 확인"""
    js = """(() => {
        try {
            const rawLinks = Array.from(document.querySelectorAll('a[href*="/vp/products/"]'));
            const titles = [];
            for (let i = 0; i < rawLinks.length; i++) {
                const a = rawLinks[i];
                if (a.closest('#recommend-area, .recommend-widget, [class*="recommend"], .together-view')) continue;
                const text = a.innerText.trim();
                if (!text) continue;
                const clean = text.split('옵션:')[0].trim().replace(/[\\r\\n]+/g, ' ');
                if (clean.length > 2 && !clean.includes('원') && !titles.includes(clean)) {
                    titles.push(clean);
                }
            }
            return titles.length + '|||' + encodeURIComponent(titles.slice(0, 15).join('###'));
        } catch(e) {
            return '0|||';
        }
    })()"""
    res = run_chrome_js(js, "cart.coupang.com")
    if "|||" in res:
        parts = res.split("|||", 1)
        count = int(parts[0]) if parts[0].isdigit() else 0
        decoded = urllib.parse.unquote(parts[1]) if len(parts) > 1 else ""
        items = decoded.split("###") if decoded else []
        return {"count": count, "items": items}
    return {"count": 0, "items": []}

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "국산 두부 500g"
    print(f"Adding '{q}'...")
    res = add_single_item(q)
    print("Result:", json.dumps(res, ensure_ascii=False, indent=2))
