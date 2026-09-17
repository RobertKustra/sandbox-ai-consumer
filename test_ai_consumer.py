import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "ai_consumer", Path(__file__).with_name("ai-consumer.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class FakeObservation:
    def __init__(self):
        self.updates = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def update(self, **kwargs):
        self.updates.append(kwargs)


class FakeLangfuse:
    def __init__(self):
        self.calls = []
        self.observations = []

    def start_as_current_observation(self, **kwargs):
        self.calls.append(kwargs)
        observation = FakeObservation()
        self.observations.append(observation)
        return observation


class AiConsumerTest(unittest.TestCase):
    @patch.dict(
        MODULE.os.environ,
        {"LANGFUSE_PUBLIC_KEY": "public", "LANGFUSE_SECRET_KEY": "secret"},
        clear=True,
    )
    def test_langfuse_uses_cluster_url_by_default(self):
        with patch.dict(sys.modules, {"langfuse": type("Sdk", (), {"get_client": lambda: object()})}):
            MODULE.create_langfuse_client()

        self.assertEqual(
            MODULE.os.environ["LANGFUSE_BASE_URL"], MODULE.DEFAULT_LANGFUSE_BASE_URL
        )

    def test_extract_usage_maps_openai_fields(self):
        body = json.dumps(
            {"usage": {"prompt_tokens": 4, "completion_tokens": 7, "total_tokens": 11}}
        )

        self.assertEqual(
            MODULE.extract_usage(body),
            {"input_tokens": 4, "output_tokens": 7, "total_tokens": 11},
        )

    @patch.object(MODULE, "post_json")
    def test_post_vllm_completion_records_generation(self, post_json):
        post_json.return_value = (
            200,
            json.dumps(
                {
                    "choices": [{"message": {"content": "hello"}}],
                    "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
                }
            ),
        )
        client = FakeLangfuse()
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "hi"}],
            "temperature": 0.8,
            "max_tokens": 80,
        }

        status_code, _ = MODULE.post_vllm_completion(
            client, "http://vllm/v1/chat/completions", payload, "single"
        )

        self.assertEqual(status_code, 200)
        self.assertEqual(client.calls[1]["as_type"], "generation")
        self.assertEqual(client.calls[1]["model"], "test-model")
        self.assertEqual(client.observations[1].updates[0]["output"], "hello")
        self.assertEqual(client.observations[1].updates[0]["usage_details"]["total_tokens"], 3)


if __name__ == "__main__":
    unittest.main()