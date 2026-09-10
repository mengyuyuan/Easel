#!/usr/bin/env bash
# 对照实验：作者版 _client_platform vs 完整版 _client_identity 的 metadata 比对
echo "===== A. 作者版（ccc5cdb, easel-verify）====="
/home/mozhe/easel-venv/bin/python -c "
import sys
sys.path.insert(0, '/home/mozhe/easel-verify')
import easel.gateway_questions as gq
print('module:', gq.__file__)
print('has _client_identity:', hasattr(gq, '_client_identity'))
print('has _client_platform:', hasattr(gq, '_client_platform'))
c = gq.GatewayClient()
try:
    c.connect()
    print('CONNECT OK')
    r = c.list_questions(session_key='agent:main:nonexistent', status='pending')
    print('list_questions OK:', r)
except Exception as e:
    print('FAILED:', type(e).__name__, str(e)[:500])
finally:
    try: c.close()
    except Exception: pass
"
echo
echo "===== B. 完整版（easel-linux, _client_identity）====="
/home/mozhe/easel-venv/bin/python -c "
import sys
sys.path.insert(0, '/home/mozhe/easel-linux')
import easel.gateway_questions as gq
print('module:', gq.__file__)
print('has _client_identity:', hasattr(gq, '_client_identity'))
print('has _client_platform:', hasattr(gq, '_client_platform'))
c = gq.GatewayClient()
try:
    c.connect()
    print('CONNECT OK')
    r = c.list_questions(session_key='agent:main:nonexistent', status='pending')
    print('list_questions OK:', r)
except Exception as e:
    print('FAILED:', type(e).__name__, str(e)[:500])
finally:
    try: c.close()
    except Exception: pass
"
