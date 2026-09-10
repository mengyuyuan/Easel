"""Assert easel sends the canonical OpenClaw client identity tuple for this OS.

OpenClaw maps process.platform -> {platform, deviceFamily} in
dist/gateway-client-platform-*.js. easel must send exactly the same tuple,
otherwise the Gateway flags a metadata mismatch and demands re-pairing.
"""
import importlib.util
import platform
import sys

EXPECTED = {
    "Darwin": {"platform": "macos", "deviceFamily": "Mac"},
    "Linux": {"platform": "linux", "deviceFamily": "Linux"},
    "Windows": {"platform": "windows", "deviceFamily": "Windows"},
}

spec = importlib.util.spec_from_file_location("gq", "easel/gateway_questions.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if hasattr(mod, "_client_identity"):
    ident = mod._client_identity()
else:
    ident = {"platform": mod._client_platform(), "deviceFamily": None}

system = platform.system()
expected = EXPECTED.get(system)
print("OS:", system)
print("expected (OpenClaw canonical):", expected)
print("easel sends                  :", ident)

if expected is None:
    print("::error title=client identity::unexpected platform " + system)
    sys.exit(2)

if ident != expected:
    msg = ("expected " + repr(expected) + " on " + system
           + " but easel sends " + repr(ident)
           + " - the Gateway compares both fields against the paired device"
           + " record and answers a mismatch with"
           + " requirePairing(metadata-upgrade), which kills the bridge.")
    print("::error title=client identity::" + msg)
    sys.exit(1)

print("::notice title=client identity::OK - canonical tuple for " + system)
