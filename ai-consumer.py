#!/usr/bin/env python3
"""Simple vLLM client for single request and stress mode."""

from __future__ import annotations

import argparse
import json
import logging
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict

DEFAULT_PROMPT = "Who are you?, and what can you do?"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-3B-Instruct"
LOGGER = logging.getLogger("vllm_request")


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="vLLM request helper: single chat completion or optional stress test."
    )
    parser.add_argument(
        "-u",
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"vLLM base URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        default=DEFAULT_PROMPT,
        help="question for single mode",
    )
    parser.add_argument(
        "--stress",
        action="store_true",
        help="run parallel stress test instead of single request",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="number of requests for stress mode (default: 50)",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=8,
        help="number of parallel workers for stress mode (default: 8)",
    )
    return parser.parse_args()


def main() -> int:
    configure_logger()
    args = parse_args()

    if args.stress:
        return run_stress(args.base_url, args.model, args.count, args.parallel)

    return run_single(args.base_url, args.model, args.prompt)


if __name__ == "__main__":
    raise SystemExit(main())
