"""Probe easel.openclaw_cmd.openclaw_base_cmd() on the host OS.

Usage:
  probe_launcher.py <path-to-openclaw_cmd.py>
  probe_launcher.py --run <path-to-openclaw_cmd.py>

Exit 0 = resolved (and, with --run, the resolved command ran)
Exit 3 = openclaw_base_cmd() raised
Exit 4 = resolved, but the resolved command is not runnable
"""
import importlib.util
import subprocess
import sys


def main() -> int:
    argv = sys.argv[1:]
    do_run = False
    if argv and argv[0] == "--run":
        do_run = True
        argv = argv[1:]
    spec = importlib.util.spec_from_file_location("oc", argv[0])
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        cmd = module.openclaw_base_cmd()
    except Exception as exc:
        print("   RAISED: %s: %s" % (type(exc).__name__, str(exc)[:220]))
        return 3
    print("   RESULT:", cmd)
    if not do_run:
        return 0
    proc = subprocess.run(cmd + ["--version"], capture_output=True, text=True, timeout=300)
    print("   RUN exit:", proc.returncode)
    print("   RUN stdout:", proc.stdout.strip()[:200])
    print("   RUN stderr:", proc.stderr.strip()[:300])
    return 0 if proc.returncode == 0 else 4


if __name__ == "__main__":
    sys.exit(main())
