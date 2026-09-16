# 飞书与微信

本版参考 Windows 下 Codex CLI 0.145.0 与 lark-cli 1.0.86 的本机帮助和事件 schema。其他版本先运行 help 和 doctor 核对参数；未完成独立新电脑端到端认证测试。

## 飞书文字私聊

先安装并登录 Codex CLI，安装配置官方 lark-cli。用 CLI 自己的授权流程保存认证，不把 app secret/token 放入本包、Git 或聊天。若环境提供 lark-shared Skill，按其流程完成认证；否则先看 `lark-cli config --help` 和 `lark-cli auth --help`。

在飞书应用中开启机器人、消息接收事件与相应权限。运行 `lark-cli event schema im.message.receive_v1` 核对当前要求（本机 schema 要求 `im:message.p2p_msg:readonly` 与 `im.message.receive_v1`）；回复和发送消息的权限以当前 CLI 帮助及飞书后台提示为准。

用户向自己的机器人发送测试文字，确认该事件中的 `chat_id` 和 `sender_id`，填写工作区 config.json 中的 chat_id 和 sender_id；这两个值构成接收白名单。设置 `channel` 为 `feishu`。如用独立 lark-cli profile 填写 `lark_profile`。

运行 `python scripts/assistant.py doctor --workspace <目录>`，再在前台运行 `listen`。只回复白名单内的文字私聊。Ctrl+C 停止。此版本不安装开机项、不常驻隐藏服务；关闭进程后聊天入口停止。

Codex 使用用户自己的 CLI 登录；`ignore_user_config` 默认 true，防止加载额外 MCP 等配置。如果自定义服务商依赖 config.toml，需要用户核对配置后设为 false；这时继承的工具权限必须自行评估。可填写 model；留空使用 CLI 默认值，不硬编码开发者账号的模型名。

## 微信

初始化可以记录个人微信/企业微信偏好。本版没有微信 BOT 适配器，不读取个人微信聊天。可选过渡办法是把选定文字复制到已接通的飞书私聊。企业微信扩展需另行实现和验证，不把微信群 webhook 当成已实现双向个人助理。
