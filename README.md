# 个人 AI 助理 · Personal AI Assistant

通过一轮访谈，搭一个了解你工作背景、能在飞书里记事和整理文字、按约定执行主动工作的个人助理。

**0.1.0-alpha · 测试版**。包含 Codex Skill、通用 Python 脚本、空白工作区和六套自动化模板。离线测试覆盖核心逻辑；尚未完成独立新电脑的模型认证、飞书往返和定时调度实测。不是一键安装完成品。

## 你会得到什么

- 初始化引导：先说明能力与心跳，再询问工作、资料、渠道和作息。
- 飞书文字私聊：白名单消息 → 模型处理 → 回到原消息；支持保存个人备忘。
- 六套主动工作模板：今日重点、待办检查、收件箱整理、晚间复盘、每周回顾、重复文字任务。
- 独立工作区：自己的背景、规则、收件箱、备忘和输出。
- 自动化修改与暂停流程：由当前 Codex 宿主的自动化工具实际调度；只创建配置不算启用。

**微信仍是待实现的接入选项。** 本版不连接个人微信或企业微信，不自动读微信聊天。语音、图片、任意电脑控制、多用户和开机自启不在本版范围。

## 给 AI 的使用口令

下载仓库后，在 Codex 中说：

> 读取这个目录的 SKILL.md，帮我搭个人 AI 助理。先解释它能干什么、什么叫心跳，再采访我，按我的需求配置职责、聊天入口和自动化。没有接通或没有测试成功的功能不要说完成。

希望注册成 Skill 时，把本仓库内容放入 `~/.codex/skills/personal-ai-assistant/`；若设置了 CODEX_HOME，则使用该目录下的 skills。重新打开任务后使用 `$personal-ai-assistant`。也可以只让 AI 直接读取 SKILL.md。

## 运行环境

- Python 3.10+；Windows 通常还需要 `tzdata`，安装命令见下。
- 已安装、可调用并已认证的 Codex CLI 和官方 lark-cli。
- 有权限配置自己飞书应用的账号。模型账户与服务由使用者自备。
- 本机参考版本：Codex CLI 0.145.0 / lark-cli 1.0.86。其他版本先看 doctor 和对应 CLI help。

源码不包含任何账号、密钥、付费课程、作者个人资料或云端服务。电脑需开机联网；模型运行按所用服务消耗额度。

## 最小启动

在仓库目录执行，下面的用户工作区路径是示例，选择你自己的独立目录：

```powershell
python -m pip install -r requirements.txt
python scripts/assistant.py init --workspace "C:/AI/MyAssistant"
python scripts/assistant.py doctor --workspace "C:/AI/MyAssistant"
```

init 可重复运行，不覆盖已有文件。让 AI 通过访谈填写工作区的 profile.md 和配置，再按 [飞书接入说明](references/channels.md) 完成授权、本人私聊 ID 与发送者 ID 配置。

```powershell
python scripts/assistant.py listen --workspace "C:/AI/MyAssistant"
```

向机器人发送“记一下：周五整理本周读书笔记”，核对飞书回复和工作区 notes/。关闭监听终端或按 Ctrl+C 即停止聊天入口。当前不会自动安装后台服务。

## 心跳与自动化

心跳是在你没有主动提问时，按约定醒来检查负责的事情；固定自动化则是按排期完成早报等工作。六套模板默认全部关闭。

让 AI 按 [初始化](references/onboarding.md) 推荐适合你的两三项，并按 [自动化说明](references/automations.md) 在支持的 Codex 宿主中创建实际任务。没有调度工具时只能手动运行，不能宣称已开启心跳。

```powershell
# 试跑：可以预览未启用的模板，只保存预览，不发送消息
python scripts/assistant.py run-job --workspace "C:/AI/MyAssistant" --job morning --preview
# 启用后的正式运行：--deliver 明确要求发送到已配置的本人飞书私聊
python scripts/assistant.py run-job --workspace "C:/AI/MyAssistant" --job morning --deliver
```

同一模板同一天复用已生成结果，失败重试不重复调用模型。首版仅适合每日/每周频率，不支持同日多次检查，也不保证精确时间提醒。修改自然语言需求由本地 Codex Skill 处理；飞书文字入口不会自行变更系统调度。

## 数据和边界

运行数据在你指定的工作区，不在源码仓库。不要把工作区提交到 Git。config.json 不存密钥，使用 CLI 自己的认证存储。

程序把指定目录的 Markdown 交给你选择的模型服务处理；远程调用使用只读模式，程序仅写备忘、输出与状态。只读模式不是完整的文件读取隔离。自定义 CLI 配置、MCP 与模型服务需要使用者自行检查。详细范围与验收见 [acceptance.md](references/acceptance.md)。

当前多轮上下文依赖已落盘备忘和资料，不保证自动记住每句话。收件箱只支持 Markdown 文字，不读取附件。模板“无变化静默”由模型判断，尚非严格的结构化业务事件检测。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试使用模拟模型与消息接口，不会消耗真实模型额度或发送飞书消息。真实渠道测试需在你自己的账户上完成。

## 开源

MIT License。源码与通用模板可使用、修改和分发；第三方工具使用各自许可与服务条款。欢迎通过 Issue 提交可复现问题，勿附带密钥、真实聊天或私人资料。
