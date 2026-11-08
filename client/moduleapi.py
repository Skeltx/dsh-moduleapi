#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModuleAPI client — OpenAI-совместимый коннектор ("парсер") к ModuleAPI.

base_url: https://moduleapi.pro/v1
Один ключ — все модели (GPT, Claude, Gemini, Grok, DeepSeek и др.).
Формат: OpenAI Chat Completions (+ Responses, + /v1/models).

Ключ ищется по порядку:
  1. переменная окружения MODULE_API_KEY
  2. переменная окружения MODULEAPI_KEY
  3. файл ./moduleapi_config.json  ->  {"api_key": "sk-..."}
  4. файл ~/.moduleapi_key  (просто строка со значением sk-...)

Использование:
  python moduleapi.py models
  python moduleapi.py check
  python moduleapi.py ask "Привет" [--model deepseek-v4-pro]
      [--system "..." ] [--temperature 0.7] [--max-tokens 2048] [--stream]

Зависимости: только стандартная библиотека Python 3.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE_URL = "https://moduleapi.pro/v1"
DEFAULT_MODEL = "deepseek-v4-pro"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "moduleapi_config.json")
HOME_KEY_PATH = os.path.join(os.path.expanduser("~"), ".moduleapi_key")


# --------------------------------------------------------------------------- #
# Ключ
# --------------------------------------------------------------------------- #
def load_api_key() -> str:
    """Возвращает ключ из окружения или локального файла конфигурации."""
    for name in ("MODULE_API_KEY", "MODULEAPI_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value

    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            key = (cfg.get("api_key") or "").strip()
            if key:
                return key
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[warn] не удалось прочитать {CONFIG_PATH}: {exc}", file=sys.stderr)

    if os.path.isfile(HOME_KEY_PATH):
        try:
            with open(HOME_KEY_PATH, "r", encoding="utf-8") as fh:
                key = fh.read().strip()
            if key:
                return key
        except OSError as exc:
            print(f"[warn] не удалось прочитать {HOME_KEY_PATH}: {exc}", file=sys.stderr)

    return ""


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def _request(method: str, path: str, api_key: str, payload=None, stream=False):
    url = BASE_URL + path
    data = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    resp = urllib.request.urlopen(req)  # raises HTTPError on 4xx/5xx
    if stream:
        return resp
    body = resp.read().decode("utf-8", "replace")
    return json.loads(body) if body else {}


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    detail = ""
    try:
        detail = exc.read().decode("utf-8", "replace")
        detail = json.loads(detail).get("error", detail)
        if isinstance(detail, dict):
            detail = detail.get("message", json.dumps(detail, ensure_ascii=False))
        detail = str(detail)
    except Exception:
        detail = ""
    return f"HTTP {exc.code}: {detail}" if detail else f"HTTP {exc.code}"


# --------------------------------------------------------------------------- #
# Команды
# --------------------------------------------------------------------------- #
def cmd_models(api_key: str) -> None:
    data = _request("GET", "/models", api_key)
    models = data.get("data", [])
    if not models:
        print("Моделей не найдено (или ключ ограничен по моделям).")
        return
    ids = [m.get("id") for m in models if isinstance(m, dict)]
    ids = sorted(i for i in ids if i)
    print(f"Доступно моделей: {len(ids)}")
    for i in ids:
        print(" -", i)


def cmd_check(api_key: str) -> None:
    if not api_key:
        print("Ключ не найден. Задайте MODULE_API_KEY или moduleapi_config.json.",
              file=sys.stderr)
        sys.exit(2)
    try:
        data = _request("GET", "/models", api_key)
    except urllib.error.HTTPError as exc:
        print(_http_error_message(exc), file=sys.stderr)
        sys.exit(1)
    models = data.get("data", [])
    print(f"Ключ валиден. Доступно моделей: {len(models)}")
    for m in models:
        if isinstance(m, dict) and m.get("id"):
            print(" -", m["id"])


def cmd_ask(api_key: str, args) -> None:
    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})

    payload = {
        "model": args.model,
        "messages": messages,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    if args.stream:
        payload["stream"] = True
        try:
            resp = _request("POST", "/chat/completions", api_key, payload, stream=True)
        except urllib.error.HTTPError as exc:
            print(_http_error_message(exc), file=sys.stderr)
            sys.exit(1)
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line or not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                obj = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            delta = (obj.get("choices") or [{}])[0].get("delta") or {}
            piece = delta.get("content")
            if piece:
                sys.stdout.write(piece)
                sys.stdout.flush()
        print()
        return

    try:
        data = _request("POST", "/chat/completions", api_key, payload)
    except urllib.error.HTTPError as exc:
        print(_http_error_message(exc), file=sys.stderr)
        sys.exit(1)

    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        text = json.dumps(data, ensure_ascii=False, indent=2)

    if args.show_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="moduleapi.py",
        description="Коннектор к ModuleAPI (OpenAI-совместимый API).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("models", help="Список доступных моделей (GET /v1/models).")
    sub.add_parser("check", help="Проверить ключ и вывести доступные модели.")

    ask = sub.add_parser("ask", help="Отправить запрос в chat/completions.")
    ask.add_argument("prompt", help="Текст запроса.")
    ask.add_argument("--model", default=DEFAULT_MODEL, help=f"Модель (по умолчанию {DEFAULT_MODEL}).")
    ask.add_argument("--system", default=None, help="Системный промпт.")
    ask.add_argument("--temperature", type=float, default=0.7, help="Температура (0..2).")
    ask.add_argument("--max-tokens", type=int, default=2048, help="Максимум выходных токенов.")
    ask.add_argument("--stream", action="store_true", help="Стримить ответ (SSE).")
    ask.add_argument("--json", dest="show_json", action="store_true", help="Показать сырой JSON ответа.")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    api_key = load_api_key()

    if args.command == "models":
        cmd_models(api_key)
    elif args.command == "check":
        cmd_check(api_key)
    elif args.command == "ask":
        cmd_ask(api_key, args)


if __name__ == "__main__":
    main()
