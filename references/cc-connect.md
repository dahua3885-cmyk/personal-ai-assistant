# 默认接入：cc-connect

用户已确认使用 chenhg5/cc-connect。本仓库通过 vendor/cc-connect Git 子模块引用原项目，固定 v1.4.1（5d4c96dd12774574369e75b60084140101c9a59a），与作者本机已安装版本一致，不表示它是最新版本。原作者为 chenhg5；npm/package.json 声明 MIT，但该标签根目录未包含 LICENSE 文件，不能宣称本仓库 MIT 许可覆盖其全部源码。保持独立上游引用，不将其源码混入本项目原创代码。

## 初始化

先介绍每日聊天沉淀、会议整理和心跳，只问用户选择飞书还是微信。使用独立个人助理工作区，不询问职业、资料清单或作息。

1. 递归克隆本仓库，已有克隆运行 `git submodule update --init --recursive` 获取固定源码。GitHub 自动生成的源码 ZIP 不包含子模块内容。
2. 已有 cc-connect 时核对 `cc-connect --version`，不要覆盖私人配置或升级正在运行的服务。新机器可以按上游 INSTALL.md 安装；固定 npm 版本命令为 `npm install -g cc-connect@1.4.1`。
3. 执行 `python scripts/assistant.py init --workspace C:/AI/MyAssistant`，创建默认资料区。让工作区 Agent 读取本包 SKILL.md，沿用两条内置流程。
4. 在该工作区另建 cc-connect.toml，复制下方配置并把路径替换为用户工作区。凭据通过上游 setup 在本地写入，不提交 Git。

```toml
data_dir = "C:/AI/MyAssistant/runtime/cc-connect"
language = "zh"

[display]
mode = "quiet"

[[projects]]
name = "personal-assistant"

[projects.agent]
type = "codex"

[projects.agent.options]
work_dir = "C:/AI/MyAssistant"
mode = "suggest"

[[projects.platforms]]
type = "weixin"

[projects.platforms.options]
allow_from = "SET_ME_TO_OWNER_ID"
```

微信：执行 `cc-connect weixin setup --config C:/AI/MyAssistant/cc-connect.toml --project personal-assistant`，本人扫码后将 allow_from 设为该本人账号 ID，再启动。飞书：把平台 type 改为 feishu，执行 `cc-connect feishu setup --config C:/AI/MyAssistant/cc-connect.toml --project personal-assistant`，按官方引导绑定或创建应用；完成应用发布，allow_from 仅填写本人 open_id。详见 vendor/cc-connect/INSTALL.md 与 config.example.toml。

最后运行 `cc-connect --config C:/AI/MyAssistant/cc-connect.toml`。前台运行，Ctrl+C 停止。不要使用 --force 干扰既有服务，不与旧 listen 或 Claude-to-IM 同时接收同一个机器人。

## 内置流程和验收

cc-connect 负责接收消息、调用 Codex、回复和管理会话。本包负责聊天沉淀、会议整理的默认职责与执行流程。心跳使用一种调度入口，不能同时注册宿主与 cc-connect 重复任务。

先测试本人发一句话并收到回复，再试跑一份聊天文本或会议逐字稿，最后启用默认排期。新学员配置、音频 ASR、按日聊天导入、主动推送需逐项实测；导入上游源码不等于整个产品已经端到端验收。

之前 Claude-to-IM 的依赖审计及消息时间戳结论不适用于 cc-connect。原候选保留作可选参考，当前初始化不默认安装它。scripts/bridge.py 专用于该旧候选，不是 cc-connect 启动器。
