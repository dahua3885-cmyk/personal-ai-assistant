from datetime import datetime, timedelta
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import workflows as w


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "assistant"
        w.core.init(self.root)
        self.cfg = w.core.config(self.root)
        self.cfg.update(channel="feishu", chat_id="oc_example", sender_id="ou_example")
        jobs = w.core.read_json(self.root / "automations.json")
        for job in jobs:
            if job["id"] in {"daily_chat", "meeting_inbox"}:
                job["enabled"] = True
        w.core.write_json(self.root / "automations.json", jobs)
        self.today = datetime.now(ZoneInfo(self.cfg["timezone"])).date().isoformat()
        self.answer = {"reply": "明确决定：周五汇总资料。负责人未明确。", "note": "", "should_notify": True}

    def add_chat(self, name="a.md", day=None, content="用户：周五整理资料\nAI：可以。"):
        target = self.root / "chats" / (day or self.today) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def test_upgrade_adds_defaults_without_resetting_old_settings(self):
        jobs = [{"id": "morning", "enabled": True, "scheduler_id": "existing-id", "schedule": "custom"}]
        w.core.write_json(self.root / "automations.json", jobs)
        w.core.init(self.root)
        result = w.core.read_json(self.root / "automations.json")
        self.assertEqual(result[0], jobs[0])
        self.assertEqual(sum(j["id"] == "daily_chat" for j in result), 1)
        self.assertFalse(next(j for j in result if j["id"] == "daily_chat")["enabled"])

    def test_empty_daily_run_costs_nothing(self):
        with patch.object(w.core, "generate") as model, patch.object(w.core, "deliver") as send:
            result = w.run_workflow(self.root, self.cfg, "daily_chat", send=True)
            self.assertTrue(all(r["status"] == "empty" for r in result["results"]))
            model.assert_not_called()
            send.assert_not_called()

    def test_import_is_deduplicated_and_validates_date(self):
        source = self.root.parent / "chat.txt"
        source.write_text("用户：决定先做文字版。", encoding="utf-8")
        one = w.import_chat(self.root, source, self.today)
        self.assertEqual(one, w.import_chat(self.root, source, self.today))
        self.assertEqual(len(list((self.root / "chats" / self.today).iterdir())), 1)
        with self.assertRaises(ValueError):
            w.import_chat(self.root, source, "../escape")

    def test_changed_inputs_same_day_create_new_revision(self):
        self.add_chat()
        with patch.object(w.core, "generate", return_value=self.answer) as model, patch.object(w.core, "deliver", return_value="om_done") as send:
            first = w.run_workflow(self.root, self.cfg, "daily_chat", send=True, day=self.today)
            w.run_workflow(self.root, self.cfg, "daily_chat", send=True, day=self.today)
            self.assertEqual(model.call_count, 1)
            self.assertEqual(send.call_count, 1)
            self.add_chat(name="b.md", content="用户：截止改成下周一。")
            second = w.run_workflow(self.root, self.cfg, "daily_chat", send=True, day=self.today)
            self.assertNotEqual(first["results"][0]["output"], second["results"][0]["output"])
            self.assertEqual(send.call_count, 2)

    def test_yesterday_late_chat_is_included(self):
        yesterday = (datetime.now(ZoneInfo(self.cfg["timezone"])).date() - timedelta(days=1)).isoformat()
        self.add_chat(day=yesterday)
        with patch.object(w.core, "generate", return_value=self.answer) as model:
            result = w.run_workflow(self.root, self.cfg, "daily_chat")
            self.assertEqual(sum(r["status"] == "ready" for r in result["results"]), 1)
            model.assert_called_once()

    def test_long_transcript_all_chunks_reach_model(self):
        source = self.root / "inbox/meetings/long.txt"
        source.write_text("甲" * 26000 + "最后一句：取消之前的计划。", encoding="utf-8")
        seen = []
        def capture(*args, **kwargs):
            seen.append(kwargs["source_context"])
            return self.answer
        with patch.object(w.core, "generate", side_effect=capture):
            w.run_workflow(self.root, self.cfg, "meeting_inbox")
        self.assertEqual(len(seen), 4)  # Three source chunks and one merge.
        self.assertIn("取消之前的计划", seen[2])

    def test_missing_transcriber_is_pending_without_upload(self):
        (self.root / "inbox/recordings/meeting.wav").write_bytes(b"test-audio")
        with patch.object(w.core, "run") as command, patch.object(w.core, "generate") as model:
            result = w.run_workflow(self.root, self.cfg, "meeting_inbox")
            self.assertEqual(result["status"], "needs_setup")
            self.assertEqual(len(result["pending_audio"]), 1)
            command.assert_not_called()
            model.assert_not_called()

    def test_audio_adapter_caches_transcript_and_does_not_repeat_work(self):
        (self.root / "inbox/recordings/meeting.wav").write_bytes(b"test-audio")
        self.cfg["transcribe_command"] = ["asr.exe", "{input}", "--out", "{output}"]
        def fake_asr(args, **kwargs):
            Path(args[-1]).write_text("发言者一：下周一讨论方案。", encoding="utf-8")
            return ""
        with patch.object(w.core, "run", side_effect=fake_asr) as command, patch.object(w.core, "generate", return_value=self.answer) as model:
            result = w.run_workflow(self.root, self.cfg, "meeting_inbox")
            self.assertEqual(result["status"], "completed")
            w.run_workflow(self.root, self.cfg, "meeting_inbox")
            command.assert_called_once()
            model.assert_called_once()
            self.assertEqual(len(list((self.root / "transcripts").glob("*.txt"))), 1)

    def test_preview_does_not_transcribe_or_send(self):
        (self.root / "inbox/recordings/meeting.wav").write_bytes(b"test-audio")
        (self.root / "inbox/meetings/meeting.txt").write_text("讨论周五复盘", encoding="utf-8")
        with patch.object(w.core, "run") as command, patch.object(w.core, "generate", return_value=self.answer), patch.object(w.core, "deliver") as send:
            w.run_workflow(self.root, self.cfg, "meeting_inbox", send=True, preview=True)
            command.assert_not_called()
            send.assert_not_called()
            self.assertFalse((self.root / "runtime/workflows").exists())

    def test_failed_meeting_does_not_block_other_inputs(self):
        for name in ("a", "b"):
            (self.root / f"inbox/meetings/{name}.txt").write_text(name, encoding="utf-8")
        with patch.object(w.core, "generate", side_effect=[RuntimeError("model unavailable"), self.answer]):
            result = w.run_workflow(self.root, self.cfg, "meeting_inbox")
            self.assertEqual(len(result["errors"]), 1)
            self.assertEqual(len(result["results"]), 1)

    def test_failed_send_reuses_completed_summary(self):
        self.add_chat()
        with patch.object(w.core, "generate", return_value=self.answer) as model, patch.object(w.core, "deliver", side_effect=[RuntimeError("offline"), "om_ok"]):
            with self.assertRaises(RuntimeError):
                w.run_workflow(self.root, self.cfg, "daily_chat", send=True, day=self.today)
            result = w.run_workflow(self.root, self.cfg, "daily_chat", send=True, day=self.today)
            self.assertTrue(result["results"][0]["delivered"])
            model.assert_called_once()


if __name__ == "__main__":
    unittest.main()
