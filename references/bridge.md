# 飞书 / 微信桥接：已导入源码

采用 op7418/Claude-to-IM-skill（归藏）及其必需的核心库 op7418/Claude-to-IM。两个 Git 子模块固定提交，完整保留 MIT 许可。不是只添加链接，也不自行重写渠道。

## 使用

需要 Git、Node.js 20+、Python 3.10+ 和已认证的 Codex。递归克隆本仓库；GitHub 自动 Source ZIP 不含子模块源码。

```powershell
git clone --recurse-submodules https://github.com/dahua3885-cmyk/personal-ai-assistant.git
cd personal-ai-assistant
python scripts/bridge.py install
python scripts/bridge.py init --workspace C:/AI/MyAssistant --channel feishu
```

微信选择 `--channel weixin`。初始化直接关联个人助理工作区与内置流程，保留已有配置。切换渠道请修改已有配置。

飞书：在工作区 runtime/im-bridge/config.env 本地填 App ID、Secret、本人 open_id 白名单；配置应用机器人、消息权限、长连接 im.message.receive_v1 并发布应用。完整配置按 vendor/Claude-to-IM-skill 内说明执行。不要提交凭据。

微信：运行 `python scripts/bridge.py weixin-login --workspace C:/AI/MyAssistant`，由上游打开扫码页面，用户本人确认。

启动：`python scripts/bridge.py start --workspace C:/AI/MyAssistant`，前台运行，Ctrl+C 停止。不会注册开机服务。同一机器人与原 assistant.py listen 二选一。

运行数据使用工作区独立 CTI_HOME，不覆盖 ~/.claude-to-im。默认 Codex、ask 模式、不全局自动批准。机器人通过工作区 AGENTS.md 读取内置聊天沉淀与会议整理规则。

## 验证与剩余工作

- 已导入源码、安装构建和类型检查通过，上游 136 项离线测试、原有 24 项测试通过。未进行真实账号登录、收发消息或模型调用。
- 上游 messages JSON 只有 role/content，没有逐条时间戳。历史导入需确认真实日期，不能把文件修改时间当成聊天日期；自动按日归档仍待适配。
- 微信语音依赖微信提供的转文字，没有文字就报错。会议录音继续需要真实 ASR；附件接收尚未自动接入会议收件箱。
- 心跳仍由宿主创建；上游负责聊天回复，本包 --deliver 仍是原飞书出口，尚未适配微信定时主动推送。不要重复启动发送器。
- 2026-09-16 检查上游锁文件，npm audit 核心 15 项（含 7 high、1 critical）、Skill 1 low。尚未升级依赖，正式交付前需修复并复测。本轮未启动联网机器人。

当前是源码集成，不宣称上述流程全部打通，不以正式可用新版发布。
