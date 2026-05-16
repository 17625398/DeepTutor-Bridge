from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile


def _now_stamp() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        check=check,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _is_git_checkout(repo: Path) -> bool:
    try:
        result = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo, check=False)
    except OSError:
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git(cmd: list[str], repo: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run(["git", *cmd], cwd=repo, check=check)


def _git_branch(repo: Path) -> str:
    result = _git(["branch", "--show-current"], repo, check=False)
    branch = result.stdout.strip()
    if not branch:
        raise RuntimeError("Detached HEAD; please switch to a branch before upgrading.")
    return branch


def _git_short(repo: Path, ref: str) -> tuple[str, str]:
    sha = _git(["rev-parse", "--short", ref], repo).stdout.strip()
    subject = _git(["log", "-1", "--format=%s", ref], repo).stdout.strip()
    return sha, subject


def _git_remote_ref(repo: Path, remote: str, branch: str) -> str:
    return f"refs/remotes/{remote}/{branch}"


def _git_pick_remote(repo: Path) -> str:
    remotes = _git(["remote"], repo, check=False).stdout.splitlines()
    remotes = [r.strip() for r in remotes if r.strip()]
    if not remotes:
        raise RuntimeError("No git remote configured for this checkout.")
    return "origin" if "origin" in remotes else remotes[0]


def _git_gap(repo: Path, remote_ref: str) -> tuple[int, int, str]:
    counts = _git(["rev-list", "--left-right", "--count", f"HEAD...{remote_ref}"], repo).stdout.strip()
    ahead_str, behind_str = counts.split()
    ahead = int(ahead_str)
    behind = int(behind_str)
    diff_stat = ""
    if behind:
        diff_stat = _git(["diff", "--stat", "--compact-summary", f"HEAD..{remote_ref}"], repo).stdout.strip()
    return ahead, behind, diff_stat


def dry_run_git(repo: Path, *, remote: str | None = None) -> int:
    if not _is_git_checkout(repo):
        print("Not a git checkout:", repo)
        return 2

    branch = _git_branch(repo)
    remote_name = remote or _git_pick_remote(repo)

    fetched = _git(["fetch", "--prune", remote_name], repo, check=False)
    if fetched.returncode != 0:
        print(f"git fetch failed for remote '{remote_name}'")
        if fetched.stderr.strip():
            print(fetched.stderr.strip())
        return 2
    remote_ref = _git_remote_ref(repo, remote_name, branch)

    verify = _git(["rev-parse", "--verify", "--quiet", f"{remote_ref}^{{commit}}"], repo, check=False)
    if verify.returncode != 0:
        print(f"Remote branch not found after fetch: {remote_name}/{branch}")
        return 2

    local_sha, local_subject = _git_short(repo, "HEAD")
    remote_sha, remote_subject = _git_short(repo, remote_ref)
    ahead, behind, diff_stat = _git_gap(repo, remote_ref)

    print("Repo:", repo)
    print("Branch:", branch)
    print("Local :", f"{local_sha} {local_subject}")
    print("Remote:", f"{remote_sha} {remote_subject}")
    print("Ahead/Behind:", f"{ahead}/{behind}")
    if diff_stat:
        print()
        print(diff_stat)

    if behind == 0:
        return 0
    if ahead > 0:
        print()
        print("Upgrade blocked: local branch has commits not on remote (not fast-forwardable).")
        return 3
    return 0


def _default_repo() -> Path:
    return Path(__file__).resolve().parent.parent


def _default_data_dir(repo: Path) -> Path:
    return repo / "data"


def _iter_backup_entries(data_dir: Path, *, include_kb: bool, include_logs: bool) -> list[Path]:
    entries: list[Path] = []
    settings_dir = data_dir / "user" / "settings"
    if settings_dir.exists():
        entries.append(settings_dir)

    chat_history = data_dir / "user" / "chat_history.db"
    if chat_history.exists():
        entries.append(chat_history)

    if include_kb:
        kb_dir = data_dir / "knowledge_bases"
        if kb_dir.exists():
            entries.append(kb_dir)

    if include_logs:
        logs_dir = data_dir / "user" / "logs"
        if logs_dir.exists():
            entries.append(logs_dir)

    return entries


def _zip_add_path(zf: zipfile.ZipFile, base_dir: Path, entry: Path) -> None:
    if entry.is_dir():
        for file in entry.rglob("*"):
            if file.is_file():
                arcname = str(file.relative_to(base_dir))
                zf.write(file, arcname=arcname)
        return
    if entry.is_file():
        arcname = str(entry.relative_to(base_dir))
        zf.write(entry, arcname=arcname)


def backup_data(
    data_dir: Path,
    *,
    out_dir: Path,
    include_kb: bool,
    include_logs: bool,
) -> Path:
    base_dir = data_dir.resolve()
    if not base_dir.exists():
        raise RuntimeError(f"data directory not found: {base_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = (out_dir / f"deeptutor-backup-{_now_stamp()}.zip").resolve()

    entries = _iter_backup_entries(base_dir, include_kb=include_kb, include_logs=include_logs)
    if not entries:
        raise RuntimeError(f"No backup targets found under: {base_dir}")

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for entry in entries:
            _zip_add_path(zf, base_dir, entry)

    return archive_path


def http_get_json(url: str, *, timeout_s: float = 5.0, headers: dict[str, str] | None = None) -> dict:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return json.loads(body)


def healthcheck(base_url: str, *, auth_token: str | None = None) -> int:
    base_url = base_url.rstrip("/")
    root_url = f"{base_url}/"
    try:
        root = http_get_json(root_url, timeout_s=5.0)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        print("Health check failed:", root_url)
        print(str(exc))
        return 2

    if not isinstance(root, dict) or "message" not in root:
        print("Health check returned unexpected response:", root_url)
        print(json.dumps(root, ensure_ascii=False) if isinstance(root, (dict, list)) else str(root))
        return 2

    status_url = f"{base_url}/api/v1/system/status"
    if auth_token:
        try:
            status = http_get_json(
                status_url,
                timeout_s=8.0,
                headers={"Authorization": f"Bearer {auth_token}"},
            )
            print("System status:", json.dumps(status, ensure_ascii=False))
        except Exception:
            print("System status check failed (non-fatal):", status_url)

    print("OK:", root.get("message"))
    return 0


def upgrade_git(repo: Path, *, assume_yes: bool, remote: str | None = None) -> int:
    if not _is_git_checkout(repo):
        raise RuntimeError(f"Not a git checkout: {repo}")

    branch = _git_branch(repo)
    remote_name = remote or _git_pick_remote(repo)

    dirty = _git(["status", "--porcelain"], repo, check=False).stdout.strip()
    if dirty:
        raise RuntimeError("Working tree is dirty; commit/stash changes before upgrading.")

    fetched = _git(["fetch", "--prune", remote_name], repo, check=False)
    if fetched.returncode != 0:
        raise RuntimeError(fetched.stderr.strip() or "git fetch failed")

    remote_ref = _git_remote_ref(repo, remote_name, branch)
    verify = _git(["rev-parse", "--verify", "--quiet", f"{remote_ref}^{{commit}}"], repo, check=False)
    if verify.returncode != 0:
        raise RuntimeError(f"Remote branch not found: {remote_name}/{branch}")

    ahead, behind, _ = _git_gap(repo, remote_ref)
    if behind == 0:
        print("Already up to date.")
        return 0
    if ahead > 0:
        raise RuntimeError("Local branch has commits not on remote; upgrade requires fast-forward.")

    if not assume_yes:
        raise RuntimeError("Interactive confirm is not supported; pass --yes to proceed.")

    merge = _git(["merge", "--ff-only", remote_ref], repo, check=False)
    sys.stdout.write(merge.stdout)
    sys.stderr.write(merge.stderr)
    return merge.returncode


def _installed_version(dist_name: str) -> str | None:
    try:
        from importlib.metadata import version
    except Exception:
        return None
    try:
        return version(dist_name)
    except Exception:
        return None


def upgrade_pip(pip_spec: str) -> int:
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", pip_spec]
    completed = _run(cmd, check=False)
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="deeptutor-upgrade")
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", type=Path, default=_default_repo())

    cmd_dry = sub.add_parser("dry-run", parents=[common])
    cmd_dry.add_argument("--mode", choices=["auto", "git", "pip"], default="auto")
    cmd_dry.add_argument("--remote", default=None)
    cmd_dry.add_argument("--pip-spec", default="deeptutor[server]")

    cmd_backup = sub.add_parser("backup", parents=[common])
    cmd_backup.add_argument("--data-dir", type=Path, default=None)
    cmd_backup.add_argument("--out-dir", type=Path, default=Path.cwd() / "deeptutor_backups")
    cmd_backup.add_argument("--include-kb", action="store_true")
    cmd_backup.add_argument("--include-logs", action="store_true")

    cmd_health = sub.add_parser("healthcheck")
    cmd_health.add_argument("--base-url", default=os.environ.get("DEEPTUTOR_BASE_URL", "http://127.0.0.1:8001"))
    cmd_health.add_argument("--auth-token", default=os.environ.get("DEEPTUTOR_AUTH_TOKEN"))

    cmd_upgrade = sub.add_parser("upgrade", parents=[common])
    cmd_upgrade.add_argument("--mode", choices=["auto", "git", "pip"], default="auto")
    cmd_upgrade.add_argument("--yes", "-y", action="store_true")
    cmd_upgrade.add_argument("--remote", default=None)
    cmd_upgrade.add_argument("--pip-spec", default="deeptutor[server]")
    cmd_upgrade.add_argument("--backup", action="store_true")
    cmd_upgrade.add_argument("--data-dir", type=Path, default=None)
    cmd_upgrade.add_argument("--backup-out-dir", type=Path, default=Path.cwd() / "deeptutor_backups")
    cmd_upgrade.add_argument("--include-kb", action="store_true")
    cmd_upgrade.add_argument("--include-logs", action="store_true")
    cmd_upgrade.add_argument("--healthcheck", action="store_true")
    cmd_upgrade.add_argument("--base-url", default=os.environ.get("DEEPTUTOR_BASE_URL", "http://127.0.0.1:8001"))
    cmd_upgrade.add_argument("--auth-token", default=os.environ.get("DEEPTUTOR_AUTH_TOKEN"))

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(getattr(exc, "code", 2) or 2)

    try:
        if args.command == "healthcheck":
            return healthcheck(args.base_url, auth_token=args.auth_token)

        repo: Path = args.repo.resolve()

        if args.command == "backup":
            data_dir = (args.data_dir or _default_data_dir(repo)).resolve()
            archive = backup_data(
                data_dir,
                out_dir=args.out_dir.resolve(),
                include_kb=args.include_kb,
                include_logs=args.include_logs,
            )
            print(str(archive))
            return 0

        if args.command == "dry-run":
            mode = args.mode
            if mode == "auto":
                mode = "git" if _is_git_checkout(repo) else "pip"

            if mode == "git":
                return dry_run_git(repo, remote=args.remote)

            current = _installed_version("deeptutor")
            print("pip spec:", args.pip_spec)
            print("installed:", current or "not installed")
            return 0

        if args.command == "upgrade":
            mode = args.mode
            if mode == "auto":
                mode = "git" if _is_git_checkout(repo) else "pip"

            if args.backup:
                data_dir = (args.data_dir or _default_data_dir(repo)).resolve()
                archive = backup_data(
                    data_dir,
                    out_dir=args.backup_out_dir.resolve(),
                    include_kb=args.include_kb,
                    include_logs=args.include_logs,
                )
                print("Backup created:", str(archive))

            if mode == "git":
                preflight = dry_run_git(repo, remote=args.remote)
                if preflight not in (0,):
                    return preflight
                code = upgrade_git(repo, assume_yes=args.yes, remote=args.remote)
            else:
                before = _installed_version("deeptutor")
                print("Installed before:", before or "not installed")
                code = upgrade_pip(args.pip_spec)
                after = _installed_version("deeptutor")
                print("Installed after :", after or "not installed")

            if code != 0:
                return code

            if args.healthcheck:
                hc = healthcheck(args.base_url, auth_token=args.auth_token)
                if hc != 0:
                    return hc

            return 0

        return 2
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        message = str(exc).strip()
        if not message and hasattr(exc, "stderr"):
            message = str(getattr(exc, "stderr") or "").strip()
        print(message or "Upgrade tool failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
