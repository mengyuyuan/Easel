# Easel PR #8 — 验证证据材料

本目录存放 Easel PR #8（ask_user question cards）的验证截图与日志。

## 目录结构

- `web/` — Web 端修复效果截图（01-chat-page → 05-reply-done：卡片、选择、提交、agent 回复完整呈现；`old-run/` 为旧版留存）
- `scripts/` — 验证脚本（wsl_ping.sh / wsl_e2e.py / wsl_render_shot3.py / wsl_identity_test.sh）
- `cli/` — CLI 端（openclaw tui）对照截图与渲染源文件
  - `cli-1-before-default.png` — 修复前：默认状态，问题和选项完全不可见
  - `cli-2-before-verbose-on.png` — 修复前：`/verbose on` 后问题可见，选项仍不可见
  - `cli-3-after-fixed.png` — 修复后：问题 + 选项都显示在卡片上
  - `cli-4-after-answer.png` — 修复后：输入数字完成回答
  - `*.html` — 截图的 HTML 源（可用浏览器打开或重新渲染）
- `evidence-log.md` — 完整证据日志（时间线、代码级发现、跨平台验证）

## 使用

- PR #8 评论附图 / 说明材料。
- 重渲截图：用 Chrome headless 对 `cli/*.html` 截图即可。
