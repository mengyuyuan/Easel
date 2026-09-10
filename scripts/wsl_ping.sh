#!/usr/bin/env bash
cd "$HOME/easel-linux" || exit 1
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
export PATH="$HOME/easel-venv/bin:$PATH"

echo "===== easel ping ====="
timeout 120 easel ping 2>&1 | tail -30
echo "PING_RC=$?"

echo
echo "===== 检查 7860 web 是否在跑 ====="
curl -s -m 3 -o /dev/null -w "web7860: %{http_code}\n" http://127.0.0.1:7860/ || echo "web 未运行"

echo
echo "===== easel-linux dist 是否含 question 卡片与打字机 ====="
ls ~/easel-linux/web/frontend/dist/assets/ 2>/dev/null | head -8
F=$(ls ~/easel-linux/web/frontend/dist/assets/index-*.js 2>/dev/null | head -1)
echo "主 JS: $F"
if [ -n "$F" ]; then
  echo "question-card 数量: $(grep -o 'question-card' "$F" | wc -l)"
  echo "answerQuestion 数量: $(grep -o 'answerQuestion' "$F" | wc -l)"
fi
