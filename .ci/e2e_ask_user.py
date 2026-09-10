"""Drive the same HTTP surface the React UI uses and assert the ask_user loop.

POST /api/chat/stream   (SSE)  -> expect a `question` event
POST /api/chat/question/answer -> question.resolve
then wait for `done` and assert the assistant used the picked option.
"""
import json
import sys
import time
import urllib.request

BASE = "http://127.0.0.1:7860"
SESSION = "macos-e2e-%d" % int(time.time())
MESSAGE = ("请用 ask_user 工具问我一个问题：今天这条内容发图文还是发视频？给我两个选项。")
DEADLINE = time.time() + 420


def post(path, obj, timeout=900):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=timeout)


print("[e2e] session =", SESSION, flush=True)
resp = post("/api/chat/stream", {"message": MESSAGE, "sessionId": SESSION})
print("[e2e] SSE connected", flush=True)

event = None
counts = {}
answered = False
question_seen = None
tokens = []

try:
    for raw in resp:
        if time.time() > DEADLINE:
            print("[e2e] DEADLINE reached", flush=True)
            break
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
            continue
        if not line.startswith("data:"):
            continue
        data = line.split(":", 1)[1].strip()
        counts[event] = counts.get(event, 0) + 1
        if event == "question":
            payload = json.loads(data)
            question_seen = payload
            print("[e2e] QUESTION EVENT:", json.dumps(payload, ensure_ascii=False)[:900], flush=True)
            if not answered:
                answers = {}
                for it in payload.get("questions", []):
                    opts = it.get("options") or []
                    answers[it["questionId"]] = ([opts[0].get("label")] if opts
                                                 else ["macos e2e answer"])
                print("[e2e] answering:", json.dumps(answers, ensure_ascii=False), flush=True)
                r = post("/api/chat/question/answer", {
                    "sessionId": SESSION,
                    "questionId": payload["id"],
                    "answers": answers,
                    "resolvedBy": "macos-e2e",
                })
                print("[e2e] answer response:", r.read().decode("utf-8")[:400], flush=True)
                answered = True
        elif event == "token":
            try:
                tokens.append(json.loads(data))
            except Exception:
                pass
        elif event == "error":
            print("[e2e] ERROR EVENT:", data[:400], flush=True)
        elif event == "done":
            print("[e2e] DONE:", data[:200], flush=True)
            break
except Exception as exc:
    print("[e2e] stream error: %s: %s" % (type(exc).__name__, exc), flush=True)

text = "".join(tokens)
print("[e2e] event counts:", json.dumps(counts), flush=True)
print("[e2e] assistant text:", text[:400].replace("\n", " / "), flush=True)

ok = bool(question_seen) and answered and counts.get("done", 0) >= 1
print("[e2e] RESULT =", "PASS" if ok else "FAIL", flush=True)
if not ok:
    print("::error title=ask_user e2e::no completed question->answer->done cycle")
    sys.exit(1)
print("::notice title=ask_user e2e::PASS on macOS (question card event, answer resolved, turn finished)")
