# 飞书与微信

本版参考 Windows 下 Codex CLI 0.145.0 与 lark-cli 1.0.86 的本机帮助和事件 schema。其他版本先运行 help 和 doctor 核对参数；未完成独立新电脑端到端认证测试。

## 飞书文字私聊

先安装并登录 Codex CLI，安装配置官方 lark-cli。用 CLI 自己的授权流程保存认证，不把 app secret/token 放入本包、Git 或聊天。若环境提供 lark-shared Skill，按其流程完成认证；否则先看 `lark-cli config --help` 和 `lark-cli auth --help`。

在飞书应用中开启机器人、消息接收事件与相应权限。运行 `lark-cli event schema im.message.receive_v1` 核对当前要求（本机 schema 要求 `im:message.p2p_msg:readonly` 与 `im.message.receive_v1`）；回复和发送消息的权限以当前 CLI 帮助及飞书后台提示为准。

用户向自己的机器人发送测试文字，确认该事件中的 `chat_id` 和 `sender_id`，填写工作区 config.json 中的 chat_id 和 sender_id；这两个值构成接收白名单。设置 `channel` 为 `feishu`。如用独立 lark-cli profile 填写 `lark_profile`。

运行 `python scripts/assistant.py doctor --workspace <目录>`，再在前台运行 `listen`。只回复白名单内的文字私聊。Ctrl+C 停止。此版本不安装开机项、不常驻隐藏服务；关闭进程后聊天入口停止。

Codex 使用用户自己的 CLI 登录；`ignore_user_config` 默认 true，防止加载额外 MCP 等配置。如果自定义服务商依赖 config.toml，需要用户核对配置后设为 false；这时继承的工具权限必须自行评估。可填写 model；留空使用 CLI 默认值，不硬编码开发者账号的模型名。

## 微信：已有官方路径，本包尚未集成

截至 2026-09-16 核对腾讯官方 openclaw-weixin 仓库，微信存在 OpenClaw channel 插件，文档包括扫码登录、文字与媒体收发、与配置的 OpenClaw agent 路由。不能把“本包没有实现”说成“微信不能接”。官方入口：https://github.com/Tencent/openclaw-weixin 。

该插件依赖 OpenClaw 运行环境，不等同于本包 Python + Codex CLI 适配器。初始化选择微信时先核对用户现有 OpenClaw 与插件环境，若要沿用这条路，另行配置与实测渠道、消息范围和本地工作流调用；未接通前保持状态明确。不要只把 config.json 改成 wechat 就宣布成功。插件能收媒体不代表本包已经能下载并转写微信语音。

个人微信、企业微信不是同一种接口。用户明确选企业微信时再核对其官方应用/智能机器人路径，不混用。

## Facebook

平台名不确定时先核对，不能把 Facebook 静默替换成飞书。本包没有 Facebook Messenger 适配器。用户确实需要它时，另行核对官方 Messenger Platform 的账号、应用、事件回调与权限要求再接入。
# 当前入口

优先使用已导入的 Claude-to-IM 桥接，见 [桥接说明](bridge.md)。以下旧版说明保留作兼容参考，不再表示微信源码未导入。
