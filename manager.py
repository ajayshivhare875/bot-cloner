"""Bot Cloner Manager - spawns/manages cloned bot instances."""
import os, json, subprocess, signal, time
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
INSTANCES_FILE = os.path.join(DATA, "instances.json")
os.makedirs(DATA, exist_ok=True)
os.makedirs(os.path.join(BASE, "instances"), exist_ok=True)


def _load():
    try:
        with open(INSTANCES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d):
    tmp = INSTANCES_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, INSTANCES_FILE)


def list_templates():
    """Return {name: info} for all templates."""
    import importlib.util
    result = {}
    tdir = os.path.join(BASE, "templates")
    for fn in sorted(os.listdir(tdir)):
        if fn.startswith("_") or not fn.endswith(".py"):
            continue
        name = fn[:-3]
        try:
            spec = importlib.util.spec_from_file_location(name, os.path.join(tdir, fn))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            result[name] = getattr(mod, "INFO", {"name": name, "emoji": "🤖", "description": ""})
        except Exception as e:
            result[name] = {"name": name, "emoji": "⚠️", "description": f"load error: {e}"}
    return result


def _is_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def clone_bot(template, token, owner_id, owner_name=""):
    """Spawn a new bot instance. Returns (instance_id, error)."""
    templates = list_templates()
    if template not in templates:
        return None, "Template not found"
    if not token or len(token) < 20 or ":" not in token:
        return None, "Invalid bot token format"

    instances = _load()
    # limit per user
    mine = [i for i in instances.values() if str(i.get("owner_id")) == str(owner_id)]
    if len(mine) >= 10:
        return None, "Max 10 cloned bots per user"

    iid = f"{template}_{int(time.time())}_{str(owner_id)[-4:]}"
    runner = os.path.join(BASE, "run_template.py")
    logf = os.path.join(BASE, "instances", f"{iid}.log")
    env = dict(os.environ)
    env["CLONE_TOKEN"] = token
    env["CLONE_TEMPLATE"] = template
    env["CLONE_OWNER"] = str(owner_id)
    # unset proxy vars that break Telegram
    env.pop("no_proxy", None); env.pop("NO_PROXY", None)

    with open(logf, "w") as lf:
        p = subprocess.Popen(
            [os.path.join(BASE, "venv", "bin", "python"), "-u", runner],
            env=env, stdout=lf, stderr=subprocess.STDOUT,
            start_new_session=True, cwd=BASE)
    time.sleep(3)
    if not _is_alive(p.pid):
        try:
            with open(logf) as f:
                tail = "".join(f.readlines()[-5:])
        except Exception:
            tail = "no log"
        return None, f"Bot failed to start. Log: {tail[:300]}"

    instances[iid] = {
        "template": template,
        "owner_id": str(owner_id),
        "owner_name": owner_name,
        "pid": p.pid,
        "status": "running",
        "created_at": datetime.now().isoformat(),
    }
    _save(instances)
    return iid, ""


def stop_bot(iid, owner_id):
    instances = _load()
    inst = instances.get(iid)
    if not inst or str(inst["owner_id"]) != str(owner_id):
        return False, "Not found"
    try:
        os.kill(inst["pid"], signal.SIGTERM)
    except Exception:
        pass
    inst["status"] = "stopped"
    _save(instances)
    return True, ""


def my_bots(owner_id):
    instances = _load()
    out = {}
    for iid, inst in instances.items():
        if str(inst["owner_id"]) == str(owner_id):
            inst["alive"] = _is_alive(inst.get("pid", 0))
            out[iid] = inst
    return out


def health_check():
    """Return {iid: alive} for all running instances. Restarts dead ones is done by watchdog."""
    instances = _load()
    return {iid: _is_alive(i.get("pid", 0)) for iid, i in instances.items()
            if i.get("status") == "running"}
