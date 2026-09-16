# 两条开箱流程

## 每日 AI 聊天沉淀

本人已送达的飞书助理对话自动保存到 chats/YYYY-MM-DD/；其他 AI 聊天由用户主动交来 UTF-8 txt/Markdown 导出，或由已选择范围内的宿主任务读取工具导出。本包不会自动抓取全部 ChatGPT、Codex、微信或其他账号历史。

```powershell
python scripts/workflows.py import-chat --workspace "C:/AI/MyAssistant" --source "C:/Exports/chat.txt" --date 2026-09-16
python scripts/workflows.py daily-chat --workspace "C:/AI/MyAssistant" --date 2026-09-16 --preview
```

正式启用后调用 daily-chat（不传 date）处理当天和前一天，补上昨日晚间资料。无材料不调用模型。原文变化生成新版本；原文没变复用结果；发送失败可重试，不重新总结。

输出在 outputs/daily-chat/，包含实际做过的事、明确决定、纠正与偏好候选、知识、待办及原文片段来源。偏好候选不会自动改写用户长期记忆。AI 提议不自动登记成用户任务。

## 会议录音整理

逐字稿放入 inbox/meetings/（txt/md）；音频放入 inbox/recordings/。用户在本地交来材料时由 Agent 自动归位，无须用户记目录。

```powershell
python scripts/workflows.py meeting-inbox --workspace "C:/AI/MyAssistant" --preview
```

预览处理文字但不启动音频转写，也不发消息。正式启用后：录音 → 转写器 → transcripts/ 保留原始逐字稿 → 分段提取 → 合并纪要 → 保存结果 → 已接通渠道通知。

输出在 outputs/meetings/：主题、决定、事项/负责人/截止/原话来源、待核对问题、知识。未明确的人名和期限保持未明确。每份输入独立处理，录音失败不阻止其他会议文字整理。

### 音频转写如何接入

初次收到音频时，Agent 检查本机已有转写能力并复用，可以是已安装的 transcribe Skill、本地转写程序或能够输出逐字稿的飞书工具，不要求用户重新设计流程。

独立脚本提供 `transcribe_command` 参数数组接口，含 `{input}` 和 `{output}`。例如用户已经配置好的转写脚本：

```json
{"transcribe_command":["C:/Python/python.exe","C:/Tools/transcribe.py","{input}","--out","{output}"]}
```

这是接口示意，不是附送的转写器。先验证真实命令支持这些参数，输出须为非空 UTF-8 文本，不接受 shell 命令串。配置只在用户工作区保存。接云转写器时说明音频上传与费用，不向未获授权的服务上传。

没有转写器只入队，返回 needs_setup 与待转写文件，不上传音频，不编纪要。安装授权是一次必要的接入动作，不是业务问卷。本版没有把商业 ASR 账户或模型权重打进开源包。

## 增量、长记录与通知

文字按 10000 字符切片，全部处理后合并，保留来源；不使用普通问答的 40000 字符截断来生成完整总结。按原文内容哈希缓存同一版本，重跑可补发失败通知。同日新增内容生成新版本，因此会议检查支持每日多个时段。

仅新增有效结果通知；无输入不产生空报告。不会给客户发消息、修改正式业务文件或把候选待办直接写成承诺。聊天与会议记录可供本地 Agent 后续查阅；远程入口并非无限历史检索。
