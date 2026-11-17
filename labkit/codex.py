"""Shared Codex configuration for the sandbox probe and exercise execution."""

from __future__ import annotations

import sys


def windows_sandbox(cfg: dict) -> str | None:
    mode = cfg.get("windows_sandbox")
    if mode not in (None, "elevated", "unelevated"):
        raise ValueError("windows_sandbox는 null, elevated, unelevated 중 하나여야 합니다.")
    return mode if sys.platform == "win32" else None


def command_prefix(cfg: dict) -> list[str]:
    command = list(cfg["codex_command"])
    if cfg.get("profile"):
        command += ["--profile", cfg["profile"]]
    mode = windows_sandbox(cfg)
    if mode:
        command += ["-c", f'windows.sandbox="{mode}"']
    return command
