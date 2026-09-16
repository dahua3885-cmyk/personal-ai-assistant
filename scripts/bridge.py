"""Use the pinned upstream IM bridge without sharing a user's global CTI state."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'vendor/Claude-to-IM'
SKILL = ROOT / 'vendor/Claude-to-IM-skill'


def run(argv, cwd, env=None):
    subprocess.run(argv, cwd=cwd, env=env, check=True)


def init(workspace, channel):
    run([sys.executable, str(ROOT / 'scripts/assistant.py'), 'init', '--workspace', str(workspace)], ROOT)
    home = workspace / 'runtime/im-bridge'
    home.mkdir(parents=True, exist_ok=True)
    config = home / 'config.env'
    if not config.exists():
        with config.open('x', encoding='utf-8') as out:
            out.write(f'CTI_RUNTIME=codex\nCTI_ENABLED_CHANNELS={channel}\n'
                      f'CTI_DEFAULT_WORKDIR={workspace.as_posix()}\nCTI_DEFAULT_MODE=ask\n'
                      'CTI_AUTO_APPROVE=false\nCTI_WEIXIN_MEDIA_ENABLED=true\n'
                      'CTI_FEISHU_APP_ID=\nCTI_FEISHU_APP_SECRET=\nCTI_FEISHU_ALLOWED_USERS=\n')
        config.chmod(0o600)
    guide = workspace / 'ASSISTANT_WORKFLOWS.md'
    guide.write_text(f'# 已安装的个人助理流程\n\n先读取 {ROOT.as_posix()}/SKILL.md。\n'
                     '内置每日 AI 聊天沉淀与会议整理；原文保留，建议不能当成决定。\n'
                     '桥接消息原文在 runtime/im-bridge/data/messages；上游没有逐条日期，'
                     '导入历史时必须确认日期，不把文件修改时间当成聊天日期。\n'
                     '音频需要真实转写器；定时任务需要宿主实际创建。\n', encoding='utf-8')
    agents = workspace / 'AGENTS.md'
    text = agents.read_text(encoding='utf-8')
    if 'ASSISTANT_WORKFLOWS.md' not in text:
        with agents.open('a', encoding='utf-8') as out:
            out.write('\n个人助理内置流程见 ASSISTANT_WORKFLOWS.md，处理资料前先读取。\n')
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'init', 'start', 'weixin-login'])
    parser.add_argument('--workspace', type=Path, default=Path.home() / 'PersonalAssistant')
    parser.add_argument('--channel', choices=['feishu', 'weixin'], default='feishu')
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    if args.action == 'install':
        if not (CORE / 'package.json').exists() or not (SKILL / 'package.json').exists():
            run(['git', 'submodule', 'update', '--init', '--recursive'], ROOT)
        npm = shutil.which('npm.cmd') or shutil.which('npm')
        if not npm:
            parser.error('需要 Node.js 20+ 和 npm')
        for folder in (CORE, SKILL):
            run([npm, 'ci', '--ignore-scripts'], folder)
            run([npm, 'run', 'build'], folder)
        return
    if args.action == 'init':
        print(init(workspace, args.channel))
        return
    config = workspace / 'runtime/im-bridge/config.env'
    if not config.exists():
        parser.error('请先运行 init')
    env = dict(os.environ, CTI_HOME=str(config.parent), CTI_CODEX_SKIP_GIT_REPO_CHECK='true')
    if args.action == 'weixin-login':
        run(['node', '--import', 'tsx', 'src/weixin-login.ts'], SKILL, env)
    else:
        values = dict(line.split('=', 1) for line in config.read_text(encoding='utf-8').splitlines()
                      if '=' in line and not line.startswith('#'))
        if 'feishu' in values.get('CTI_ENABLED_CHANNELS', '').split(','):
            for key in ('CTI_FEISHU_APP_ID', 'CTI_FEISHU_APP_SECRET', 'CTI_FEISHU_ALLOWED_USERS'):
                if not values.get(key, '').strip():
                    parser.error(f'请先在本地 config.env 配置 {key}，不要把密钥发到公开仓库')
        run(['node', 'dist/daemon.mjs'], SKILL, env)


if __name__ == '__main__':
    main()
