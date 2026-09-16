"""Built-in daily chat and meeting workflows. No silent chat scraping or implicit cloud uploads."""
import argparse
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo

import assistant as core

VERSION = "0.2.0-alpha"
TEXT = {".md", ".txt"}
AUDIO = {".mp3", ".m4a", ".wav", ".mp4", ".aac", ".ogg", ".flac"}
CHAT_TASK = "整理这些本人和 AI 的对话。按实际做过的事、用户明确决定、纠正与偏好候选、可复用知识、明确待办分组。不要把 AI 建议当成用户决定，不把聊天中提及的第三方观点当成用户观点。保留文件/片段来源。没有内容的组省略。只产出整理结果，note 为空。"
MEETING_TASK = "整理会议逐字稿：会议主题、已明确的决定、待办表（事项/负责人/截止时间/原话来源）、待核对问题、可复用知识。没有明确的负责人或日期就写未明确，不能按你的推断给人派任务。说话人不明确时不要强行归因。保留文件/片段来源。note 为空。"


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def file_digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()[:24]


def safe_files(workspace, folder, suffixes):
    base = workspace / folder
    if not base.exists():
        return []
    return [p for p in sorted(base.rglob("*")) if p.is_file() and p.suffix.lower() in suffixes
            and p.resolve().is_relative_to(workspace.resolve())
            and not any(parent.is_symlink() for parent in [p, *p.parents] if parent != workspace)]


def import_chat(workspace, source, day):
    date.fromisoformat(day)
    if source.suffix.lower() not in TEXT or not source.is_file():
        raise ValueError("请提供明确选择的 Markdown 或 UTF-8 文本聊天导出，不直接读取浏览器或全机聊天库")
    body = source.read_text(encoding="utf-8-sig")
    if not body.strip():
        raise ValueError("聊天导出为空")
    target = workspace / "chats" / day / ("import-" + digest(body) + ".md")
    with core.workspace_lock(workspace):
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text(f"# 用户交来的 AI 聊天记录\n\n日期：{day}\n来源文件：{source.name}\n\n{body}", encoding="utf-8")
    return {"status": "imported", "path": str(target)}


def summarize(workspace, cfg, documents, task):
    # Process every chunk; unlike general Q&A this workflow must not silently drop long inputs.
    pieces = []
    for name, body in documents:
        for index in range(0, len(body), 10000):
            label = f"{name}#片段{index // 10000 + 1}"
            pieces.append((label, body[index:index + 10000]))
    if not pieces:
        raise ValueError("没有可整理的文字")
    results = []
    for label, text in pieces:
        answer = core.generate(workspace, cfg, task + "\n这是原文的一部分，压缩到 1000 字以内，不丢明确决定和待办。",
                               source_context=f"来源：{label}\n{text}")
        results.append(f"来源：{label}\n{answer['reply']}")
    if len(results) == 1:
        return results[0]
    for _ in range(6):
        if len("\n\n".join(results)) <= 18000:
            return core.generate(workspace, cfg, task + "\n合并以下分段提取，排重并保留来源。不得补充原文之外的事实。",
                                 source_context="\n\n".join(results))["reply"]
        groups, current = [], ""
        for result in results:
            if len(result) > 18000:
                raise ValueError("分段结果过长，请更换能够遵守输出长度的模型后重试；没有截断原文")
            if len(current) + len(result) > 18000:
                groups.append(current)
                current = ""
            current += result + "\n\n"
        if current:
            groups.append(current)
        results = [core.generate(workspace, cfg, task + "\n将这些提取合并压缩到 1500 字以内，保留来源与明确决定、待办。", source_context=g)["reply"] for g in groups]
    raise ValueError("内容过多且模型未能压缩，停止，原文已保留")


def compile_record(workspace, cfg, sources, task, category, label, send, preview):
    documents = [(str(p.relative_to(workspace)), p.read_text(encoding="utf-8-sig")) for p in sources]
    documents = [(name, body) for name, body in documents if body.strip()]
    if not documents:
        return {"status": "empty", "category": category, "label": label}
    revision = digest(VERSION + task + json.dumps(documents, ensure_ascii=False))
    record = workspace / "runtime/workflows" / category / (revision + ".json")
    saved = core.read_json(record) if record.exists() and not preview else {}
    if not saved:
        body = summarize(workspace, cfg, documents, task)
        saved = {"body": body, "delivered": False, "sources": [n for n, _ in documents], "revision": revision}
        if not preview:
            core.write_json(record, saved)
    output = workspace / "outputs" / category / (label + "-" + revision + ("-preview" if preview else "") + ".md")
    output.parent.mkdir(parents=True, exist_ok=True)
    if not output.exists():
        output.write_text(f"# {label}\n\n输入：{len(documents)} 份；原文版本：{revision}\n\n{saved['body']}", encoding="utf-8")
    if send and not preview and not saved["delivered"]:
        key = "paw-" + digest(str(workspace) + category + revision)
        saved["receipt"] = core.deliver(cfg, saved["body"], key)
        saved["delivered"] = True
        core.write_json(record, saved)
    return {"status": "ready", "output": str(output), "delivered": saved["delivered"], "source_count": len(documents)}


def transcribe_audio(workspace, cfg, audio):
    key = file_digest(audio)
    target = workspace / "transcripts" / (key + ".txt")
    if target.exists() and target.read_text(encoding="utf-8-sig").strip():
        return target
    command = cfg.get("transcribe_command") or []
    if not command:
        return None
    if (not isinstance(command, list) or not all(isinstance(x, str) for x in command)
            or not any("{input}" in x for x in command) or not any("{output}" in x for x in command)
            or Path(command[0]).suffix.lower() in {".cmd", ".bat"}):
        raise ValueError("transcribe_command 应为原生程序参数列表，包含 {input} 和 {output}；不支持 shell 包装")
    with tempfile.TemporaryDirectory(prefix="assistant-transcribe-") as temporary:
        out = Path(temporary) / "transcript.txt"
        args = [x.replace("{input}", str(audio)).replace("{output}", str(out)) for x in command]
        core.run(args, timeout=int(cfg.get("transcribe_timeout_seconds", 1800)))
        if not out.exists() or not out.read_text(encoding="utf-8-sig").strip():
            raise ValueError("转写器没有生成非空 UTF-8 逐字稿")
        target.parent.mkdir(exist_ok=True)
        target.write_text(f"来源录音：{audio.relative_to(workspace)}\n\n" + out.read_text(encoding="utf-8-sig"), encoding="utf-8")
    return target


def run_workflow(workspace, cfg, job_id, send=False, preview=False, day=None):
    jobs = [j for j in core.read_json(workspace / "automations.json") if j["id"] == job_id]
    if len(jobs) != 1 or job_id not in {"daily_chat", "meeting_inbox"}:
        raise ValueError("未知内置流程")
    if not preview and jobs[0].get("enabled") is not True:
        raise ValueError("此流程尚未启用，可先 --preview 试跑")
    if send and not preview:
        core.require_feishu(cfg)
    results, pending, errors = [], [], []
    with core.workspace_lock(workspace):
        if job_id == "daily_chat":
            today = date.fromisoformat(day) if day else datetime.now(ZoneInfo(cfg["timezone"])).date()
            days = [today] if day else [today - timedelta(days=1), today]
            for target_day in days:
                stamp = target_day.isoformat()
                sources = safe_files(workspace, "chats/" + stamp, TEXT)
                results.append(compile_record(workspace, cfg, sources, CHAT_TASK, "daily-chat", stamp, send, preview))
        else:
            sources = safe_files(workspace, "inbox/meetings", TEXT)
            for audio in safe_files(workspace, "inbox/recordings", AUDIO):
                if preview:
                    pending.append({"file": str(audio.relative_to(workspace)), "reason": "预览不启动音频转写"})
                    continue
                try:
                    transcript = transcribe_audio(workspace, cfg, audio)
                    if transcript:
                        sources.append(transcript)
                    else:
                        pending.append({"file": str(audio.relative_to(workspace)), "reason": "等待接通转写器，原录音未上传或修改"})
                except Exception as exc:
                    errors.append({"file": str(audio.relative_to(workspace)), "error": type(exc).__name__, "reason": "转写失败，未标完成"})
            for source in sorted(set(sources)):
                name = "meeting-" + digest(str(source.relative_to(workspace)))
                try:
                    results.append(compile_record(workspace, cfg, [source], MEETING_TASK, "meetings", name, send, preview))
                except Exception as exc:
                    errors.append({"file": str(source.relative_to(workspace)), "error": type(exc).__name__, "reason": "整理或发送失败，保留已生成结果以便重试"})
    report = {"status": "needs_setup" if pending else ("partial_failure" if errors else "completed"),
              "results": results, "pending_audio": pending, "errors": errors, "preview": preview}
    if not preview:
        core.write_json(workspace / "runtime" / (job_id + "-status.json"), report)
    return report


def main():
    parser = argparse.ArgumentParser(description="默认流程：聊天沉淀与会议整理")
    parser.add_argument("action", choices=["import-chat", "daily-chat", "meeting-inbox"])
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--deliver", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    cfg = core.config(workspace)
    if args.action == "import-chat":
        if not args.source or not args.date:
            parser.error("import-chat 需要 --source 和 --date（聊天实际日期）")
        result = import_chat(workspace, args.source.resolve(), args.date)
    else:
        result = run_workflow(workspace, cfg, args.action.replace("-", "_"), args.deliver, args.preview, args.date)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") in {"needs_setup", "partial_failure"}:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
