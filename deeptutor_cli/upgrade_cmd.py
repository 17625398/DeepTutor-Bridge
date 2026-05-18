"""
CLI Upgrade Command
===================

Manage DeepTutor upgrades, rollbacks, and backups.
"""

from __future__ import annotations

from pathlib import Path
import sys

from rich.console import Console
import typer

console = Console()


def register(app: typer.Typer) -> None:
    @app.command("run")
    def upgrade_run(
        mode: str = typer.Option("auto", "--mode", help="Upgrade mode: auto, git, or pip"),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
        backup: bool = typer.Option(False, "--backup", help="Create backup before upgrade"),
        healthcheck: bool = typer.Option(False, "--healthcheck", help="Run health check after upgrade"),
        base_url: str = typer.Option("http://127.0.0.1:8001", "--base-url", help="API base URL"),
    ) -> None:
        """Upgrade DeepTutor to the latest version."""
        from deeptutor_upgrade import main as upgrade_main

        args = ["upgrade", "--mode", mode]
        if yes:
            args.append("--yes")
        if backup:
            args.append("--backup")
        if healthcheck:
            args.append("--healthcheck")
        args.extend(["--base-url", base_url])

        code = upgrade_main(args)
        if code != 0:
            raise typer.Exit(code=code)

    @app.command("rollback")
    def upgrade_rollback(
        backup_file: Path = typer.Argument(..., help="Path to backup file"),
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    ) -> None:
        """Rollback to a previous backup."""
        from deeptutor_upgrade import main as upgrade_main

        code = upgrade_main(["rollback", "--backup-file", str(backup_file)] + (["--yes"] if yes else []))
        if code != 0:
            raise typer.Exit(code=code)

    @app.command("backup")
    def upgrade_backup(
        include_kb: bool = typer.Option(False, "--include-kb", help="Include knowledge bases"),
        include_logs: bool = typer.Option(False, "--include-logs", help="Include logs"),
        include_config: bool = typer.Option(True, "--include-config/--no-config", help="Include config files"),
        include_plugins: bool = typer.Option(True, "--include-plugins/--no-plugins", help="Include plugins"),
        include_modified: bool = typer.Option(True, "--include-modified/--no-modified", help="Include modified files"),
        out_dir: Path = typer.Option(Path.cwd() / "deeptutor_backups", "--out-dir", help="Output directory"),
    ) -> None:
        """Create a backup of DeepTutor data."""
        from deeptutor_upgrade import main as upgrade_main

        args = ["backup", "--out-dir", str(out_dir)]
        if include_kb:
            args.append("--include-kb")
        if include_logs:
            args.append("--include-logs")
        if include_config:
            args.append("--include-config")
        else:
            args.append("--no-config")
        if include_plugins:
            args.append("--include-plugins")
        else:
            args.append("--no-plugins")
        if include_modified:
            args.append("--include-modified")
        else:
            args.append("--no-modified")

        code = upgrade_main(args)
        if code != 0:
            raise typer.Exit(code=code)

    @app.command("list")
    def upgrade_list_backups(
        out_dir: Path = typer.Option(Path.cwd() / "deeptutor_backups", "--out-dir", help="Backup directory"),
    ) -> None:
        """List available backups."""
        from deeptutor_upgrade import main as upgrade_main

        code = upgrade_main(["list-backups", "--out-dir", str(out_dir)])
        if code != 0:
            raise typer.Exit(code=code)

    @app.command("history")
    def upgrade_history() -> None:
        """Show upgrade history."""
        from deeptutor_upgrade import main as upgrade_main

        code = upgrade_main(["history"])
        if code != 0:
            raise typer.Exit(code=code)

    @app.command("healthcheck")
    def upgrade_healthcheck(
        base_url: str = typer.Option("http://127.0.0.1:8001", "--base-url", help="API base URL"),
    ) -> None:
        """Check if DeepTutor API is healthy."""
        from deeptutor_upgrade import main as upgrade_main

        code = upgrade_main(["healthcheck", "--base-url", base_url])
        if code != 0:
            raise typer.Exit(code=code)
