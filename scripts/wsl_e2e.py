#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WSL 端到端验证：easel web SSE -> ask_user question 事件 -> resolve 答案 -> agent 继续 -> done"""
import json, time, sys, urllib.request

BASE = "http://127.0.0.1:7860"
SESSION = f"wsl-verify-{int(time.time())}"
MSG = "请用 ask_user 工具问我一个问题：今天想发什么方向的内容？给我两个选项让我选。"

def sse_events(resp):
    cur = {}
    while True:
        raw = resp.readline()
        if not raw:
            return
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if line == "":
            if cur:
                yield cur
                cur = {}
            continue
        field, _, value = line.partition(":")
        value = value.lstrip(" ")
        if field == "event":
            cur["event"] = value
        elif field == "data":
            cur["data"] = value

print(f"[0] session={SESSION}")
body = json.dumps({"message": MSG, "sessionId": SESSION}).encode()
req = urllib.request.Request(f"{BASE}/api/chat/stream", data=body,
    headers={"Content-Type": "application/json", "Accept": "text/event-stream"}, method="POST")
resp = urllib.request.urlopen(req, timeout=600)
print("[1] SSE 流已建立，等待 agent ...")

question = None
tokens = []
answered = False
done = False
deadline = time.time() + 300

with resp:
    for ev in sse_events(resp):
        if time.time() > deadline:
            print("[!] 5分钟超时，退出"); break
        et = ev.get("event")
        if et == "token":
            try: tokens.append(json.loads(ev.get("data", '""')))
            except Exception: pass
        elif et == "activity":
            print(f"    [activity] {ev.get('data','')[:120]}")
        elif et == "question" and question is None:
            question = json.loads(ev["data"])
            print("[2] ===== 收到 question 事件（ask_user 卡片数据）=====")
            print(json.dumps(question, ensure_ascii=False, indent=2)[:2200])
            # 立刻提交答案：每题选第一个选项
            qs = question.get("questions", [])
            answers = {}
            for it in qs:
                opts = it.get("options") or []
                if opts:
                    answers[it.get("questionId")] = [opts[0].get("label")]
                else:
                    answers[it.get("questionId")] = ["好的"]
            print(f"[3] 提交答案: {json.dumps(answers, ensure_ascii=False)}")
            body2 = json.dumps({"questionId": question["id"], "answers": answers,
                                "sessionId": SESSION}).encode()
            req2 = urllib.request.Request(f"{BASE}/api/chat/question/answer", data=body2,
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req2, timeout=60) as r2:
                    print(f"[4] answer 接口响应: {r2.read().decode('utf-8')[:500]}")
                answered = True
            except Exception as e:
                print(f"[!] answer 提交失败: {e}")
        elif et == "error":
            print(f"[!] error 事件: {ev.get('data','')[:300]}")
        elif et == "done":
            done = True
            print("[5] done 事件到达")
            break

text = "".join(tokens)
print()
print("===== 结果汇总 =====")
print(f"question 事件: {'✓ 收到' if question else '✗ 未收到'}")
print(f"答案提交:     {'✓ 成功' if answered else '✗ 未提交'}")
print(f"done 事件:    {'✓ 到达' if done else '✗ 未到达'}")
print(f"agent 后续输出 ({len(tokens)} 个 token 片段):")
print(text[:600])
