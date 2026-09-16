# 默认主动流程与可选扩展

初始化直接推荐 daily_chat、meeting_inbox 两条成型流程；另外六套通用模板作为后续扩展。不逐项询问用户。

默认当地时间：daily_chat 每天 21:30；meeting_inbox 每天 10:30、16:30、21:30。用户接受默认方案后创建实际排期。profile.md 不必填写，init 不启动服务。

## 在宿主中实际调度

使用可用的 automation_update 或当前宿主等效工具，优先当前任务 heartbeat；提示词用自然语言，按工具 schema 操作，不给用户看原始 RRULE。没有调度工具明确“待启用”。

先创建任务并保存返回 ID、时区和排期，成功后把相应 enabled 设为 true。暂停/更新操作已有 ID。新默认模板通过 init 增量加入，不覆盖旧模板状态和资料。

聊天任务提示词应说明：对指定工作区执行 daily_chat；如用户已选择宿主任务历史作为来源，先用实际可用的读取工具导出该范围内用户和 AI 的可见消息，按原始日期去重写入 chats/，不复制工具日志/隐藏推理/密钥，不扩到未选择任务。再执行：

```powershell
python scripts/assistant.py run-job --workspace "C:/AI/MyAssistant" --job daily_chat --deliver
```

会议任务：检查指定收件箱，运行下列命令；若返回 needs_setup，只有在用户已授权且确有转写能力时接通处理，不假装成功。转写失败或授权问题明确反馈。

```powershell
python scripts/assistant.py run-job --workspace "C:/AI/MyAssistant" --job meeting_inbox --deliver
```

目前 --deliver 的程序出口仅支持本人飞书私聊；其他渠道需由宿主已经验证的发送能力处理。脚本发送后，宿主不要重复发送同一结果。

无新输入不调用模型、不通知；通知失败保留结果待重试。电脑关机/离线时不能保证执行；聊天默认补查昨天，超过一天的补跑显式指定 date，避免突然发送大量过期消息。严格到点提醒单独配置。

## 其他六套模板

morning、followup、inbox、evening、weekly、repeat 沿用 v0.1.0 的每日缓存逻辑，同日只生成一版。不要与支持按输入变化增量执行的两条新流程混淆。用户需要时再开，不在初始化展开菜单。
