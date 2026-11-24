#!/usr/bin/env python3
"""Unit & integration tests for the GitHub Repositories domain."""

from __future__ import annotations

import datetime
import json
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))

import catalog_classifier  # noqa: E402
import server  # noqa: E402
from github import cli as github_cli  # noqa: E402
from github import exporter as github_exporter  # noqa: E402
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


if __name__ == "__main__":
    unittest.main()
