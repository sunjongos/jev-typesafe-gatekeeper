"""Local-only SMS comparison UI. Run: python web_app.py"""
import json
import os
import secrets
import threading
import time
from contextlib import ExitStack
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import jev

ROOT = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
RACE_MODELS = ("luna", "terra", "sol", "haiku", "sonnet", "opus", "gemini", "jev")
# 모델끼리는 병렬, 같은 모델의 중복 요청은 차단한다.
LOCKS = {key: threading.Lock() for key in RACE_MODELS}
STACKS = {key: ExitStack() for key in RACE_MODELS}
CLIENTS = {key: {} for key in RACE_MODELS}


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, content_type="application/json; charset=utf-8"):
        body = json.dumps(data, ensure_ascii=False).encode() if isinstance(data, dict) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def local_host(self):
        return self.headers.get("Host") in (f"127.0.0.1:{self.server.server_port}",
                                           f"localhost:{self.server.server_port}")

    def do_GET(self):
        if not self.local_host():
            return self.reply(403, {"error": "로컬 주소로 접속해 주세요."})
        if self.path == "/":
            return self.reply(200, (ROOT / "web" / "index.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/assets/ucanlabs-logo.png":
            return self.reply(200, (ROOT / "web" / "assets" / "ucanlabs-logo.png").read_bytes(), "image/png")
        if self.path == "/api/config":
            models = []
            for key in RACE_MODELS:
                name, provider, model_id, prices = jev.모델들[key]
                env = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "jev": "TYPESAFE_API_KEY"}[provider]
                models.append({"key": key, "name": name, "provider": provider,
                               "ready": bool(os.getenv(env)) if env else True,
                               "note": "키 미설정" if not os.getenv(env) else "API 키 설정됨",
                               "prices": prices})
            return self.reply(200, {"token": TOKEN, "models": models, "messages": jev.messages})
        return self.reply(404, {"error": "찾을 수 없습니다."})

    def do_POST(self):
        if not self.local_host() or not secrets.compare_digest(self.headers.get("X-Run-Token", ""), TOKEN):
            return self.reply(403, {"error": "페이지를 새로고침해 주세요."})
        if self.path != "/api/run":
            return self.reply(404, {"error": "찾을 수 없습니다."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length < 4096:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            key, case = data["model"], data["case"]
            if key not in RACE_MODELS or type(case) is not int or not 0 <= case < len(jev.messages):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            return self.reply(400, {"error": "모델과 케이스를 확인해 주세요."})
        lock = LOCKS[key]
        if not lock.acquire(blocking=False):
            return self.reply(409, {"error": "같은 모델이 다른 요청을 처리 중입니다. 완료 후 다시 실행해 주세요."})
        start = time.perf_counter()
        try:
            ask = jev.make_ask(key, STACKS[key], CLIENTS[key])
            result = ask(jev.messages[case])
            i, o = result["input_tokens"], result["output_tokens"]
            prices = jev.모델들[key][3]
            result.update(model=key, case=case, elapsed=time.perf_counter() - start,
                          cost=(i * prices[0] + o * prices[1]) / 1_000_000 if i is not None and o is not None else None)
            self.reply(200, result)
        except Exception as exc:
            # SDK errors can contain account identifiers or request URLs. Keep them server-side.
            error_type = type(exc).__name__
            code = getattr(exc, "status_code", None)
            note = {401: "API 키 인증에 실패했습니다.", 403: "이 모델의 호출 권한이 없습니다.",
                    404: "모델을 사용할 수 없습니다.", 429: "요청 한도 또는 API 잔액을 확인해 주세요.",
                    400: "API 요청 설정 또는 계정 결제 상태를 확인해 주세요."}.get(
                        code, "API 키·모델 접근 권한·할당량·네트워크 상태를 확인해 주세요.")
            self.reply(200, {"model": key, "case": case, "error": f"{error_type}: {note}",
                             "elapsed": time.perf_counter() - start, "cost": None})
        finally:
            lock.release()

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("문자 분류 비교: http://127.0.0.1:8765  (종료: Ctrl+C)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        for stack in STACKS.values():
            stack.close()
