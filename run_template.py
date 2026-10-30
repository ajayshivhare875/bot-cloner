"""Runner: launches a single template bot with env-provided token."""
import os, importlib.util, sys

token = os.environ.get("CLONE_TOKEN", "")
template = os.environ.get("CLONE_TEMPLATE", "")
if not token or not template:
    print("CLONE_TOKEN and CLONE_TEMPLATE required", flush=True)
    sys.exit(1)

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", f"{template}.py")
spec = importlib.util.spec_from_file_location(template, path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(f"Starting template '{template}'...", flush=True)
mod.run(token)
