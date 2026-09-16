import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("assistant", Path(__file__).parents[1] / "scripts/assistant.py")
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name).resolve() / "workspace"
        a.init(self.workspace)
        self.cfg = a.config(self.workspace)
        self.cfg.update(channel="feishu", chat_id="oc_example", sender_id="ou_example")
        self.event = dict(chat_id="oc_example", sender_id="ou_example", sender_type="user",
                          chat_type="p2p", message_id="om_example", message_type="text", content="记下明天读书")
        self.answer = {"reply": "已记录", "note": "明天读书", "should_notify": True}

    def enable(self, job_id):
        jobs = a.read_json(self.workspace / "automations.json")
        for j in jobs:
            if j["id"] == job_id:
                j["enabled"] = True
        a.write_json(self.workspace / "automations.json", jobs)

    def test_init_preserves_user_files_and_disables_jobs(self):
        (self.workspace / "profile.md").write_text("私人设置", encoding="utf-8")
        a.init(self.workspace)
        self.assertEqual((self.workspace / "profile.md").read_text(encoding="utf-8"), "私人设置")
        self.assertFalse(any(j["enabled"] for j in a.read_json(self.workspace / "automations.json")))

    def test_untrusted_senders_and_groups_never_reach_model(self):
        with patch.object(a, "generate") as model, patch.object(a, "deliver") as send:
            for change in ({"sender_id": "ou_other"}, {"chat_id": "oc_other"}, {"sender_type": "bot"}, {"chat_type": "group"}):
                self.assertEqual(a.process_event(self.workspace, self.cfg, self.event | change)["status"], "ignored")
            model.assert_not_called()
            send.assert_not_called()

    def test_duplicate_message_is_not_reexecuted(self):
        with patch.object(a, "generate", return_value=self.answer) as model, patch.object(a, "deliver", return_value="om_receipt") as send:
            self.assertEqual(a.process_event(self.workspace, self.cfg, self.event)["status"], "replied")
            self.assertEqual(a.process_event(self.workspace, self.cfg, self.event)["status"], "duplicate")
            self.assertEqual(model.call_count, 1)
            self.assertEqual(send.call_count, 1)
        self.assertEqual(len(list((self.workspace / "notes").glob("*.md"))), 1)
        archives = list((self.workspace / "chats").rglob("*.md"))
        self.assertEqual(len(archives), 1)
        text = archives[0].read_text(encoding="utf-8")
        self.assertIn(self.event["content"], text)
        self.assertIn(self.answer["reply"], text)

    def test_failed_delivery_reuses_saved_result(self):
        with patch.object(a, "generate", return_value=self.answer) as model, patch.object(a, "deliver", side_effect=[RuntimeError("offline"), "om_ok"]) as send:
            with self.assertRaises(RuntimeError):
                a.process_event(self.workspace, self.cfg, self.event)
            self.assertEqual(a.process_event(self.workspace, self.cfg, self.event)["status"], "replied")
            self.assertEqual(model.call_count, 1)
            self.assertEqual(send.call_count, 2)

    def test_attachment_is_not_pretended_read(self):
        with patch.object(a, "generate") as model, patch.object(a, "deliver", return_value="om_ok") as send:
            a.process_event(self.workspace, self.cfg, self.event | {"message_type": "image"})
            model.assert_not_called()
            self.assertIn("只处理文字", send.call_args.args[1])

    def test_disabled_and_unknown_jobs_are_rejected(self):
        with patch.object(a, "generate") as model:
            for name in ("morning", "../invalid"):
                with self.assertRaises(ValueError):
                    a.job(self.workspace, self.cfg, name)
            model.assert_not_called()

    def test_preview_never_delivers_or_creates_formal_state(self):
        with patch.object(a, "generate", return_value=self.answer.copy()), patch.object(a, "deliver") as send:
            result = a.job(self.workspace, self.cfg, "morning", send=True, preview=True)
            self.assertTrue(Path(result["output"]).exists())
            self.assertFalse(result["delivered"])
            self.assertFalse((self.workspace / "runtime/jobs").exists())
            send.assert_not_called()

    def test_job_retry_is_idempotent(self):
        self.enable("morning")
        with patch.object(a, "generate", return_value=self.answer.copy()) as model, patch.object(a, "deliver", side_effect=[RuntimeError("offline"), "om_ok"]) as send:
            with self.assertRaises(RuntimeError):
                a.job(self.workspace, self.cfg, "morning", send=True)
            self.assertTrue(a.job(self.workspace, self.cfg, "morning", send=True)["delivered"])
            a.job(self.workspace, self.cfg, "morning", send=True)
            self.assertEqual(model.call_count, 1)
            self.assertEqual(send.call_count, 2)

    def test_unchanged_check_stays_quiet(self):
        self.enable("followup")
        answer = dict(reply="无新增", note="", should_notify=False)
        with patch.object(a, "generate", return_value=answer), patch.object(a, "deliver") as send:
            self.assertFalse(a.job(self.workspace, self.cfg, "followup", send=True)["delivered"])
            send.assert_not_called()

    def test_concurrent_processing_refused(self):
        with a.workspace_lock(self.workspace):
            with self.assertRaises(RuntimeError):
                with a.workspace_lock(self.workspace):
                    pass

    def test_context_excludes_config_and_reports_truncation(self):
        (self.workspace / "inbox/long.md").write_text("甲" * 14000, encoding="utf-8")
        (self.workspace / "secret.md").write_text("NEVER_INCLUDE", encoding="utf-8")
        ctx = a.context(self.workspace)
        self.assertNotIn("NEVER_INCLUDE", ctx)
        self.assertNotIn("sender_id", ctx)
        self.assertIn("已截断", ctx)

    def test_model_contract_passes_stdin_and_validates_result(self):
        def fake_run(args, **kwargs):
            self.assertIn("--ignore-user-config", args)
            self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
            self.assertIn("<本次任务>", kwargs["input"])
            out = Path(args[args.index("--output-last-message") + 1])
            a.write_json(out, self.answer)
            return ""
        with patch.object(a, "command", return_value="codex.exe"), patch.object(a, "run", side_effect=fake_run):
            self.assertEqual(a.generate(self.workspace, self.cfg, "记事"), self.answer)

    def test_delivery_requires_real_receipt(self):
        with patch.object(a, "command", return_value="lark-cli.exe"), patch.object(a, "run", return_value='{"ok":false}'):
            with self.assertRaises(RuntimeError):
                a.deliver(self.cfg, "内容", "pa-test")


if __name__ == "__main__":
    unittest.main()
