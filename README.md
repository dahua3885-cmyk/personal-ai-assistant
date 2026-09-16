# 个人 AI 助理

> 默认接入已改为用户确认的 **cc-connect**，固定 v1.4.1 源码作为 Git 子模块导入。飞书、微信接入与极简初始化见 [cc-connect 接入说明](references/cc-connect.md)。Claude-to-IM 保留为可选候选，其审计结论不适用于 cc-connect。新学员的真实账号与内置流程仍需联调。

**把你和 AI 的聊天、会议录音交给它，留下每天的决定、知识和下一步。**

`0.2.0-alpha` · MIT 开源测试版。先带好两套流程，用户不必填写职业、工作资料和作息问卷。

## 已经带好的流程

### 1. 每日 AI 聊天沉淀

本人和机器人聊过的文字自动留档；其他 AI 聊天可以交来文本导出。每天把这些记录整理成：做过的事、明确决定、纠正与偏好候选、可复用知识、待办。AI 的提议不会被当成你的决定。

默认晚上 21:30 整理，补查昨天晚间新增。没有新记录就安静，不重复生成空报告。原文和来源保留，便于本地 Agent 后续查阅。不会自行抓取你所有平台、所有任务的聊天历史。

### 2. 会议录音与纪要整理

录音交来 → 转成逐字稿 → 整理主题、决定、待办和知识 → 保存原文与结果 → 通知本人。

逐字稿可直接整理；音频需要接通实际转写工具，程序已提供适配接口。没有转写器就明确显示“待转写”，不上传、不编纪要。检查时按原文内容去重，同日新增也能处理。长记录分段读完再合并。

默认交来立即处理，每天 10:30、16:30、21:30 检查新材料。用户只需要说“时间改一下”或“暂停”。详细行为见 [内置流程](references/workflows.md)。

## 初始化只走三步

1. 介绍上述两条流程，以及“心跳就是按约定时间主动检查”。
2. 选择聊天入口，按实际接法授权或扫码。
3. 接受或调整带好的默认方案，试跑一份材料并启用实际排期。

不要求先定义岗位、填写业务资料或逐项挑选自动化。原来的早报、待办检查、收件箱整理、晚报、周回顾、重复文字任务六套模板仍保留，需要时再开启。

下载后对 Codex 说：

> 读取这个目录的 SKILL.md，帮我搭个人助理。先介绍带好的聊天沉淀和会议整理流程，再带我连接聊天入口，按默认方案开始。

可将仓库内容放到 `~/.codex/skills/personal-ai-assistant/`（若设置 CODEX_HOME 则用其 skills 子目录），或直接让 AI 读取本目录 SKILL.md。

## 渠道支持实话表

| 渠道 | 当前状态 |
| --- | --- |
| 飞书本人文字私聊 | 默认复用已导入的 cc-connect；旧自带适配代码保留兼容 |
| 微信 | 默认复用已导入的 cc-connect；在用户自己的账号上扫码并实测 |
| Facebook Messenger | 本包未实现；不要把 Facebook 和飞书混为一谈 |

当前配置以 [cc-connect 接入说明](references/cc-connect.md) 为准。接收媒体不等于已完成录音转写；下方 lark-cli 命令为旧兼容路径。

## 本地运行

Python 3.10+、已认证的 Codex CLI、飞书路径使用官方 lark-cli。参考本机版本为 Codex CLI 0.145.0 / lark-cli 1.0.86，其他版本先核对 help。模型、渠道和转写服务使用自己的账户，电脑需开机联网。

```powershell
python -m pip install -r requirements.txt
python scripts/assistant.py init --workspace "C:/AI/MyAssistant"
python scripts/assistant.py doctor --workspace "C:/AI/MyAssistant"
```

init 创建默认职责、收件箱、聊天归档和自动化配置，保留已有用户文件。更新版本后再运行 init，只补不存在的新模板，不覆盖已设置任务。没有创建真实排期前 enabled 保持 false。

飞书接好后：

```powershell
python scripts/assistant.py listen --workspace "C:/AI/MyAssistant"
```

按 Ctrl+C 停止，不安装后台服务。聊天入口只处理文字；文件和录音由本地 Agent 接收归位。不是微信/飞书手机附件的完整下载器。

```powershell
# 导入用户明确交来的 AI 聊天，日期为聊天实际日期
python scripts/workflows.py import-chat --workspace "C:/AI/MyAssistant" --source "C:/Exports/chat.txt" --date 2026-09-16
# 预览：不发消息；会议预览也不启动转写
python scripts/assistant.py run-job --workspace "C:/AI/MyAssistant" --job daily_chat --preview
python scripts/assistant.py run-job --workspace "C:/AI/MyAssistant" --job meeting_inbox --preview
```

默认流程由 [宿主自动化工具](references/automations.md) 实际调度，成功后再标为 enabled。脚本不是独立常驻调度器。--deliver 目前仅向配置的本人飞书私聊发送，无变更不重复发送。

## 版本与验证

v0.2.0 将问卷式初始化改成默认成型流程，新增本人对话归档、聊天导入与每日沉淀、会议增量处理及可选转写接口。逻辑测试模拟模型和消息接口，不消耗真实额度、不发送消息。

```powershell
python -m unittest discover -s tests -v
```

尚未完成新电脑模型/飞书/定时端到端验收、真实 ASR 质量测试和微信网关集成。结果内容准确性仍需核对。不是一键完成的正式版。

## 数据与许可

用户资料在独立工作区，不放在源码。向你配置的模型或转写服务提供资料前确认该服务可用且获授权。不要将凭据和真实聊天提交到 Git。默认模型只读运行，不代表完整的文件读取隔离，详见 [验收与边界](references/acceptance.md)。

MIT License；第三方工具遵循各自许可与服务条款。仓库不包含作者私人记录、客户资料、第三方课程或任何服务账号。
