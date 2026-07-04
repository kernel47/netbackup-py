"""SSH transport for safe NetBackup CLI collection."""

from __future__ import annotations

import shlex
import subprocess

from nbu.config import NetBackupConfig
from nbu.exceptions import SshError, TimeoutError


class SshTransport:
    """Runs approved read-only NetBackup commands over SSH."""

    SAFE_COMMANDS = {
        "bpdbjobs",
        "bppllist",
        "bpimagelist",
        "bpstulist",
        "nbemmcmd",
        "nbstl",
        "nbdeployutil",
        "nbcertcmd",
        "vmquery",
        "nbdiscover",
        "bpps",
    }

    def __init__(self, config: NetBackupConfig) -> None:
        self.config = config

    def run(self, command: str, *args: str) -> str:
        if command not in self.SAFE_COMMANDS:
            raise SshError(f"Command {command!r} is not in the safe NetBackup command allow-list")
        ssh_target = self.config.master
        if self.config.username:
            ssh_target = f"{self.config.username}@{ssh_target}"
        ssh_args = ["ssh", "-p", str(self.config.ssh_port)]
        if self.config.ssh_key_filename:
            ssh_args.extend(["-i", self.config.ssh_key_filename])
        remote = " ".join(shlex.quote(part) for part in (command, *args))
        try:
            completed = subprocess.run(
                [*ssh_args, ssh_target, remote],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"SSH command timed out: {command}") from exc
        if completed.returncode != 0:
            raise SshError(completed.stderr.strip() or f"SSH command failed: {command}")
        return completed.stdout

