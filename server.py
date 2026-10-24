import os
import sys
import json
import gc
import http.server
import socketserver
import threading
from urllib.parse import urlparse, parse_qs
import coupang_engine

# Memory optimization for 512MB RAM cloud containers (Render Free Tier):
# Reduce per-thread stack size from default 8MB to 256KB (32x memory savings per thread)
try:
    threading.stack_size(256 * 1024)
except Exception:
    pass

PORT = int(os.environ.get("PORT", 8081))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

def ensure_cloudflared():
    if os.environ.get("RENDER") or os.environ.get("RAILWAY_STATIC_URL"):
        return
    import subprocess
    try:
        res = subprocess.run(["pgrep", "-f", "cloudflared tunnel"], capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return
    except Exception:
        pass
    
    cf_bin = os.path.join(DIRECTORY, "scratch", "cloudflared")
    if os.path.exists(cf_bin):
        log_file = open(os.path.join(DIRECTORY, "scratch", "tunnel.log"), "a", encoding="utf-8")
        subprocess.Popen([cf_bin, "tunnel", "--url", f"http://127.0.0.1:{PORT}"], stdout=log_file, stderr=log_file)

def get_public_tunnel_url(host=None):
    # 1. Render provided external URL
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if render_url:
        return render_url.rstrip("/")
    
    # 2. Host header if running on any cloud or domain
    if host and 'localhost' not in host and '127.0.0.1' not in host:
        return f"https://{host}"

    # 3. Permanent 24/7 Cloud URL
    return "https://dietbot-4giy.onrender.com"

class CoupangAutoServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def setup(self):
        super().setup()
        try:
            self.request.settimeout(15.0)  # Close dead/hanging sockets after 15s
        except Exception:
            pass

    def translate_path(self, path):
        resolved = super().translate_path(path)
        if not os.path.exists(resolved):
            import unicodedata
            # macOS filesystem NFD/NFC normalization matching
            parts = resolved.split(os.sep)
            curr = "/" if resolved.startswith("/") else ""
            for part in parts:
                if not part: continue
                match = None
                target_nfc = unicodedata.normalize('NFC', part)
                target_nfd = unicodedata.normalize('NFD', part)
                if os.path.exists(curr):
                    try:
                        for entry in os.listdir(curr):
                            entry_nfc = unicodedata.normalize('NFC', entry)
                            entry_nfd = unicodedata.normalize('NFD', entry)
                            if entry == part or entry_nfc == target_nfc or entry_nfd == target_nfd:
                                match = entry
                                break
                    except Exception:
                        pass
                curr = os.path.join(curr, match if match else part)
            if os.path.exists(curr):
                return curr
        return resolved

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Allow-Private-Network', 'true')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/cart-summary':
            import importlib
            importlib.reload(coupang_engine)
            summary = coupang_engine.get_cart_summary()
            self._send_json(summary)
            return
        elif parsed.path == '/api/ping':
            self._send_json({"status": "ok", "message": "Coupang Auto Server is active!"})
            return
        elif parsed.path == '/api/partners/status':
            import importlib, coupang_partners
            importlib.reload(coupang_partners)
            self._send_json(coupang_partners.get_account_status())
            return
        elif parsed.path == '/api/partners/links':
            import importlib, coupang_partners
            importlib.reload(coupang_partners)
            self._send_json(coupang_partners.get_all_cached_links())
            return
        elif parsed.path == '/api/public-url':
            host = self.headers.get('Host')
            tunnel_url = get_public_tunnel_url(host=host)
            self._send_json({"success": True, "public_url": tunnel_url})
            return
        elif parsed.path == '/api/sync-github':
            import github_sync
            success, msg = github_sync.perform_git_sync("feat: manual dashboard sync")
            self._send_json({"success": success, "message": msg})
            return
        elif parsed.path == '/api/tokens/verify':
            import survey_token_manager as stm
            query = parse_qs(parsed.query)
            token = query.get('token', [''])[0]
            res = stm.verify_token(token)
            self._send_json(res)
            return
        elif parsed.path == '/api/tokens/list':
            import survey_token_manager as stm
            tokens = stm.get_all_tokens()
            self._send_json({"success": True, "tokens": tokens})
            return
        elif parsed.path == '/api/system/status':
            import subprocess
            try:
                commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
            except Exception:
                commit = "unknown"
            c_dir = os.path.join(DIRECTORY, "clients")
            c_list = sorted(os.listdir(c_dir)) if os.path.exists(c_dir) else []
            self._send_json({
                "commit": commit,
                "clients_count": len(c_list),
                "has_이보보": "이보보_30대" in c_list,
                "clients": c_list
            })
            return

        # Friendly URL routing
        if parsed.path in ['/survey', '/survey/']:
            self.path = '/survey.html'
        elif parsed.path in ['/clients', '/clients/', '/admin', '/admin/', '/manage', '/manage/']:
            self.path = '/clients.html'
        elif parsed.path in ['/builder', '/builder/', '/diy', '/diy/', '/meal', '/meal/']:
            self.path = '/diy_meal_builder.html'
        elif parsed.path in ['/builder', '/builder/', '/diy', '/diy/', '/meal', '/meal/']:
            self.path = '/diy_meal_builder.html'

        super().do_GET()

    def do_HEAD(self):
        parsed = urlparse(self.path)
        if parsed.path in ['/survey', '/survey/']:
            self.path = '/survey.html'
        elif parsed.path in ['/clients', '/clients/', '/admin', '/admin/', '/manage', '/manage/']:
            self.path = '/clients.html'
        elif parsed.path in ['/builder', '/builder/', '/diy', '/diy/', '/meal', '/meal/']:
            self.path = '/diy_meal_builder.html'
        elif parsed.path in ['/api/ping', '/api/partners/status', '/api/partners/links', '/api/public-url']:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            return
        super().do_HEAD()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
        
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if parsed.path == '/api/ping':
            self._send_json({"status": "ok", "message": "Coupang Auto Server is active!"})
            return

        if parsed.path == '/api/add-to-cart':
            query = data.get('query', '')
            name = data.get('name', '')
            qty = int(data.get('qty', 1))
            spec = data.get('spec', '')
            if not query:
                self._send_json({"success": False, "error": "Query required"}, 400)
                return

            print(f"[API] Adding to cart: {query} ({name}) - targetQty: {qty}, spec: {spec}")
            import importlib
            importlib.reload(coupang_engine)
            result = coupang_engine.add_single_item(query, name, target_qty=qty, spec=spec)
            self._send_json(result)
            return

        elif parsed.path == '/api/batch-add':
            items = data.get('items', [])
            if not items:
                self._send_json({"success": False, "error": "No items provided"}, 400)
                return

            print(f"[API] Batch adding {len(items)} items...")
            results = []
            for it in items:
                q = it.get('query', '')
                n = it.get('name', '')
                qty = int(it.get('qty', 1))
                spec = it.get('spec', '')
                if q:
                    res = coupang_engine.add_single_item(q, n, target_qty=qty, spec=spec)
                    results.append(res)

            self._send_json({
                "success": True,
                "total": len(items),
                "added": len([r for r in results if r.get('success')]),
                "details": results
            })
            return

        elif parsed.path == '/api/open-cart':
            print("[API] Opening Coupang cart page in Chrome (Bringing to foreground)...")
            import importlib
            importlib.reload(coupang_engine)
            res = coupang_engine.open_cart_page()
            self._send_json({"success": True, "message": "Cart opened", "detail": res})
            return

        elif parsed.path == '/api/fix-quantities':
            print("[API] Auditing and fixing cart item quantities...")
            import importlib
            importlib.reload(coupang_engine)
            res = coupang_engine.audit_and_fix_cart_quantities()
        elif parsed.path == '/api/partners/deeplink':
            import importlib, coupang_partners
            importlib.reload(coupang_partners)
            query = data.get('query', '')
            url = data.get('url', '')
            if query:
                link = coupang_partners.get_deeplink_for_query(query)
                self._send_json({"success": True, "query": query, "shortenUrl": link})
            elif url:
                links = coupang_partners.generate_deeplinks([url])
                if links:
                    self._send_json({"success": True, "data": links[0]})
                else:
                    self._send_json({"success": False, "error": "Failed to generate deeplink"}, 500)
            else:
                self._send_json({"success": False, "error": "query or url required"}, 400)
            return

        elif parsed.path == '/api/tokens/generate':
            import survey_token_manager as stm
            note = data.get('note', '')
            count = int(data.get('count', 1))
            created = []
            for _ in range(max(1, min(count, 50))):
                t = stm.generate_token(note=note)
                if t:
                    created.append(t)
            self._send_json({"success": True, "tokens": created, "token": created[0] if created else None})
            return

        elif parsed.path == '/api/tokens/delete':
            import survey_token_manager as stm
            token = data.get('token', '')
            res = stm.delete_token(token)
            self._send_json({"success": res})
            return

        elif parsed.path == '/api/tokens/reset':
            import survey_token_manager as stm
            token = data.get('token', '')
            res = stm.reset_token(token)
            self._send_json({"success": res})
            return

        elif parsed.path == '/api/tokens/import':
            tokens_in = data.get('tokens', {})
            import survey_token_manager as stm
            curr = stm._load_tokens()
            curr.update(tokens_in)
            stm._save_tokens(curr)
            self._send_json({"success": True, "count": len(curr), "tokens": curr})
            return



        elif parsed.path in ['/api/create-diet-client', '/api/create-client']:
            token = data.get('token', '').strip()
            is_admin = data.get('admin', False)

            if token and not is_admin:
                valid, msg = stm.verify_token(token)
                if not valid:
                    self._send_json({"success": False, "error": f"1회용 초대 코드가 유효하지 않습니다: {msg}"}, 403)
                    return

            name = data.get('name', '회원님')
            age = data.get('age', '30세')
            gender = data.get('gender', '남성')
            height = data.get('height', '175')
            weight = data.get('weight', '75')
            target_weight = data.get('target_weight', '68')
            activity_level = data.get('activity_level', '좌식 생활')
            workout_type = data.get('workout_type', '웨이트')
            workout_freq = data.get('workout_freq', '주 3~4회')
            workout_duration = data.get('workout_duration', '30분~1시간')
            meal_count = data.get('meal_count', '하루 3끼')
            delivery_freq = data.get('delivery_freq', '주 2~3회')
            snack_habit = data.get('snack_habit', '없음')
            meal_target = data.get('meal_target', '점심만')
            health_notes = data.get('health_notes', '없음')
            budget = int(data.get('budget', 250000))
            goal_notes = data.get('goal_notes', '')

            import re
            from urllib.parse import quote
            clean_name = re.sub(r'[^\w가-힣]', '', name.strip()) or '회원님'
            clean_age = re.sub(r'[^\w가-힣]', '', age.strip()) or '연령미상'
            base_id = f"{clean_name}_{clean_age}"
            client_id = base_id

            count = 2
            target_clients_dir = os.path.join(DIRECTORY, "clients")
            while os.path.exists(os.path.join(target_clients_dir, client_id)):
                client_id = f"{base_id}_{count}"
                count += 1

            print(f"[DietBot API] Creating diet client [{client_id}] for {name} ({gender}, {height}cm, {weight}kg -> {target_weight}kg, {meal_target})...")
            try:
                sys.path.insert(0, os.path.join(DIRECTORY, "generator"))
                import importlib
                import diet_calculator
                import build_client as builder
                importlib.reload(diet_calculator)
                importlib.reload(builder)

                # 다이어트 매크로 & 원물 식단 계산
                diet_analysis = diet_calculator.calculate_diet_macro(
                    age=age.replace('세', ''),
                    gender=gender,
                    height_cm=height,
                    weight_kg=weight,
                    target_weight_kg=target_weight,
                    activity_level=activity_level,
                    workout_type=workout_type,
                    workout_freq=workout_freq,
                    workout_duration=workout_duration,
                    meal_change_target=meal_target,
                    budget=budget,
                    allergies=health_notes
                )

                # 포털 빌더 호출
                builder.build_client(
                    client_id=client_id,
                    name=name,
                    age=age,
                    household="1명",
                    budget=budget,
                    frequency=f"{meal_target} 클린 원물 식단",
                    goal="다이어트 챌린지",
                    cuisine="클린 원물 식단 (닭가슴살, 샐러드, 고단백 두유)",
                    exclude=health_notes,
                    pantry="",
                    goal_notes=goal_notes,
                    diet_analysis=diet_analysis
                )

                # client_info.json에 정밀 다이어트 데이터 추가 기록
                c_info_file = os.path.join(target_clients_dir, client_id, "client_info.json")
                if os.path.exists(c_info_file):
                    try:
                        with open(c_info_file, "r", encoding="utf-8") as f:
                            c_info = json.load(f)
                        c_info["diet_analysis"] = diet_analysis
                        c_info["gender"] = gender
                        c_info["height_cm"] = height
                        c_info["weight_kg"] = weight
                        c_info["target_weight_kg"] = target_weight
                        c_info["activity_level"] = activity_level
                        c_info["workout_type"] = workout_type
                        c_info["workout_freq"] = workout_freq
                        c_info["meal_target"] = meal_target
                        c_info["health_notes"] = health_notes
                        with open(c_info_file, "w", encoding="utf-8") as f:
                            json.dump(c_info, f, ensure_ascii=False, indent=2)
                    except Exception as ex:
                        print(f"[Warning] Failed to enrich client_info.json: {ex}")

                # clients.html 자동 동기화
                try:
                    dash_script = os.path.join(DIRECTORY, "scratch", "generate_clients_dashboard.py")
                    if os.path.exists(dash_script):
                        with open(dash_script, "r", encoding="utf-8") as f:
                            exec(f.read(), {"__name__": "__main__"})
                except Exception as ex:
                    print(f"[Warning] Failed to update clients.html: {ex}")
                finally:
                    gc.collect()

                # 토큰 소멸
                if token and not is_admin:
                    try:
                        host = self.headers.get('Host', f'localhost:{PORT}')
                        mobile_base = get_public_tunnel_url(host=host)
                        stm.mark_token_used(
                            token=token,
                            client_id=client_id,
                            client_name=name,
                            portal_url=f"{mobile_base}/clients/{quote(client_id)}/index.html"
                        )
                    except Exception as ex:
                        print(f"[Warning] Failed to mark token used: {ex}")

                # GitHub 동기화
                try:
                    import github_sync
                    github_sync.trigger_async_sync(f"feat: auto-sync diet client {client_id}")
                except Exception as ex:
                    print(f"[Warning] Failed to trigger git sync: {ex}")

                host = self.headers.get('Host', f'localhost:{PORT}')
                encoded_client_id = quote(client_id)
                mobile_base = get_public_tunnel_url(host=host)

                self._send_json({
                    "success": True,
                    "client_id": client_id,
                    "portal_url": f"{mobile_base}/clients/{encoded_client_id}/index.html",
                    "cart_url": f"{mobile_base}/clients/{encoded_client_id}/cart.html",
                    "local_portal_url": f"http://localhost:{PORT}/clients/{encoded_client_id}/index.html",
                    "local_cart_url": f"http://localhost:{PORT}/clients/{encoded_client_id}/cart.html",
                    "diet_analysis": diet_analysis
                })
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"[API Error] Failed to build diet client: {e}")
                self._send_json({"success": False, "error": str(e)}, 500)
            return

            import time
            token = data.get('token', '').strip()
            is_admin = bool(data.get('admin', False)) or (token == 'ADMIN_MASTER')

            import survey_token_manager as stm
            if not is_admin:
                if not token:
                    self._send_json({
                        "success": False,
                        "error": "⛔ 1회용 설문 초대 코드가 필요합니다. 초대 링크를 통해 접속해 주세요."
                    }, 400)
                    return
                token_check = stm.verify_token(token)
                if token_check.get("status") == "already_used":
                    self._send_json({
                        "success": False,
                        "error": "⚠️ 이미 작성이 완료된 1회용 설문 링크입니다.",
                        "status": "already_used",
                        "portal_url": token_check.get("portal_url")
                    }, 400)
                    return
                elif token_check.get("status") != "valid":
                    self._send_json({
                        "success": False,
                        "error": "⛔ 유효하지 않거나 만료된 초대 코드입니다."
                    }, 400)
                    return

            name = data.get('name', '고객님')
            age = data.get('age', '30대')
            household = data.get('household', '1명')
            budget = int(data.get('budget', 300000))
            frequency = data.get('frequency', '저녁만 (30끼)')
            concept = data.get('concept', '다이어트')
            cuisine = data.get('cuisine', '한식, 일식')
            exclude = data.get('exclude', '없음')
            pantry = data.get('pantry', '아무것도 없음')
            goal_notes = data.get('goal_notes', '')

            import re
            from urllib.parse import quote
            clean_name = re.sub(r'[^\w가-힣]', '', name.strip()) or '고객님'
            clean_age = re.sub(r'[^\w가-힣]', '', age.strip()) or '연령미상'
            base_id = f"{clean_name}_{clean_age}"
            client_id = base_id

            # 동명이인/재설문 시 폴더 중복 방지 (예: 이보환_27세, 이보환_27세_2)
            count = 2
            target_clients_dir = os.path.join(DIRECTORY, "clients")
            while os.path.exists(os.path.join(target_clients_dir, client_id)):
                client_id = f"{base_id}_{count}"
                count += 1

            print(f"[API] Creating client folder [{client_id}] for {name} ({household}, {budget:,}원, {concept}, {cuisine})...")
            try:
                sys.path.insert(0, os.path.join(DIRECTORY, "generator"))
                import importlib
                import recipe_engine
                import build_client as builder
                importlib.reload(recipe_engine)
                importlib.reload(builder)
                builder.build_client(
                    client_id=client_id,
                    name=name,
                    age=age,
                    household=household,
                    budget=budget,
                    frequency=frequency,
                    goal=concept,
                    cuisine=cuisine,
                    exclude=exclude,
                    pantry=pantry,
                    goal_notes=goal_notes
                )

                # clients.html 자동 동기화 갱신 (메모리 절약을 위해 subprocess 대신 in-process 실행)
                try:
                    dash_script = os.path.join(DIRECTORY, "scratch", "generate_clients_dashboard.py")
                    if os.path.exists(dash_script):
                        with open(dash_script, "r", encoding="utf-8") as f:
                            exec(f.read(), {"__name__": "__main__"})
                except Exception as ex:
                    print(f"[Warning] Failed to update clients.html: {ex}")
                finally:
                    gc.collect()

                # 1회용 초대 토큰 소멸 처리 (영구 재작성 방지)
                if token and not is_admin:
                    try:
                        stm.mark_token_used(
                            token=token,
                            client_id=client_id,
                            client_name=name,
                            portal_url=f"https://bohwan100.github.io/zipbab/clients/{quote(client_id)}/index.html"
                        )
                    except Exception as ex:
                        print(f"[Warning] Failed to mark token used: {ex}")

                # GitHub 자동 영구 보존 동기화 (Auto-Sync)
                try:
                    import github_sync
                    github_sync.trigger_async_sync(f"feat: auto-sync client {client_id}")
                except Exception as ex:
                    print(f"[Warning] Failed to trigger git sync: {ex}")

                host = self.headers.get('Host', f'localhost:{PORT}')
                encoded_client_id = quote(client_id)
                mobile_base = get_public_tunnel_url(host=host)
                cdn_base = mobile_base

                self._send_json({
                    "success": True,
                    "client_id": client_id,
                    "portal_url": f"{cdn_base}/clients/{encoded_client_id}/index.html",
                    "cart_url": f"{cdn_base}/clients/{encoded_client_id}/cart.html",
                    "cdn_portal_url": f"{cdn_base}/clients/{encoded_client_id}/index.html",
                    "cdn_cart_url": f"{cdn_base}/clients/{encoded_client_id}/cart.html",
                    "render_portal_url": f"{mobile_base}/clients/{encoded_client_id}/index.html",
                    "render_cart_url": f"{mobile_base}/clients/{encoded_client_id}/cart.html",
                    "mobile_portal_url": f"{cdn_base}/clients/{encoded_client_id}/index.html",
                    "mobile_cart_url": f"{cdn_base}/clients/{encoded_client_id}/cart.html",
                    "local_portal_url": f"http://localhost:{PORT}/clients/{encoded_client_id}/index.html",
                    "local_cart_url": f"http://localhost:{PORT}/clients/{encoded_client_id}/cart.html",
                    "public_tunnel_url": cdn_base,
                    "survey_public_url": f"{cdn_base}/survey.html"
                })
            except Exception as e:
                print(f"[API Error] Failed to build client: {e}")
                self._send_json({"success": False, "error": str(e)}, 500)
            return

        elif parsed.path == '/api/delete-client':
            import shutil
            import unicodedata

            client_ids = data.get('client_ids', [])
            single_id = data.get('client_id')
            if single_id and single_id not in client_ids:
                client_ids.append(single_id)

            if not client_ids:
                self._send_json({"success": False, "error": "client_id or client_ids required"}, 400)
                return

            clients_base = os.path.abspath(os.path.join(DIRECTORY, "clients"))
            deleted = []
            errors = []

            for cid in client_ids:
                if not cid or not isinstance(cid, str):
                    continue
                cid_nfc = unicodedata.normalize('NFC', cid.strip())
                cid_nfd = unicodedata.normalize('NFD', cid.strip())

                matched_dir = None
                if os.path.exists(clients_base):
                    for entry in os.listdir(clients_base):
                        entry_nfc = unicodedata.normalize('NFC', entry)
                        entry_nfd = unicodedata.normalize('NFD', entry)
                        if entry == cid or entry_nfc == cid_nfc or entry_nfd == cid_nfd:
                            matched_dir = os.path.join(clients_base, entry)
                            break

                if not matched_dir or not os.path.isdir(matched_dir):
                    errors.append(f"Folder not found: {cid}")
                    continue

                real_path = os.path.abspath(matched_dir)
                if not real_path.startswith(clients_base) or real_path == clients_base:
                    errors.append(f"Invalid path: {cid}")
                    continue

                try:
                    shutil.rmtree(real_path)
                    deleted.append(cid)
                    print(f"[API] Successfully deleted client folder: {real_path}")
                except Exception as err:
                    errors.append(f"Failed to delete {cid}: {str(err)}")

            # clients_registry.json 동기화 (삭제된 고객 영구 제거 및 최신순 정렬 보존)
            if deleted:
                try:
                    reg_file = os.path.join(DIRECTORY, "data", "clients_registry.json")
                    if os.path.exists(reg_file):
                        with open(reg_file, "r", encoding="utf-8") as f:
                            reg_data = json.load(f)
                        changed = False
                        for d_cid in deleted:
                            if d_cid in reg_data:
                                del reg_data[d_cid]
                                changed = True
                        if changed:
                            with open(reg_file, "w", encoding="utf-8") as f:
                                json.dump(reg_data, f, ensure_ascii=False, indent=2)
                except Exception as ex:
                    print(f"[Warning] Failed to update clients_registry.json after delete: {ex}")

            # clients.html 자동 동기화 갱신 (메모리 절약을 위해 subprocess 대신 in-process 실행)
            try:
                dash_script = os.path.join(DIRECTORY, "scratch", "generate_clients_dashboard.py")
                if os.path.exists(dash_script):
                    with open(dash_script, "r", encoding="utf-8") as f:
                        exec(f.read(), {"__name__": "__main__"})

            except Exception as ex:
                print(f"[Warning] Failed to update clients.html after delete: {ex}")
            finally:
                gc.collect()

            # GitHub 자동 영구 보존 동기화 (Auto-Sync)
            try:
                import github_sync
                github_sync.trigger_async_sync(f"feat: auto-sync delete clients {', '.join(deleted)}")
            except Exception as ex:
                print(f"[Warning] Failed to trigger git sync: {ex}")

            self._send_json({
                "success": len(deleted) > 0,
                "deleted": deleted,
                "errors": errors,
                "remaining_count": len([d for d in os.listdir(clients_base) if os.path.isdir(os.path.join(clients_base, d))]) if os.path.exists(clients_base) else 0
            })
            return

        self.send_error(404, "Endpoint not found")

    def _send_json(self, data, status=200):
        response_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    timeout = 10

def run():
    httpd = ThreadedHTTPServer(("", PORT), CoupangAutoServer)
    print(f"🚀 [Coupang Auto Server] Serving on http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run()
