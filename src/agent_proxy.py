"""Database Manager — CLIProxyAPI & Google/Antigravity Agentic Gateway.

Discovers local CLIProxyAPI (`127.0.0.1:8317/v1`) dynamically via
`ecosystem-registry.json`, surfaces authenticated Google / Antigravity account
status from `~/.cli-proxy-api/` without exposing token secrets, starts the local
proxy on demand when requested by the user, and powers AI-assisted GitHub audit
reports, refresh summaries, and cross-domain Q&A.

Zero third-party dependencies (Python 3.10+ Standard Library only).
"""

from __future__ import annotations

import datetime
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PROXY_URL = "http://127.0.0.1:8317"
DEFAULT_AI_REPORT_PATH = (
    Path(os.environ.get("USERPROFILE") or Path.home())
    / "Downloads"
    / "GitHub Repositories - AI Agent Executive Report.md"
)


def _load_json_safe(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _mask_account_name(raw: str) -> str:
    """Mask email usernames lightly while keeping connected account distinguishable."""
    if "@" not in raw:
        return raw
    local, domain = raw.split("@", 1)
    if len(local) <= 3:
        masked = local[0] + "***"
    else:
        masked = local[:3] + "***" + local[-1]
    return f"{masked}@{domain}"


def discover_cliproxy_config(
    auth_dir: Path | None = None,
) -> dict[str, Any]:
    """Resolve CLIProxyAPI endpoint, launcher files, and connected account metadata."""
    reg_env = os.environ.get("LOCAL_ECOSYSTEM_REGISTRY")
    reg_candidates = [
        Path(reg_env) if reg_env else Path.home() / ".local" / "share" / "ecosystem-registry.json",
        Path(os.environ.get("LOCALAPPDATA", "")) / "SharedLibraries" / "ecosystem-registry.json",
    ]
    registry: dict[str, Any] = {}
    registry_path_used: str | None = None
    for cand in reg_candidates:
        if cand.is_file():
            registry = _load_json_safe(cand)
            registry_path_used = str(cand)
            break

    proxy_cfg = ((registry.get("services") or {}).get("cliProxyApi") or {})
    base_url = str(os.environ.get("CLIPROXY_URL") or proxy_cfg.get("url") or DEFAULT_PROXY_URL).rstrip("/")
    openai_base = str(os.environ.get("CLIPROXY_OPENAI_BASE") or proxy_cfg.get("openaiBase") or f"{base_url}/v1").rstrip("/")

    proxy_dir = auth_dir or Path(os.environ.get("CLIPROXY_AUTH_DIR") or (Path.home() / ".cli-proxy-api"))
    accounts: list[dict[str, str]] = []
    if proxy_dir.is_dir():
        for fp in sorted(proxy_dir.glob("*.json"), key=lambda p: p.name.lower()):
            stem = fp.stem
            if "-" not in stem:
                continue
            provider, ident = stem.split("-", 1)
            provider_l = provider.lower()
            if provider_l in ("antigravity", "gemini", "google", "claude", "codex", "kimi", "qwen", "iflow"):
                label_provider = "Google / Antigravity" if provider_l in ("antigravity", "gemini", "google") else provider.title()
                accounts.append(
                    {
                        "provider": label_provider,
                        "account": _mask_account_name(ident),
                        "file": fp.name,
                    }
                )

    vbs_launcher = proxy_dir / "start-cliproxy-hidden.vbs"
    bat_launcher = proxy_dir / "run-cliproxy.bat"
    config_yaml = proxy_dir / "config.yaml"
    exe_candidates = [
        proxy_dir / "cli-proxy-api.exe",
        Path.home() / ".local" / "bin" / "cliproxyapi.exe",
    ]
    exe_found = next((str(p) for p in exe_candidates if p.is_file()), shutil.which("cliproxyapi"))

    # Optional Bearer token in ecosystem-secrets.json (never exposed back to UI)
    sec_env = os.environ.get("LOCAL_ECOSYSTEM_SECRETS")
    sec_path = Path(sec_env) if sec_env else Path((registry.get("paths") or {}).get("secretsFile") or (Path.home() / ".local" / "share" / "ecosystem-secrets.json"))
    secrets = _load_json_safe(sec_path)
    api_key = ((secrets.get("tokens") or {}).get("cliProxyApi") or os.environ.get("CLIPROXY_API_KEY") or "")

    return {
        "registry_path": registry_path_used,
        "url": base_url,
        "openai_base": openai_base,
        "proxy_dir": str(proxy_dir),
        "config_yaml": str(config_yaml) if config_yaml.is_file() else None,
        "vbs_launcher": str(vbs_launcher) if vbs_launcher.is_file() else None,
        "bat_launcher": str(bat_launcher) if bat_launcher.is_file() else None,
        "executable": exe_found,
        "can_auto_start": bool(vbs_launcher.is_file() or bat_launcher.is_file() or exe_found),
        "accounts": accounts,
        "account_count": len(accounts),
        "google_account_count": sum(1 for a in accounts if "Google" in a["provider"]),
        "_api_key": api_key,
    }


def _pick_default_model(models: list[str]) -> str | None:
    if not models:
        return None
    preferred_prefixes = (
        "gemini-3",
        "gemini-2.5",
        "gemini-4",
        "claude-sonnet",
        "claude-opus",
        "gpt-",
    )
    for pref in preferred_prefixes:
        for m in models:
            if m.lower().startswith(pref) and "embed" not in m.lower() and "image" not in m.lower():
                return m
    for m in models:
        if "embed" not in m.lower():
            return m
    return models[0]


def fetch_proxy_models(openai_base: str, api_key: str = "", timeout: float = 2.5) -> tuple[bool, list[str], str | None]:
    """Probe CLIProxyAPI `/v1/models` endpoint."""
    headers = {"Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(f"{openai_base}/models", headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        raw_data = payload.get("data") if isinstance(payload, dict) else []
        models = sorted(
            {
                str(item.get("id"))
                for item in (raw_data or [])
                if isinstance(item, dict) and item.get("id")
            }
        )
        return True, models, None
    except urllib.error.HTTPError as exc:
        return False, [], f"HTTP {exc.code}"
    except Exception as exc:
        return False, [], str(exc)


def get_proxy_status(auth_dir: Path | None = None, timeout: float = 2.5) -> dict[str, Any]:
    """Return full sanitized CLIProxyAPI & Google account status plus live model catalog."""
    cfg = discover_cliproxy_config(auth_dir=auth_dir)
    online, models, probe_err = fetch_proxy_models(cfg["openai_base"], api_key=cfg["_api_key"], timeout=timeout)
    return {
        "online": online,
        "url": cfg["url"],
        "openai_base": cfg["openai_base"],
        "models": models,
        "default_model": _pick_default_model(models),
        "accounts": cfg["accounts"],
        "account_count": cfg["account_count"],
        "google_account_count": cfg["google_account_count"],
        "can_auto_start": cfg["can_auto_start"],
        "error": None if online else probe_err,
    }


def start_cliproxy_service(auth_dir: Path | None = None, wait_seconds: float = 5.0) -> dict[str, Any]:
    """Start local CLIProxyAPI daemon cleanly if it is offline and wait for readiness."""
    status = get_proxy_status(auth_dir=auth_dir, timeout=1.5)
    if status["online"]:
        return {**status, "started": False, "message": "CLIProxyAPI is already running."}

    cfg = discover_cliproxy_config(auth_dir=auth_dir)
    cmd: list[str] | None = None
    cwd = cfg["proxy_dir"] if Path(cfg["proxy_dir"]).is_dir() else str(ROOT_DIR)

    if os.name == "nt" and cfg["vbs_launcher"]:
        cmd = ["wscript.exe", cfg["vbs_launcher"]]
    elif cfg["executable"] and cfg["config_yaml"]:
        cmd = [cfg["executable"], "-config", cfg["config_yaml"]]
    elif os.name == "nt" and cfg["bat_launcher"]:
        cmd = ["cmd.exe", "/c", cfg["bat_launcher"]]
    elif cfg["executable"]:
        cmd = [cfg["executable"]]

    if not cmd:
        return {
            **status,
            "started": False,
            "message": "CLIProxyAPI launcher/binary not found on this machine.",
        }

    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        creation_flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
        kwargs["creationflags"] = creation_flags
    else:
        kwargs["start_new_session"] = True

    try:
        subprocess.Popen(cmd, **kwargs)
    except OSError as exc:
        return {**status, "started": False, "message": f"Failed to launch CLIProxyAPI: {exc}"}

    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        time.sleep(0.35)
        probe = get_proxy_status(auth_dir=auth_dir, timeout=1.2)
        if probe["online"]:
            return {**probe, "started": True, "message": "CLIProxyAPI started and connected."}

    final_status = get_proxy_status(auth_dir=auth_dir, timeout=1.5)
    return {
        **final_status,
        "started": bool(final_status["online"]),
        "message": "CLIProxyAPI launched; still warming up." if not final_status["online"] else "CLIProxyAPI connected.",
    }


def call_proxy_chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2200,
    timeout: float = 45.0,
    auth_dir: Path | None = None,
) -> dict[str, Any]:
    """Send an OpenAI-compatible chat completion request through local CLIProxyAPI."""
    cfg = discover_cliproxy_config(auth_dir=auth_dir)
    online, models, probe_err = fetch_proxy_models(cfg["openai_base"], api_key=cfg["_api_key"], timeout=2.5)
    if not online:
        return {
            "ok": False,
            "error": f"CLIProxyAPI is offline at {cfg['openai_base']} ({probe_err or 'unreachable'}). Start CLIProxyAPI first.",
        }

    chosen_model = (model or "").strip() or _pick_default_model(models) or "gemini-2.5-flash"
    body = json.dumps(
        {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if cfg["_api_key"]:
        headers["Authorization"] = f"Bearer {cfg['_api_key']}"

    req = urllib.request.Request(f"{cfg['openai_base']}/chat/completions", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        content = ""
        if choices and isinstance(choices[0], dict):
            msg = choices[0].get("message") or {}
            content = str(msg.get("content") or "").strip()
        if not content:
            return {"ok": False, "model": chosen_model, "error": "Model returned an empty response."}
        return {
            "ok": True,
            "model": data.get("model") or chosen_model,
            "content": content,
            "usage": data.get("usage") or {},
        }
    except urllib.error.HTTPError as exc:
        err_text = exc.read().decode("utf-8", errors="replace")[:350]
        return {"ok": False, "model": chosen_model, "error": f"Proxy HTTP {exc.code}: {err_text}"}
    except Exception as exc:
        return {"ok": False, "model": chosen_model, "error": f"Proxy request failed: {exc}"}


def _compact_github_context(
    repos: list[dict[str, Any]],
    doctor: dict[str, Any],
    local_sync: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a concise, token-efficient telemetry snapshot for agent analysis."""
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_repos": len(repos),
        "metrics": doctor.get("metrics"),
        "cache_metadata": doctor.get("cache_metadata"),
        "failing_repos": doctor.get("failing_repos", []),
        "behind_forks": doctor.get("behind_forks", []),
        "stale_push_anomalies": doctor.get("stale_push_anomalies", []),
        "unbuilt_repos": doctor.get("unbuilt_repos", []),
        "unreleased_top": [
            {"name": r.get("name"), "unreleased": r.get("unreleased_commits_count")}
            for r in repos
            if int(r.get("unreleased_commits_count") or 0) > 0
        ][:20],
        "missing_descriptions": [r.get("name") for r in repos if not str(r.get("description") or "").strip()][:20],
        "local_sync_counts": (local_sync or {}).get("counts"),
        "local_dirty_or_ahead": [
            {
                "folder": m.get("folder_name"),
                "web": m.get("web_full_name"),
                "status": m.get("sync_status"),
                "ahead": m.get("ahead_by"),
                "behind": m.get("behind_by"),
                "dirty": m.get("dirty_count"),
            }
            for m in ((local_sync or {}).get("matched") or [])
            if m.get("sync_status") != "synced"
        ],
        "local_only": [
            {"folder": l.get("folder_name"), "slug": l.get("github_slug"), "status": l.get("sync_status")}
            for l in ((local_sync or {}).get("local_only") or [])
        ],
        "web_only": [
            {"name": w.get("name"), "full_name": w.get("full_name"), "status": w.get("sync_status")}
            for w in ((local_sync or {}).get("web_only") or [])
        ][:25],
        "deleted_on_web_since_last": (local_sync or {}).get("deleted_on_web_since_last", []),
        "deleted_locally_since_last": (local_sync or {}).get("deleted_locally_since_last", []),
    }


def generate_github_ai_report(
    repos: list[dict[str, Any]],
    doctor: dict[str, Any],
    local_sync: dict[str, Any] | None = None,
    model: str | None = None,
    destination: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Generate a prioritized Markdown executive audit via CLIProxyAPI and save to Downloads."""
    ctx = _compact_github_context(repos, doctor, local_sync)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a senior DevOps engineer analyzing a developer's GitHub & local workspace telemetry JSON. "
                "Write a crisp, actionable GitHub-flavored Markdown executive audit report grounded ONLY in the provided telemetry. "
                "Include: 1) Overall Health Snapshot, 2) Urgent CI Failures & Unbuilt Commits, 3) Local vs. Web Drift / Deleted Repos / Dirty Trees, "
                "4) Behind-Upstream Forks & Unreleased Tags, and 5) Concrete Next Commands (`gh repo sync`, `git push`, tag releases). Never invent repo names or metrics."
            ),
        },
        {
            "role": "user",
            "content": f"Telemetry JSON:\n{json.dumps(ctx, indent=2, ensure_ascii=False)}",
        },
    ]
    res = call_proxy_chat(messages, model=model, temperature=0.2, max_tokens=2200)
    if not res.get("ok"):
        return res

    dest_path = Path(destination) if destination else DEFAULT_AI_REPORT_PATH
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"<!-- Generated by Database Manager via CLIProxyAPI ({res['model']}) at {ctx['generated_at']} -->\n\n"
    )
    dest_path.write_text(header + res["content"].rstrip() + "\n", encoding="utf-8")
    return {
        "ok": True,
        "model": res["model"],
        "destination": str(dest_path),
        "content": res["content"],
        "usage": res.get("usage", {}),
    }


def summarize_github_refresh(
    repos: list[dict[str, Any]],
    doctor: dict[str, Any],
    local_sync: dict[str, Any] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Generate a concise post-refresh change summary and metadata/cleanup recommendations."""
    ctx = _compact_github_context(repos, doctor, local_sync)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an engineering assistant inside Database Manager. Give a concise, bulleted summary "
                "of the latest GitHub + local workspace refresh based strictly on the provided JSON: highlight newly "
                "detected deletions or local-only/web-only repos, failing CI builds, dirty/unpushed local clones, and "
                "repositories missing descriptions. Keep it short, readable, and non-destructive."
            ),
        },
        {
            "role": "user",
            "content": f"Refresh Snapshot:\n{json.dumps(ctx, indent=2, ensure_ascii=False)}",
        },
    ]
    return call_proxy_chat(messages, model=model, temperature=0.2, max_tokens=1200)


def ask_cross_domain_agent(
    question: str,
    context_summary: dict[str, Any],
    model: str | None = None,
) -> dict[str, Any]:
    """Answer a natural-language question using live Database Manager multi-domain context."""
    q = str(question or "").strip()
    if not q:
        return {"ok": False, "error": "Question cannot be empty."}

    messages = [
        {
            "role": "system",
            "content": (
                "You are the Database Manager AI assistant running via local CLIProxyAPI. "
                "Answer concisely using ONLY the live multi-domain JSON context supplied (PC parts, Games & benchmarks, "
                "AI models, Media, Books, Phones, GitHub repos). If specific data isn't in the context snippet, say so clearly."
            ),
        },
        {
            "role": "user",
            "content": f"User question: {q}\n\nDatabase context:\n{json.dumps(context_summary, indent=2, ensure_ascii=False)[:14000]}",
        },
    ]
    return call_proxy_chat(messages, model=model, temperature=0.2, max_tokens=1600)
