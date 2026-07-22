#!/usr/bin/env python3
"""Simple vLLM client for single request and stress mode."""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

DEFAULT_PROMPT = "Who are you?, and what can you do?"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
LOGGER = logging.getLogger("vllm_request")
ENV_FILE = ".env"


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_int(value: str | None, default: int) -> int:
    if value is None or value.strip() == "":
        return default
    try:
        return int(value)
    except ValueError:
        LOGGER.warning("invalid integer value '%s', using default %s", value, default)
        return default


def load_dotenv(path: str) -> None:
    dotenv_path = Path(path)
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            # Keep explicit environment variables as higher priority than .env values.
            os.environ.setdefault(key, value)


@dataclass
class RequestResult:
    index: int
    status_code: int
    elapsed: float
    response_text: str


def configure_logger() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def post_json(url: str, payload: dict, timeout: float = 120.0) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.getcode(), body
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        return err.code, body


def extract_content(response_text: str) -> str | None:
    try:
        parsed = json.loads(response_text)
        return parsed["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return None


def run_single(base_url: str, model: str, prompt: str) -> int:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 80,
    }
    endpoint = f"{base_url.rstrip('/')}/v1/chat/completions"

    status_code, body = post_json(endpoint, payload)
    LOGGER.info("status: %s", status_code)

    if status_code == 200:
        content = extract_content(body)
        if content is not None:
            print(content)
        else:
            print(body)
    else:
        try:
            parsed = json.loads(body)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            print(body)

    return 0 if status_code == 200 else 1


def run_stress(base_url: str, model: str, count: int, parallel: int) -> int:
    endpoint = f"{base_url.rstrip('/')}/v1/chat/completions"
    LOGGER.info("stress mode: count=%s parallel=%s", count, parallel)

    def run_one(i: int) -> RequestResult:
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": f"Test #{i}: napisz 6 nie powtarzajacych sie slow o AI"}
            ],
            "temperature": 0.7,
            "max_tokens": 64,
        }
        start = time.perf_counter()
        status_code, body = post_json(endpoint, payload)
        elapsed = time.perf_counter() - start
        return RequestResult(index=i, status_code=status_code, elapsed=elapsed, response_text=body)

    summary: Dict[int, int] = {}
    failures = 0

    with ThreadPoolExecutor(max_workers=parallel) as pool:
        futures = [pool.submit(run_one, i) for i in range(1, count + 1)]

        for future in as_completed(futures):
            result = future.result()
            summary[result.status_code] = summary.get(result.status_code, 0) + 1
            LOGGER.info("%s %s %.3fs", result.index, result.status_code, result.elapsed)
            if result.status_code == 200:
                content = extract_content(result.response_text)
                if content is not None:
                    LOGGER.info("%s content: %s", result.index, content)
                else:
                    LOGGER.info("%s content: <unavailable>", result.index)
            if result.status_code != 200:
                failures += 1

    print("\nStatus summary:")
    for status_code in sorted(summary):
        print(f"{status_code} {summary[status_code]}")

    return 0 if failures == 0 else 1


def run_repeating(task_name: str, interval_minutes: float, task: callable) -> int:
    if interval_minutes <= 0:
        return task()

    interval_seconds = interval_minutes * 60.0
    cycle = 1

    try:
        while True:
            started_at = time.time()
            LOGGER.info("cycle %s started (%s mode)", cycle, task_name)
            exit_code = task()
            if exit_code != 0:
                LOGGER.warning("cycle %s finished with code %s", cycle, exit_code)
            else:
                LOGGER.info("cycle %s finished successfully", cycle)

            cycle += 1
            next_run_at = started_at + interval_seconds
            sleep_for = max(0.0, next_run_at - time.time())
            LOGGER.info("next cycle in %.2f minute(s)", sleep_for / 60.0)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        LOGGER.info("stopped by user")
        return 130


def parse_args() -> argparse.Namespace:
    bootstrap_parser = argparse.ArgumentParser(add_help=False)
    bootstrap_parser.add_argument(
        "--env-file",
        default=ENV_FILE,
        help=f"path to .env file (default: {ENV_FILE})",
    )
    bootstrap_args, _ = bootstrap_parser.parse_known_args()
    load_dotenv(bootstrap_args.env_file)

    default_base_url = os.getenv("VLLM_BASE_URL", DEFAULT_BASE_URL)
    default_model = os.getenv("VLLM_MODEL", DEFAULT_MODEL)
    default_prompt = os.getenv("VLLM_PROMPT", DEFAULT_PROMPT)
    default_stress = parse_bool(os.getenv("VLLM_STRESS"), default=False)
    default_count = parse_int(os.getenv("VLLM_COUNT"), default=50)
    default_parallel = parse_int(os.getenv("VLLM_PARALLEL"), default=8)
    default_repeat_minutes = float(os.getenv("VLLM_REPEAT_MINUTES", "0"))

    parser = argparse.ArgumentParser(
        description="vLLM request helper: single chat completion or optional stress test."
    )
    parser.add_argument(
        "--env-file",
        default=bootstrap_args.env_file,
        help=f"path to .env file (default: {ENV_FILE})",
    )
    parser.add_argument(
        "-u",
        "--base-url",
        default=default_base_url,
        help=f"vLLM base URL (env: VLLM_BASE_URL, default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--model",
        default=default_model,
        help=f"model name (env: VLLM_MODEL, default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        default=default_prompt,
        help="question for single mode",
    )
    parser.add_argument(
        "--stress",
        action="store_true",
        default=default_stress,
        help="run parallel stress test instead of single request",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=default_count,
        help="number of requests for stress mode (env: VLLM_COUNT, default: 50)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=default_parallel,
        help="number of parallel workers for stress mode (env: VLLM_PARALLEL, default: 8)",
    )
    parser.add_argument(
        "--repeat-minutes",
        type=float,
        default=default_repeat_minutes,
        help="repeat full cycle every N minutes for single or stress mode (env: VLLM_REPEAT_MINUTES, default: 0 - disabled)",
    )
    return parser.parse_args()


def main() -> int:
    configure_logger()
    args = parse_args()

    if args.stress:
        return run_repeating(
            task_name="stress",
            interval_minutes=args.repeat_minutes,
            task=lambda: run_stress(args.base_url, args.model, args.count, args.parallel),
        )

    return run_repeating(
        task_name="single",
        interval_minutes=args.repeat_minutes,
        task=lambda: run_single(args.base_url, args.model, args.prompt),
    )


if __name__ == "__main__":
    raise SystemExit(main())
