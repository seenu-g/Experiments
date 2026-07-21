"""
Unit tests for agent.py: history persistence, tools that can fail, and the
confirm-required gating around destructive tools. Deterministic, no live
model calls (ollama.chat is mocked where needed). Run with: python test_agent.py
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent
import tools


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


class TestReadFile(unittest.TestCase):
    def test_reads_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("hello world")
            path = f.name
        self.assertEqual(tools.read_file(path), "hello world")

    def test_missing_file_gives_friendly_message(self):
        result = tools.read_file("no_such_file_xyz.txt")
        self.assertEqual(result, "error: no file found at 'no_such_file_xyz.txt'")

    def test_directory_gives_a_friendly_message_not_a_raw_traceback(self):
        # On Windows this surfaces as PermissionError, on Linux/Mac as IsADirectoryError --
        # either way it must be one of our friendly messages, not a raw stack trace.
        with tempfile.TemporaryDirectory() as d:
            result = tools.read_file(d)
        self.assertTrue(
            "no permission to read" in result or "is a directory" in result,
            result,
        )


class TestDeleteFile(unittest.TestCase):
    def test_deletes_existing_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        result = tools.delete_file(path)
        self.assertEqual(result, f"deleted {path}")
        self.assertFalse(Path(path).exists())

    def test_missing_file_gives_friendly_message(self):
        result = tools.delete_file("no_such_file_xyz.txt")
        self.assertEqual(result, "error: no file found at 'no_such_file_xyz.txt'")

    def test_directory_gives_a_friendly_message_not_a_raw_traceback(self):
        with tempfile.TemporaryDirectory() as d:
            result = tools.delete_file(d)
        self.assertTrue(
            "no permission to delete" in result or "is a directory" in result,
            result,
        )


def _fake_tool_call_response(name, args):
    return {
        "message": {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"function": {"name": name, "arguments": args}}],
        }
    }


def _fake_final_response(text):
    return {"message": {"role": "assistant", "content": text, "tool_calls": None}}


class TestConfirmRequiredGating(unittest.TestCase):
    def setUp(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            self.path = f.name

    def tearDown(self):
        Path(self.path).unlink(missing_ok=True)

    @patch("agent.ollama.chat")
    def test_denied_confirmation_skips_execution(self, mock_chat):
        mock_chat.side_effect = [
            _fake_tool_call_response("delete_file", {"path": self.path}),
            _fake_final_response("ok, I did not delete it"),
        ]
        messages = agent.run_agent("delete that file", [], confirm=lambda name, args: False)

        self.assertTrue(Path(self.path).exists())  # never deleted
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        self.assertIn("denied by user", tool_messages[0]["content"])

    @patch("agent.ollama.chat")
    def test_approved_confirmation_executes(self, mock_chat):
        mock_chat.side_effect = [
            _fake_tool_call_response("delete_file", {"path": self.path}),
            _fake_final_response("done"),
        ]
        messages = agent.run_agent("delete that file", [], confirm=lambda name, args: True)

        self.assertFalse(Path(self.path).exists())  # actually deleted
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        self.assertIn("deleted", tool_messages[0]["content"])

    @patch("agent.ollama.chat")
    def test_non_gated_tool_ignores_confirm(self, mock_chat):
        mock_chat.side_effect = [
            _fake_tool_call_response("calculate", {"expression": "2+2"}),
            _fake_final_response("4"),
        ]
        # confirm always denies, but calculate isn't in CONFIRM_REQUIRED so it must still run
        messages = agent.run_agent("what is 2+2", [], confirm=lambda name, args: False)
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        self.assertEqual(tool_messages[0]["content"], "4")


if __name__ == "__main__":
    unittest.main(verbosity=2)
