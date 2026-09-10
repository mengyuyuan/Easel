"""Assert easel sends the canonical macOS client identity tuple."""

import importlib.util
import sys

spec = importlib.util.spec_from_file_location("gq", "easel/gateway_questions.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if hasattr(mod, "_client_identity"):
    ident = mod._client_identity()
else:
    ident = {"platform": mod._client_platform(), "deviceFamily": None}
print("easel client identity:", ident)

expected = {"platform": "macos", "deviceFamily": "Mac"}
if ident != expected:
    print("::error title=client identity::expected " + repr(expected)
          + " on macOS but got " + repr(ident)
          + " - the Gateway compares both fields against the paired device record"
          + " and answers a mismatch with requirePairing(metadata-upgrade).")
    sys.exit(1)
print("OK: canonical macOS tuple")
