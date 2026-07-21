"""
Unit tests for history persistence in agent.py: load_history/save_history.
Deterministic, no model calls. Run with: python test_agent.py
"""
import json
import tempfile
import unittest
from pathlib import Path

import agent


class FakeMessage:
    """Stands in for ollama's pydantic Message object."""

    def __init__(self, data):
        self._data = data

    def model_dump(self, exclude_none=False):
        if exclude_none:
            return {k: v for k, v in self._data.items() if v is not None}
        return self._data


class TestHistoryPersistence(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_history_file = agent.HISTORY_FILE
        agent.HISTORY_FILE = Path(self._tmpdir.name) / "history.json"

    def tearDown(self):
        agent.HISTORY_FILE = self._orig_history_file
        self._tmpdir.cleanup()

    def test_missing_file_returns_default_system_prompt(self):
        history = agent.load_history()
        self.assertEqual(history, [{"role": "system", "content": agent.SYSTEM_PROMPT}])

    def test_round_trip_plain_dict_messages(self):
        original = [
            {"role": "system", "content": agent.SYSTEM_PROMPT},
            {"role": "user", "content": "hi"},
            {"role": "tool", "content": "42"},
        ]
        agent.save_history(original)
        self.assertEqual(agent.load_history(), original)

    def test_round_trip_converts_pydantic_message(self):
        history = [
            {"role": "user", "content": "what time is it?"},
            FakeMessage({"role": "assistant", "content": "it's 5pm", "tool_calls": None}),
        ]
        agent.save_history(history)
        loaded = agent.load_history()
        self.assertEqual(
            loaded,
            [
                {"role": "user", "content": "what time is it?"},
                {"role": "assistant", "content": "it's 5pm"},
            ],
        )

    def test_saved_file_is_valid_json_on_disk(self):
        agent.save_history([{"role": "user", "content": "hi"}])
        raw = json.loads(agent.HISTORY_FILE.read_text())
        self.assertEqual(raw, [{"role": "user", "content": "hi"}])

    def test_appending_and_saving_preserves_order(self):
        history = [{"role": "system", "content": agent.SYSTEM_PROMPT}]
        history.append({"role": "user", "content": "first"})
        history.append(FakeMessage({"role": "assistant", "content": "reply one"}))
        agent.save_history(history)

        loaded = agent.load_history()
        loaded.append({"role": "user", "content": "second"})
        agent.save_history(loaded)

        final = agent.load_history()
        roles = [m["role"] for m in final]
        contents = [m["content"] for m in final]
        self.assertEqual(roles, ["system", "user", "assistant", "user"])
        self.assertEqual(contents, [agent.SYSTEM_PROMPT, "first", "reply one", "second"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
