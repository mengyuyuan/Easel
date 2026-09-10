#!/usr/bin/env python3
"""ask_cli — 在终端里接收并回答 OpenClaw 的 ask_user 问题。

背景：OpenClaw 的 TUI（openclaw tui / easel chat）没有渲染 ask_user 的代码
（dist/tui-*.js 里 ask_user 出现 0 次），问题只会挂到 Gateway 的 question 管理器里，
官方只有 Control UI 消费它。本脚本复用 easel 自带的 gateway 桥接，把待答问题拉到终端，
让你在 CLI 一侧也能看到并作答。

用法：
    python scripts/ask_cli.py                      监听所有会话的待答问题
    python scripts/ask_cli.py --session easel-xxx  只监听某个会话
    python scripts/ask_cli.py --once               答完一轮就退出
    python scripts/ask_cli.py --interval 0.5       轮询间隔（秒）

典型用法：一个终端跑 easel chat（TUI），另一个终端跑本脚本；
agent 调 ask_user 时，本脚本会在第二个终端里列出选项让你选。
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from easel.gateway_questions import GatewayClient, GatewayQuestionError  # noqa: E402

E = chr(27)
DIM = E + '[0;90m'
CYAN = E + '[0;36m'
GREEN = E + '[0;32m'
YELLOW = E + '[0;33m'
RED = E + '[0;31m'
NC = E + '[0m'


def render(question: dict) -> None:
    qid = question.get('id') or ''
    session = question.get('sessionKey') or ''
    print()
    print(CYAN + '┌─ ask_user ────────────────────────────────────────────────' + NC)
    print(DIM + '  会话: ' + str(session) + NC)
    print(DIM + '  id  : ' + str(qid) + NC)
    for idx, item in enumerate(question.get('questions') or []):
        if idx:
            print(CYAN + '├───────────────────────────────────────────────────────────' + NC)
        header = item.get('header')
        title = ('[' + str(header) + '] ') if header else ''
        print(CYAN + '│ ' + NC + title + str(item.get('question') or '请选择'))
        for i, opt in enumerate(item.get('options') or [], 1):
            desc = opt.get('description')
            suffix = ('  ' + DIM + '— ' + str(desc) + NC) if desc else ''
            print(CYAN + '│   ' + GREEN + str(i) + ')' + NC + ' ' + str(opt.get('label')) + suffix)
        if item.get('isOther'):
            print(CYAN + '│   ' + YELLOW + '0)' + NC + ' 自行输入…')
    print(CYAN + '└───────────────────────────────────────────────────────────' + NC)


def ask_one(item: dict) -> str:
    options = item.get('options') or []
    is_other = bool(item.get('isOther'))
    while True:
        try:
            raw = input('  请选择: ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return ''
        if raw == '0' and is_other:
            try:
                custom = input('  输入内容: ').strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return ''
            if custom:
                return custom
            continue
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return str(options[int(raw) - 1].get('label'))
        for opt in options:
            if raw and raw == opt.get('label'):
                return raw
        hint = ('，或 0 自行输入') if is_other else ''
        print('  ' + RED + '无效选择，请输入 1-' + str(len(options)) + hint + NC)


def handle(client: GatewayClient, question: dict) -> bool:
    render(question)
    answers = {}
    for item in question.get('questions') or []:
        picked = ask_one(item)
        if not picked:
            print('  ' + YELLOW + '已跳过（问题继续挂着，agent 仍在等待）' + NC)
            return False
        answers[item['questionId']] = [picked]
    try:
        result = client.resolve(question['id'], answers, resolved_by='easel-ask-cli')
    except GatewayQuestionError as exc:
        print('  ' + RED + '提交失败: ' + str(exc) + NC)
        return False
    print('  ' + GREEN + '✓ 已提交 ' + str(answers) + ' -> ' + str(result.get('status')) + NC)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description='在终端里接收并回答 ask_user 问题')
    ap.add_argument('--session', help='只监听该会话（sessionKey 或 web sessionId）')
    ap.add_argument('--interval', type=float, default=1.0, help='轮询间隔秒（默认 1.0）')
    ap.add_argument('--once', action='store_true', help='答完一轮就退出')
    args = ap.parse_args()

    target = args.session
    if target and not target.startswith('agent:'):
        target = 'agent:main:' + target

    scope = ('（会话 ' + target + '）') if target else '（所有会话）'
    print(CYAN + 'ask_cli' + NC + ' — 监听 ask_user 问题' + scope + '，Ctrl+C 退出')

    seen = set()
    client = None
    try:
        while True:
            if client is None:
                try:
                    client = GatewayClient()
                    client.connect()
                    print(DIM + '  已连接 Gateway' + NC)
                except Exception as exc:  # noqa: BLE001
                    client = None
                    print(RED + '  连接 Gateway 失败: ' + str(exc) + NC)
                    time.sleep(max(args.interval, 2.0))
                    continue
            try:
                pending = client.list_questions(status='pending')
            except Exception as exc:  # noqa: BLE001
                print(YELLOW + '  查询失败，重连: ' + str(exc) + NC)
                try:
                    client.close()
                except Exception:  # noqa: BLE001
                    pass
                client = None
                time.sleep(args.interval)
                continue
            for q in pending:
                qid = q.get('id')
                if not qid or qid in seen:
                    continue
                if target and q.get('sessionKey') != target:
                    continue
                exp = q.get('expiresAtMs')
                seen.add(qid)
                if exp and exp < time.time() * 1000:
                    continue
                handle(client, q)
                if args.once:
                    return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print()
        print(DIM + '  退出' + NC)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:  # noqa: BLE001
                pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
