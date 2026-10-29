import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DEEPSEEK_KEEPALIVE_ENABLED", "false")

from app import create_app
from services.agent_service import run_agent


def completion_with(content=None, tool_calls=None):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeCompletions:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(
                id="call_1",
                function=SimpleNamespace(
                    name="search_products",
                    arguments=json.dumps(
                        {"category": "耳机", "budget_min": 0, "budget_max": 200},
                        ensure_ascii=False,
                    ),
                ),
            )
            return completion_with(tool_calls=[tool_call])
        return completion_with(
            content=json.dumps(
                {
                    "answer": "已找到 200 元内的耳机方案。",
                    "plans": [
                        {
                            "name": "通勤耳机",
                            "desc": "预算内方案",
                            "items": [
                                {
                                    "id": "D009",
                                    "name": "主动降噪蓝牙耳机",
                                    "quantity": 1,
                                    "price": 149,
                                    "final_price": 117.29,
                                    "platform": "京东",
                                }
                            ],
                            "total_price": 117.29,
                            "advantage": "支持降噪",
                        }
                    ],
                    "requires_input": False,
                    "suggested_replies": ["再便宜一点"],
                },
                ensure_ascii=False,
            )
        )


class DeepSeekResidentTests(unittest.TestCase):
    def test_health_ready_with_deepseek_connection(self):
        connected_status = {
            "connected": True,
            "checking": False,
            "last_check_at": 1730000000.0,
            "last_success_at": 1730000000.0,
            "last_error": "",
        }
        with (
            patch("services.agent_service.get_deepseek_connection_status", return_value=connected_status),
            patch.dict(
                os.environ,
                {
                    "LLM_PROVIDER": "deepseek",
                    "DEEPSEEK_API_KEY": "sk-test-key",
                    "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
                    "DEEPSEEK_MODEL": "deepseek-flash",
                    "ALLOW_LOCAL_FALLBACK": "false",
                },
            ),
        ):
            client = create_app().test_client()
            health = client.get("/health")
            ready = client.get("/ready")

        self.assertEqual(health.status_code, 200)
        config = health.get_json()["config_status"]
        self.assertTrue(config["deepseek_connected"])
        self.assertFalse(config["deepseek_connecting"])
        self.assertTrue(config["deepseek_resident"])
        self.assertTrue(config["llm_ready"])
        self.assertFalse(config["local_fallback_enabled"])
        self.assertEqual(ready.status_code, 200)
        self.assertTrue(ready.get_json()["deepseek_resident"])

    def test_ready_fails_for_placeholder_key(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "deepseek",
                "DEEPSEEK_API_KEY": "your_deepseek_api_key_here",
            },
        ):
            client = create_app().test_client()
            health = client.get("/health")
            ready = client.get("/ready")

        self.assertEqual(health.status_code, 200)
        self.assertFalse(health.get_json()["config_status"]["deepseek_resident"])
        self.assertEqual(ready.status_code, 503)
        self.assertFalse(ready.get_json()["deepseek_resident"])

    def test_frontend_assets_are_served_locally(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "deepseek",
                "DEEPSEEK_API_KEY": "sk-test-key",
            },
        ):
            client = create_app().test_client()
            page = client.get("/")
            tailwind = client.get("/assets/tailwindcss.js")
            crypto_js = client.get("/assets/crypto-js.min.js")
            worker = client.get("/assets/password-worker.js")
            service_worker = client.get("/sw.js")
            manifest = client.get("/manifest.webmanifest")
            runtime_config = client.get("/runtime-config.js")
            icon = client.get("/assets/app-icon.svg")

        responses = (
            page,
            tailwind,
            crypto_js,
            worker,
            service_worker,
            manifest,
            runtime_config,
            icon,
        )
        try:
            self.assertEqual(page.status_code, 200)
            html = page.get_data(as_text=True)
            self.assertIn("assets/tailwindcss.js", html)
            self.assertIn("assets/crypto-js.min.js", html)
            self.assertIn("manifest.webmanifest", html)
            self.assertIn("runtime-config.js", html)
            self.assertNotIn("https://cdn.tailwindcss.com", html)
            self.assertIn("LIFE_WALLET_CONFIG", runtime_config.get_data(as_text=True))
            for response in (
                tailwind,
                crypto_js,
                worker,
                service_worker,
                manifest,
                runtime_config,
                icon,
            ):
                self.assertEqual(response.status_code, 200)
                self.assertGreater(len(response.get_data()), 100)
        finally:
            for response in responses:
                response.close()

    def test_run_agent_uses_tools_with_injected_client(self):
        fake_completions = FakeCompletions()
        fake_client = SimpleNamespace(chat=SimpleNamespace(completions=fake_completions))
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "deepseek",
                "DEEPSEEK_MODEL": "deepseek-flash",
            },
        ):
            result = run_agent("预算200元推荐耳机", client=fake_client)

        self.assertEqual(result["used_tools"], ["search_products"])
        self.assertFalse(result["requires_input"])
        self.assertIn("耳机", result["answer"])
        self.assertEqual(len(fake_completions.calls), 2)
        self.assertEqual(fake_completions.calls[0]["model"], "deepseek-flash")
        self.assertEqual(fake_completions.calls[0]["tool_choice"], "auto")
        self.assertIn("timeout", fake_completions.calls[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)