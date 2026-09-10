#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WSL(Linux) Easel 渲染验证 v3：新会话 → 发消息 → ask_user 卡片 → 选择 → 提交 → 等生成结束 → 回复呈现截图"""
import os, sys
from playwright.sync_api import sync_playwright

CHROME = r"C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe"
OUT = r"C:\Users\Administrator\AppData\Local\Temp\easel-wsl-shots3"
URL = "http://172.23.227.107:7860/"
MSG = "请用 ask_user 工具问我一个问题：今天想发什么方向的内容？给我两个选项让我选。"

os.makedirs(OUT, exist_ok=True)

def shot(pg, name):
    pg.screenshot(path=f"{OUT}/{name}.png")
    print(f"[shot] {name}.png")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 950})

    pg.goto(URL, wait_until="domcontentloaded", timeout=30000)
    pg.wait_for_timeout(4500)

    # 确保在对话页
    if pg.query_selector("textarea") is None:
        for sel in ["text=开始对话", "text=对话"]:
            try:
                pg.click(sel, timeout=4000, strict=False)
                break
            except Exception:
                continue
        pg.wait_for_timeout(2500)

    # 新建干净会话
    try:
        pg.click(".new-chat-btn", timeout=4000)
        pg.wait_for_timeout(2200)
        print("[nav] clicked .new-chat-btn")
    except Exception as e:
        print("[nav] new-chat-btn not clicked, keep current session:", str(e)[:90])

    n = pg.eval_on_selector_all("textarea", "els => els.length")
    print(f"[nav] textarea count={n}")
    if n == 0:
        print("[!] no textarea, body:", pg.eval_on_selector("body", "el => el.innerText.slice(0,300)"))
        b.close(); sys.exit(1)

    leftover = pg.query_selector(".question-card")
    print(f"[check] initial question-card: {'EXISTS(old)' if leftover else 'NONE'}")
    shot(pg, "01-chat-page")

    ta = pg.query_selector("textarea")
    ta.click()
    pg.keyboard.type(MSG, delay=8)
    pg.wait_for_timeout(300)
    pg.keyboard.press("Enter")
    print("[send] message sent, waiting for ask_user card ...")

    pg.wait_for_selector(".question-card", timeout=240000)
    pg.wait_for_timeout(1500)
    shot(pg, "02-question-card")
    txt = pg.eval_on_selector(".question-card", "el => el.innerText")
    print("[card] ===== card text =====")
    print(txt[:700])

    pg.click(".question-card__option")
    pg.wait_for_timeout(700)
    shot(pg, "03-selected")

    pg.click(".question-card__submit")
    pg.wait_for_timeout(1800)
    shot(pg, "04-submitted")
    print("[submit] submitted, waiting for generation to finish ...")

    try:
        pg.wait_for_function("() => document.body.innerText.includes('生成中')", timeout=15000)
        print("[gen] '生成中' indicator seen")
    except Exception:
        print("[gen] '生成中' not captured (maybe already done)")

    try:
        pg.wait_for_function("() => !document.body.innerText.includes('生成中')", timeout=360000)
        print("[gen] generation finished")
    except Exception as e:
        print("[gen] wait generation-end TIMEOUT:", str(e)[:120])

    # 等界面文本稳定（打字机吐完）
    prev, stable = None, 0
    for _ in range(90):
        t = pg.evaluate("() => document.body.innerText")
        if t == prev:
            stable += 1
        else:
            stable = 0
            prev = t
        if stable >= 3:
            break
        pg.wait_for_timeout(2000)
    print(f"[stable] text stable (stable={stable})")

    # 滚到底部
    pg.evaluate("() => { document.querySelectorAll('*').forEach(e => { if (e.scrollHeight > e.clientHeight + 40) e.scrollTop = e.scrollHeight; }); }")
    pg.wait_for_timeout(800)
    shot(pg, "05-reply-done")

    tail = pg.evaluate("() => document.body.innerText")
    print("===== page text tail 1200 chars =====")
    print(tail[-1200:])

    b.close()

print("\n===== shots =====")
for f in sorted(os.listdir(OUT)):
    print(" ", f)
