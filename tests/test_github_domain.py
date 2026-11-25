#!/usr/bin/env python3
"""Unit & integration tests for the GitHub Repositories domain."""

from __future__ import annotations

import datetime
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import agent_proxy  # noqa: E402
import catalog_classifier  # noqa: E402
import server  # noqa: E402
from github import cli as github_cli  # noqa: E402
from github import exporter as github_exporter  # noqa: E402
from github import local_sync as github_local_sync  # noqa: E402
from github import scanner as github_scanner  # noqa: E402


class TestGitHubDomain(unittest.TestCase):
    def test_public_snapshot_contains_no_private_repos(self) -> None:
        pub_path = ROOT_DIR / "data" / "github" / "repos_public.json"
        self.assertTrue(pub_path.exists())
        data = json.loads(pub_path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 35)
        self.assertFalse(any(r.get("is_private") for r in data))

    def test_triage_buckets_and_push_commit_drift_guard(self) -> None:
        now = datetime.datetime(2026, 11, 24, 12, 0, 0, tzinfo=datetime.timezone.utc)
        repos = [
            {
                "name": "active-repo",
                "full_name": "Mostakim2005/active-repo",
                "is_fork": False,
                "is_private": False,
                "pushed_at": "2026-11-23T12:00:00Z",
                "recent_commits": [{"date": "2026-11-23T12:00:00Z"}],
                "latest_run": {"name": "CI", "status": "completed", "conclusion": "success"},
                "unreleased_commits_count": 2,
            },
            {
                "name": "mid-repo",
                "full_name": "Mostakim2005/mid-repo",
                "is_fork": False,
                "is_private": False,
                "pushed_at": "2026-11-18T12:00:00Z",
                "recent_commits": [{"date": "2026-11-18T12:00:00Z"}],
                "latest_run": None,
                "unreleased_commits_count": 0,
            },
            {
                "name": "stale-bump-repo",
                "full_name": "Mostakim2005/stale-bump-repo",
                "is_fork": True,
                "is_private": False,
                "pushed_at": "2026-11-23T12:00:00Z",
                "recent_commits": [{"date": "2026-08-26T12:00:00Z"}],
                "latest_run": {"name": "CI", "status": "in_progress", "conclusion": None},
                "unreleased_commits_count": 1,
            },
            {
                "name": "failing-repo",
                "full_name": "Mostakim2005/failing-repo",
                "is_fork": False,
                "is_private": True,
                "pushed_at": "2026-10-01T12:00:00Z",
                "recent_commits": [{"date": "2026-10-01T12:00:00Z"}],
                "latest_run": {"name": "CI", "status": "completed", "conclusion": "failure"},
                "unreleased_commits_count": 0,
            },
        ]

        triaged = github_scanner.triage_repositories(repos, now=now)
        self.assertEqual([r["name"] for r in triaged["section_1"]], ["active-repo"])
        self.assertEqual([r["name"] for r in triaged["section_2"]], ["mid-repo"])
        self.assertEqual([r["name"] for r in triaged["section_3"]], ["stale-bump-repo", "failing-repo"])
        self.assertTrue(triaged["section_3"][0]["stale_push_anomaly"])
        m = triaged["metrics"]
        self.assertEqual(m["total_repos"], 4)
        self.assertEqual(m["passing_ci"], 1)
        self.assertEqual(m["failing_ci"], 1)
        self.assertEqual(m["running_ci"], 1)
        self.assertEqual(m["no_ci"], 1)
        self.assertEqual(m["forks_count"], 1)
        self.assertEqual(m["private_count"], 1)
        self.assertEqual(m["total_unreleased_commits"], 3)

    def test_exporter_handles_none_runs_and_conclusions(self) -> None:
        now = datetime.datetime(2026, 11, 24, 12, 0, 0, tzinfo=datetime.timezone.utc)
        repos = [
            {
                "name": "sec2-no-ci",
                "full_name": "Mostakim2005/sec2-no-ci",
                "is_fork": False,
                "is_private": False,
                "pushed_at": "2026-11-18T10:00:00Z",
                "recent_commits": [{"date": "2026-11-18T10:00:00Z"}],
                "latest_run": None,
                "latest_release": None,
                "latest_tag": None,
                "unbuilt_commits_count": 3,
                "unreleased_commits_count": 0,
            },
            {
                "name": "sec3-running-ci",
                "full_name": "Mostakim2005/sec3-running-ci",
                "is_fork": True,
                "is_private": False,
                "pushed_at": "2026-10-10T10:00:00Z",
                "recent_commits": [{"date": "2026-10-10T10:00:00Z"}],
                "parent": {"full_name": "upstream/repo"},
                "upstream_comparison": {"status": "behind", "ahead_by": 1, "behind_by": 4},
                "latest_run": {"name": "Build", "status": "in_progress", "conclusion": None},
                "latest_release": None,
                "latest_tag": {"name": "v0.1.0"},
                "unbuilt_commits_count": 0,
                "unreleased_commits_count": 1,
            },
        ]

        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "audit.md"
            written = github_exporter.export_markdown_report(repos, destination=out_file, now=now)
            self.assertEqual(written, str(out_file))
            text = out_file.read_text(encoding="utf-8")
            self.assertIn("sec2-no-ci", text)
            self.assertIn("sec3-running-ci", text)
            self.assertIn("IN_PROGRESS", text)
            self.assertIn("+1 / -4", text)

    def test_cache_precedence_and_redaction(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            live = td_path / "live_cache.json"
            pub = td_path / "repos_public.json"
            sample = [
                {"name": "pub-repo", "is_private": False},
                {"name": "secret-repo", "is_private": True},
            ]
            pub.write_text(json.dumps([sample[0]]), encoding="utf-8")
            self.assertEqual(len(github_scanner.get_cached_repos(live, pub)), 1)

            live.write_text(json.dumps(sample), encoding="utf-8")
            self.assertEqual(len(github_scanner.get_cached_repos(live, pub)), 2)

            redacted = github_scanner.redact_public_repos(sample)
            self.assertEqual([r["name"] for r in redacted], ["pub-repo"])

    def test_doctor_and_classifier(self) -> None:
        repos = github_scanner.get_cached_repos()
        doc = github_cli.inspect_github_doctor(repos)
        self.assertTrue(doc["healthy"])
        self.assertGreaterEqual(doc["total_repos"], 35)
        self.assertIn("dataview-fork", doc["stale_push_anomalies"])

        cls = catalog_classifier.classify_github_catalog()
        self.assertGreaterEqual(cls["total"], 35)
        self.assertIn("dormant", cls["bucket_counts"])

    def test_github_http_endpoints_and_post_csrf_guard(self) -> None:
        api_srv = server.ReusableThreadingHTTPServer(("127.0.0.1", 0), server.DatabaseHandler)
        port = api_srv.server_address[1]
        thread = threading.Thread(target=api_srv.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{port}"
            with urllib.request.urlopen(f"{base}/api/status", timeout=5) as resp:
                status_payload = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(status_payload["counts"]["github"], 35)

            with urllib.request.urlopen(f"{base}/api/github?type=fork", timeout=5) as resp:
                forks = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(len(forks), 1)
                self.assertTrue(all(r.get("is_fork") for r in forks))

            with urllib.request.urlopen(f"{base}/api/github/triage", timeout=5) as resp:
                tri = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(tri["metrics"]["total_repos"], 35)

            with urllib.request.urlopen(f"{base}/api/github/doctor", timeout=5) as resp:
                doc = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(doc["healthy"])

            with urllib.request.urlopen(f"{base}/api/github/classified", timeout=5) as resp:
                cls = json.loads(resp.read().decode("utf-8"))
                self.assertGreaterEqual(cls["total"], 35)

            with urllib.request.urlopen(f"{base}/github/index.html", timeout=5) as resp:
                html_body = resp.read().decode("utf-8")
                self.assertEqual(resp.status, 200)
                self.assertNotIn("innerHTML", html_body)

            # Reject cross-origin POST (CSRF defense)
            for bad_origin in ("https://evil.example", "null"):
                req = urllib.request.Request(
                    f"{base}/api/github/export",
                    data=b"{}",
                    method="POST",
                    headers={"Origin": bad_origin},
                )
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=5)
                self.assertEqual(ctx.exception.code, 403)

            # Reject non-loopback Host header
            req_host = urllib.request.Request(
                f"{base}/api/github/export",
                data=b"{}",
                method="POST",
                headers={"Host": "evil.example:8770"},
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx_host:
                urllib.request.urlopen(req_host, timeout=5)
            self.assertEqual(ctx_host.exception.code, 403)

            # Allow same-origin loopback POST (mocking export target to temp dir)
            with tempfile.TemporaryDirectory() as td:
                tmp_md = str(Path(td) / "export.md")
                with mock.patch("github.exporter.export_markdown_report", return_value=tmp_md):
                    req_ok = urllib.request.Request(
                        f"{base}/api/github/export",
                        data=b"{}",
                        method="POST",
                        headers={"Origin": f"http://127.0.0.1:{port}"},
                    )
                    with urllib.request.urlopen(req_ok, timeout=5) as resp:
                        res_json = json.loads(resp.read().decode("utf-8"))
                        self.assertEqual(res_json["status"], "ok")
                        self.assertEqual(res_json["destination"], tmp_md)

            # Busy scan lock returns 409 instead of spawning duplicate gh scans
            github_scanner._SCAN_LOCK.acquire()
            try:
                req_busy = urllib.request.Request(
                    f"{base}/api/github/refresh",
                    data=b"{}",
                    method="POST",
                    headers={"Origin": f"http://127.0.0.1:{port}"},
                )
                with self.assertRaises(urllib.error.HTTPError) as ctx_busy:
                    urllib.request.urlopen(req_busy, timeout=5)
                self.assertEqual(ctx_busy.exception.code, 409)
            finally:
                github_scanner._SCAN_LOCK.release()
        finally:
            api_srv.shutdown()
            api_srv.server_close()

    def test_local_sync_reconciles_deleted_and_dirty_repos(self) -> None:
        self.assertEqual(
            github_local_sync.normalize_github_slug("git@github.com:Mostakim2005/Database-Manager.git"),
            "mostakim2005/database-manager",
        )
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo_a = root / "active-repo"
            repo_a.mkdir()
            env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
            subprocess.run(["git", "init"], cwd=repo_a, check=True, capture_output=True, env=env)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_a, check=True, capture_output=True, env=env)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_a, check=True, capture_output=True, env=env)
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/Mostakim2005/active-repo.git"], cwd=repo_a, check=True, capture_output=True, env=env)
            (repo_a / "README.md").write_text("hi\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo_a, check=True, capture_output=True, env=env)
            subprocess.run(["git", "commit", "-m", "init"], cwd=repo_a, check=True, capture_output=True, env=env)
            # Dirty untracked file
            (repo_a / "notes.txt").write_text("dirty\n", encoding="utf-8")

            repo_b = root / "deleted-web-repo"
            repo_b.mkdir()
            subprocess.run(["git", "init"], cwd=repo_b, check=True, capture_output=True, env=env)
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/Mostakim2005/deleted-web-repo.git"], cwd=repo_b, check=True, capture_output=True, env=env)

            web_repos = [
                {"name": "active-repo", "full_name": "Mostakim2005/active-repo", "is_fork": False, "is_private": False, "pushed_at": "2026-11-25T10:00:00Z"},
                {"name": "web-only-repo", "full_name": "Mostakim2005/web-only-repo", "is_fork": False, "is_private": False, "pushed_at": "2026-11-25T10:00:00Z"},
            ]
            prev_state = {
                "web_slugs": ["mostakim2005/active-repo", "mostakim2005/deleted-web-repo", "mostakim2005/web-only-repo"],
                "local_slugs": ["mostakim2005/active-repo", "mostakim2005/deleted-web-repo", "mostakim2005/web-only-repo"],
            }
            report = github_local_sync.reconcile_local_with_web(web_repos, previous_state=prev_state, roots=[root])
            c = report["counts"]
            self.assertEqual(c["local_total"], 2)
            self.assertEqual(c["dirty_or_ahead"], 1)
            self.assertEqual(c["local_only"], 1)
            self.assertEqual(c["web_only"], 1)
            self.assertEqual(report["deleted_on_web_since_last"], ["mostakim2005/deleted-web-repo"])
            self.assertEqual(report["deleted_locally_since_last"], ["mostakim2005/web-only-repo"])
            self.assertTrue(report["local_only"][0]["deleted_on_web"])
            self.assertTrue(report["web_only"][0]["deleted_locally"])

    def test_background_refresh_progress_and_single_repo_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            live = td_path / "live_cache.json"
            pub = td_path / "repos_public.json"
            pub.write_text("[]", encoding="utf-8")

            fake_raw = [{"name": "r1", "full_name": "Mostakim2005/r1", "owner": {"login": "Mostakim2005"}, "default_branch": "main", "fork": False, "private": False}]
            fake_detail = {"name": "r1", "full_name": "Mostakim2005/r1", "is_fork": False, "is_private": False, "default_branch": "main", "pushed_at": "2026-11-25T10:00:00Z", "recent_commits": [], "unbuilt_commits_count": 0, "unreleased_commits_count": 0}

            with mock.patch("github.scanner._fetch_all_owner_repos", return_value=fake_raw), \
                 mock.patch("github.scanner._scan_single_repo_details", return_value=fake_detail), \
                 mock.patch("github.scanner._update_sync_state_from_scan", return_value={"last_refreshed_at": "2026-11-25T12:00:00Z", "local_sync": {"counts": {"synced": 1}}}):
                job = github_scanner.start_background_refresh(include_local=False, live_cache_path=live, public_cache_path=pub)
                self.assertTrue(job["job_id"])
                deadline = time.monotonic() + 5.0
                while time.monotonic() < deadline:
                    st = github_scanner.get_refresh_status()
                    if not st["running"]:
                        break
                    time.sleep(0.05)
                final_st = github_scanner.get_refresh_status()
                self.assertEqual(final_st["stage"], "completed")
                self.assertEqual(final_st["percent"], 100.0)
                self.assertTrue(live.exists())

            with mock.patch("github.scanner.run_gh_api", return_value=fake_raw[0]), \
                 mock.patch("github.scanner._scan_single_repo_details", return_value=fake_detail):
                res = github_scanner.refresh_single_repository("Mostakim2005/r1", live_cache_path=live, public_cache_path=pub, sync_state_path=td_path / "sync.json")
                self.assertEqual(res["status"], "ok")
                self.assertEqual(res["repository"]["full_name"], "Mostakim2005/r1")

    def test_cliproxy_discovery_and_agent_endpoints(self) -> None:
        class MockProxyHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/v1/models":
                    body = json.dumps({"data": [{"id": "gemini-2.5-flash"}, {"id": "claude-sonnet-5.5"}]}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(404)
                self.end_headers()

            def do_POST(self):
                if self.path == "/v1/chat/completions":
                    length = int(self.headers.get("Content-Length") or "0")
                    self.rfile.read(length)
                    body = json.dumps({"model": "gemini-2.5-flash", "choices": [{"message": {"content": "# Executive GitHub Summary\n- All systems checked."}}]}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(404)
                self.end_headers()

            def log_message(self, *args):
                pass

        proxy_srv = http.server.HTTPServer(("127.0.0.1", 0), MockProxyHandler)
        proxy_port = proxy_srv.server_address[1]
        threading.Thread(target=proxy_srv.serve_forever, daemon=True).start()

        api_srv = server.ReusableThreadingHTTPServer(("127.0.0.1", 0), server.DatabaseHandler)
        api_port = api_srv.server_address[1]
        threading.Thread(target=api_srv.serve_forever, daemon=True).start()

        try:
            with tempfile.TemporaryDirectory() as td:
                auth_dir = Path(td)
                (auth_dir / "antigravity-alice@gmail.com.json").write_text("{}", encoding="utf-8")
                (auth_dir / "antigravity-bob@gmail.com.json").write_text("{}", encoding="utf-8")

                with mock.patch.dict(os.environ, {
                    "CLIPROXY_URL": f"http://127.0.0.1:{proxy_port}",
                    "CLIPROXY_OPENAI_BASE": f"http://127.0.0.1:{proxy_port}/v1",
                    "CLIPROXY_AUTH_DIR": str(auth_dir),
                }):
                    st = agent_proxy.get_proxy_status()
                    self.assertTrue(st["online"])
                    self.assertEqual(st["google_account_count"], 2)
                    self.assertIn("gemini-2.5-flash", st["models"])

                    base = f"http://127.0.0.1:{api_port}"
                    with urllib.request.urlopen(f"{base}/api/agent/status", timeout=5) as resp:
                        api_st = json.loads(resp.read().decode("utf-8"))
                        self.assertTrue(api_st["online"])
                        self.assertEqual(api_st["google_account_count"], 2)

                    req_ask = urllib.request.Request(
                        f"{base}/api/agent/ask",
                        data=json.dumps({"question": "What is my PC baseline?"}).encode("utf-8"),
                        method="POST",
                        headers={"Origin": base, "Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(req_ask, timeout=5) as resp:
                        ask_res = json.loads(resp.read().decode("utf-8"))
                        self.assertTrue(ask_res["ok"])
                        self.assertIn("Executive GitHub Summary", ask_res["content"])

                    # Untrusted origin blocked on agent POST
                    req_bad = urllib.request.Request(
                        f"{base}/api/agent/ask",
                        data=json.dumps({"question": "test"}).encode("utf-8"),
                        method="POST",
                        headers={"Origin": "https://evil.example", "Content-Type": "application/json"},
                    )
                    with self.assertRaises(urllib.error.HTTPError) as ctx:
                        urllib.request.urlopen(req_bad, timeout=5)
                    self.assertEqual(ctx.exception.code, 403)
        finally:
            proxy_srv.shutdown()
            proxy_srv.server_close()
            api_srv.shutdown()
            api_srv.server_close()


if __name__ == "__main__":
    unittest.main()
