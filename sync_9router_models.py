#!/usr/bin/env python3
"""
Sync models from 9Router to Hermes Agent on vm101.
Maintains providers.router_xaiserv_my_id.models in config.yaml
and provider_models_cache.json.
"""
import os, sys, json, time, tempfile
import urllib.request

HERMES_DIR = "/home/xs/.hermes"
HERMES_AGENT = "/home/xs/.hermes/hermes-agent"
CONFIG_PATH = os.path.join(HERMES_DIR, "config.yaml")
CACHE_PATH = os.path.join(HERMES_DIR, "provider_models_cache.json")
ENV_PATH = os.path.join(HERMES_DIR, ".env")

sys.path.insert(0, HERMES_AGENT)
try:
    import hermes_bootstrap
    from hermes_yaml import YAML
except Exception as e:
    print(f"[SYNC ERROR] Failed to import hermes dependencies: {e}", file=sys.stderr)
    sys.exit(1)

def load_config(yaml_obj):
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml_obj.load(f)

def get_api_key(cfg, key_env):
    api_key = None
    if key_env and os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key_env}="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except Exception:
            pass
    if not api_key:
        api_key = cfg.get("model", {}).get("api_key")
    return api_key

def main(verbose=False):
    yaml_obj = YAML()
    yaml_obj.preserve_quotes = True

    cfg = load_config(yaml_obj)
    if not cfg:
        print("[SYNC ERROR] Cannot read config.yaml", file=sys.stderr)
        return 1

    p = cfg.get("providers", {}).get("router_xaiserv_my_id")
    if not p:
        if verbose:
            print("[SYNC] Provider router_xaiserv_my_id not configured in config.yaml")
        return 0

    base_url = (p.get("api") or p.get("base_url") or "https://router.xaiserv.my.id/v1").rstrip("/")
    key_env = p.get("key_env")
    api_key = p.get("api_key") or get_api_key(cfg, key_env)

    if not api_key:
        print("[SYNC ERROR] No API key found for 9Router", file=sys.stderr)
        return 1

    req = urllib.request.Request(
        f"{base_url}/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Hermes-9Router-Sync/1.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        if verbose:
            print(f"[SYNC] Upstream request to {base_url}/models failed: {e}")
        return 0  # Non-fatal: 9router might be temporarily restarting

    remote_models = [m["id"] for m in data.get("data", []) if isinstance(m, dict) and "id" in m]
    if not remote_models:
        if verbose:
            print("[SYNC] Received empty models list from 9Router, skipping.")
        return 0

    current_models = list(p.get("models") or [])
    
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}
            
    cache_stale = any(
        ("router_xaiserv_my_id" in k or "router.xaiserv.my.id" in k) and cache[k].get("models") != remote_models
        for k in cache if isinstance(cache[k], dict)
    )

    if remote_models == current_models and not cache_stale and p.get("discover_models") is True:
        if verbose:
            print(f"[SYNC] In sync ({len(remote_models)} models).")
        return 0

    added = set(remote_models) - set(current_models)
    removed = set(current_models) - set(remote_models)

    # 1. Update config.yaml atomically
    p["models"] = remote_models
    p["discover_models"] = True
    p["models_discovered"] = True

    dir_name = os.path.dirname(CONFIG_PATH)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix=".config_sync_tmp_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        yaml_obj.dump(cfg, f)
    os.replace(tmp_path, CONFIG_PATH)

    # 2. Update provider_models_cache.json
    cache = {}
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    cache["router_xaiserv_my_id"] = {
        "fp": "router_custom",
        "at": time.time(),
        "models": remote_models
    }
    for k in list(cache.keys()):
        if k.startswith("custom:") and "router.xaiserv.my.id" in k:
            if isinstance(cache[k], dict):
                cache[k]["models"] = remote_models
                cache[k]["at"] = time.time()
    
    fd2, tmp_cache = tempfile.mkstemp(dir=dir_name, prefix=".cache_sync_tmp_")
    with os.fdopen(fd2, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)
    os.replace(tmp_cache, CACHE_PATH)

    print(f"[SYNC] OK: {len(remote_models)} models synced from 9Router (added: {len(added)}, removed: {len(removed)})")
    if added:
        print(f"[SYNC] Added: {list(added)}")
    if removed:
        print(f"[SYNC] Removed: {list(removed)}")
    return 0

if __name__ == "__main__":
    is_verbose = "-v" in sys.argv or "--verbose" in sys.argv
    sys.exit(main(verbose=is_verbose))