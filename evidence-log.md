# Easel ask_user 问题卡片 — 验证证据日志

2026-09-09 / 09-10 · Windows 11 + WSL Ubuntu 26.04 · openclaw@2026.9.2

## 背景

Easel（社媒内容工作台，ZJU-REAL/Easel）的 `ask_user` 工具提问时，自研 web 前端不显示问题卡片（用户报告：「跳出的选项不在 web 端显示」）。
本目录汇总修复与跨平台验证的全部证据，供 PR #8 使用。

## 一、Web 端（PR #8 主体修复）

- **截图**：`web/` 目录（01-chat-page → 05-reply-done，2026-09-11 00:24 重拍版；旧版留存于 `web/old-run/`）— 问题卡片渲染、选项选择、提交、agent 回复完整呈现（05 含完整产出回复 + 输入区回到空闲态）。
- **全链路**：SSE `question` 事件 → 卡片渲染 → 提交答案 → gateway resolve → agent 恢复 → `done`（通过）。
- **复核（2026-09-11 00:20，Linux/WSL）**：API e2e 重跑通过（question 事件 → `answered` → `done` → agent 产出整期内容）；浏览器完整 UI 流程重拍 5 张截图通过。

## 二、CLI 端（openclaw tui）排查与修复

### 发现 1：默认 verbose=off，所有工具卡片（含 ask_user）不渲染

- **证据**：`cli/cli-1-before-default.png` — 触发 ask_user 后终端只有
  `This response is taking longer than expected. Still waiting for the current run.`
- **代码级**（tui 包）：
  ```js
  if (evt.stream === "tool") {
      const verbose = state.sessionInfo.verboseLevel ?? "off";
      if (!allowToolEvents) return;          // ← 默认 off 时直接丢弃
      ...
      chatLog.startTool(toolCallId, toolName, data.args, evt.runId);
  }
  ```
- **修复**：配置 `agents.defaults.verboseDefault = "on"`（openclaw.json），或会话内 `/verbose on`。

### 发现 2：开启 verbose 后只有问题文本，选项不可见

- **证据**：`cli/cli-2-before-verbose-on.png` — 卡片显示 `❓ Ask User (running)` + 问题文本，但选项缺失。
- **代码级**（tool-display 包）：
  - `TOOL_DISPLAY_CONFIG.ask_user.detailKeys = ["questions.0.question"]` — 只取问题字段；
  - `coerceDisplayValue()` 没有 object 分支 → `options: [{label},…]` 对象数组无法渲染。
- **修复**（本机补丁，两处）：
  1. `coerceDisplayValue` 增加 object 分支（取 `label`/`text`/`title`/`name` 首个非空字符串）；
  2. `ask_user.detailKeys` 增加 `"questions.0.options"`。
- **效果**：`cli/cli-3-after-fixed.png` — `question 午餐吃什么？, options 面条, 米饭`。

### 回答闭环

- 终端直接输入数字（`1`/`2`/…）或文字回答，gateway 解析并恢复 run。
- **证据**：`cli/cli-4-after-answer.png` — 输入 `1` 后：`你选择了 面条 🍜`。

## 三、跨平台验证

- **WSL Ubuntu 26.04**（09-11 00:20 复核）：`easel ping` rc=0 — `Step 1: Gateway healthz OK`、`Step 2: agent PONG OK`、`✓ 全部通过`；web 端 ask_user 全链路（API e2e + 浏览器 UI）通过；TUI 卡片显示 + 回答通过。
- **对照实验（Linux）**：作者版 `_client_platform`（仅 platform 字段）→ `CONNECT FAILED: NOT_PAIRED, metadata-upgrade`；完整版 `_client_identity`（platform + deviceFamily + darwin→macos 映射）→ `CONNECT OK`。（证明分支修复必须保留）
- **Windows**：openclaw.json 加 `verboseDefault:"on"` + tool-display 两处补丁 + gateway 重启。

## 四、注意事项

- CLI 侧的显示补丁打在 openclaw npm 包内（`dist/tool-display-*.js`），openclaw 升级会还原，需重打（方法已记录于 easel-social-media-workbench 技能）。
- 上游建议：openclaw 的 TUI 若能原生渲染 ask_user 卡片（含选项），则无需本补丁。TUI 官方支持界面列表目前不含 TUI 的 ask_user 交互。


## 五、Windows 端验证（2026.9.10 深夜）

- **配置**：openclaw.json 加 `agents.defaults.verboseDefault="on"` + tool-display 同款两处补丁（node 模块 LOAD OK 验证通过）。
- **gateway 重启**（D:\Easel\gw-run.ps1）后，TUI footer 直接显示 `verbose on`（默认值生效）。
- **agent 调用 ask_user**：gateway 侧 question 记录 `win验证 / 喝咖啡还是茶？ / options: 咖啡, 茶`；会话诊断日志 `reason=blocked_tool_call`（agent 在等待回答）。
- **盲答链路**：TUI 直接输入 `1` → `question.waitAnswer 217659ms` 返回 → agent 恢复，回复「你选了 面 🍜」；第二题（喝水还是喝可乐）盲答 `1` → `waitAnswer 213126ms` → 「你选了 水 💧」。
- 说明：Windows TUI 为 pty 重绘流（无 tmux），卡片渲染帧未落盘留存；渲染代码与 WSL 同版本同补丁（Linux 端 4 张截图即渲染效果）。
- **坑位记录**：billing fail 后 inline key 熔断约 8 分钟；Easel 原 key 欠费 → 已换（新 key）；gateway 重启会触发 main-session-restart-recovery 拉起中断会话（可能挂在新 ask_user 上，需 resolve）。
