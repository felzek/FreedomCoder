from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from freedomcoder.claude_code import (
    claude_binary,
    claude_version,
    ensure_model_available,
    format_shell_snippet,
    launch as launch_claude_code,
)
from freedomcoder.config import load_project_instructions, load_settings
from freedomcoder.errors import FreedomCoderError, RuntimeIntegrationError
from freedomcoder.hf import download_profile_quant
from freedomcoder.launcher import (
    default_target_dir,
    install_launcher,
    launcher_name,
    path_contains,
    path_hint,
)
from freedomcoder.ollama import (
    chat,
    create_model,
    ollama_model_names,
    ollama_tags,
    render_modelfile,
)
from freedomcoder.models import ModelProfile, Settings
from freedomcoder.profiles import format_profile, list_profiles, load_profile
from freedomcoder.prompting import build_task_prompt, collect_file_contexts

KNOWN_COMMANDS = frozenset(
    {"doctor", "install-launcher", "profiles", "pull", "ollama", "task", "claude-code"}
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="freedomcoder",
        description="Local-first coding-agent tooling centered on the Heretic 27B GGUF lineage.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Inspect local configuration and runtime availability.")
    install_parser = subparsers.add_parser(
        "install-launcher",
        help="Install a cross-platform one-word launcher into your user bin directory.",
    )
    install_parser.add_argument(
        "--target-dir",
        type=Path,
        default=None,
        help="Override the launcher install directory.",
    )
    install_parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the target location and PATH hint without writing anything.",
    )

    profiles_parser = subparsers.add_parser("profiles", help="Inspect built-in model profiles.")
    profiles_subparsers = profiles_parser.add_subparsers(dest="profiles_command", required=True)
    profiles_subparsers.add_parser("list", help="List available profiles.")
    show_parser = profiles_subparsers.add_parser("show", help="Show a single profile.")
    show_parser.add_argument("profile", help="Profile id, such as 'flagship' or 'constrained'.")

    pull_parser = subparsers.add_parser("pull", help="Download a GGUF for a built-in profile.")
    pull_parser.add_argument("--profile", default=None, help="Profile id to download.")
    pull_parser.add_argument("--quant", default=None, help="Explicit quant override.")
    pull_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".freedomcoder/models"),
        help="Directory where the GGUF should be downloaded.",
    )

    ollama_parser = subparsers.add_parser("ollama", help="Create an Ollama model from a GGUF.")
    ollama_subparsers = ollama_parser.add_subparsers(dest="ollama_command", required=True)
    create_parser = ollama_subparsers.add_parser("create", help="Create a local Ollama model.")
    create_parser.add_argument("--profile", default=None, help="Profile id to use.")
    source_group = create_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--gguf", type=Path, help="Path to the GGUF file.")
    source_group.add_argument(
        "--from-model",
        default=None,
        help="Existing local Ollama model to wrap with FreedomCoder's template.",
    )
    create_parser.add_argument("--name", default=None, help="Ollama model name override.")
    create_parser.add_argument(
        "--context-window",
        type=int,
        default=16_384,
        help="Default Ollama context window for the created model.",
    )
    create_parser.add_argument(
        "--modelfile-out",
        type=Path,
        default=None,
        help="Persist the generated Modelfile at this path.",
    )
    create_parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the generated Modelfile and exit without running ollama create.",
    )

    task_parser = subparsers.add_parser(
        "task", help="Run a focused local coding task through an Ollama model."
    )
    task_parser.add_argument("task", help="Task prompt for the local coding workflow.")
    task_parser.add_argument("--profile", default=None, help="Profile id for generation defaults.")
    task_parser.add_argument("--model", default=None, help="Ollama model name to use.")
    task_parser.add_argument(
        "--files",
        nargs="+",
        type=Path,
        required=True,
        help="Specific files to include in context.",
    )
    task_parser.add_argument(
        "--mode",
        choices=["patch", "plan", "review"],
        default="patch",
        help="Response framing for the task.",
    )
    task_parser.add_argument(
        "--context-window",
        type=int,
        default=16_384,
        help="Ollama num_ctx override for this task.",
    )
    task_parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="Print the constructed prompt instead of calling Ollama.",
    )

    claude_parser = subparsers.add_parser(
        "claude-code",
        help="Launch or inspect Claude Code using Ollama as the backend.",
    )
    claude_subparsers = claude_parser.add_subparsers(dest="claude_command", required=True)

    env_parser = claude_subparsers.add_parser(
        "env",
        help="Print shell commands for running Claude Code against the local Ollama model.",
    )
    env_parser.add_argument("--profile", default=None, help="Profile id for the default model name.")
    env_parser.add_argument("--model", default=None, help="Ollama model name override.")
    env_parser.add_argument(
        "--shell",
        choices=["powershell", "cmd", "bash"],
        default="powershell",
        help="Shell syntax to print.",
    )
    env_parser.add_argument(
        "claude_args",
        nargs=argparse.REMAINDER,
        help="Extra Claude Code arguments to append after `--`.",
    )

    launch_parser = claude_subparsers.add_parser(
        "launch",
        help="Launch Claude Code against the local Ollama model.",
    )
    launch_parser.add_argument("--profile", default=None, help="Profile id for the default model name.")
    launch_parser.add_argument("--model", default=None, help="Ollama model name override.")
    launch_parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the environment snippet instead of launching Claude Code.",
    )
    launch_parser.add_argument(
        "--shell",
        choices=["powershell", "cmd", "bash"],
        default="powershell",
        help="Shell syntax used for --print-only output.",
    )
    launch_parser.add_argument(
        "--skip-model-check",
        action="store_true",
        help="Skip checking whether the target model exists in Ollama before launch.",
    )
    launch_parser.add_argument(
        "claude_args",
        nargs=argparse.REMAINDER,
        help="Extra Claude Code arguments to append after `--`.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(_prepare_args(raw_args))
    try:
        return dispatch(args)
    except FreedomCoderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def dispatch(args: argparse.Namespace) -> int:
    settings = load_settings(start=Path.cwd())
    if args.command == "doctor":
        _run_doctor(settings)
        return 0
    if args.command == "install-launcher":
        target_dir = args.target_dir
        if args.print_only:
            resolved_target = (target_dir or default_target_dir()).resolve()
            print(resolved_target / launcher_name())
            if not path_contains(resolved_target):
                print(path_hint(directory=resolved_target))
            return 0
        installed = install_launcher(target_dir=target_dir)
        print(installed)
        if not path_contains(installed.parent):
            print(path_hint(directory=installed.parent))
        return 0
    if args.command == "profiles":
        if args.profiles_command == "list":
            for profile in list_profiles():
                print(
                    f"{profile.id}: {profile.label} | recommended quant={profile.recommended_quant} "
                    f"| model id={profile.model_id}"
                )
            return 0
        print(format_profile(load_profile(args.profile)))
        return 0
    if args.command == "pull":
        profile = load_profile(args.profile or settings.default_profile)
        path = download_profile_quant(
            profile,
            quant=args.quant,
            output_dir=args.output_dir,
        )
        print(path)
        return 0
    if args.command == "ollama":
        if args.ollama_command == "create":
            profile = load_profile(args.profile or settings.default_profile)
            model_name = args.name or profile.default_model_name
            if args.gguf is not None and not args.gguf.is_file():
                raise RuntimeIntegrationError(f"GGUF file not found: {args.gguf}")
            source_ref = (
                args.gguf.resolve().as_posix()
                if args.gguf is not None
                else str(args.from_model)
            )
            modelfile_text = render_modelfile(
                profile,
                source_ref=source_ref,
                context_window=args.context_window,
            )
            if args.print_only:
                print(modelfile_text)
                return 0
            created_from = create_model(
                name=model_name,
                modelfile_text=modelfile_text,
                modelfile_out=args.modelfile_out,
            )
            print(f"Created Ollama model '{model_name}' using {created_from}")
            return 0
    if args.command == "task":
        profile = load_profile(args.profile or settings.default_profile)
        model_name = args.model or settings.default_model or profile.default_model_name
        _, agents_text = load_project_instructions(settings, start=Path.cwd())
        contexts = collect_file_contexts(
            args.files,
            max_file_bytes=settings.max_file_bytes,
            max_context_chars=settings.max_context_chars,
        )
        prompt = build_task_prompt(
            task=args.task,
            mode=args.mode,
            agents_text=agents_text,
            file_contexts=contexts,
        )
        if args.print_prompt:
            print(prompt)
            return 0
        response = chat(
            host=settings.ollama_host,
            model=model_name,
            prompt=prompt,
            options=profile.generation_defaults.ollama_options(num_ctx=args.context_window),
        )
        print(response)
        return 0
    if args.command == "claude-code":
        profile = load_profile(args.profile or settings.default_profile)
        model_name = _resolve_claude_model_name(
            settings=settings,
            profile=profile,
            requested_model=args.model,
        )
        extra_args = _normalize_passthrough_args(args.claude_args)
        if args.claude_command == "env":
            print(
                format_shell_snippet(
                    shell=args.shell,
                    host=settings.ollama_host,
                    model=model_name,
                    extra_args=extra_args,
                )
            )
            return 0
        if args.claude_command == "launch":
            claude_binary()
            if not args.skip_model_check:
                ensure_model_available(host=settings.ollama_host, model=model_name)
            if args.print_only:
                print(
                    format_shell_snippet(
                        shell=args.shell,
                        host=settings.ollama_host,
                        model=model_name,
                        extra_args=extra_args,
                    )
                )
                return 0
            return launch_claude_code(
                host=settings.ollama_host,
                model=model_name,
                extra_args=extra_args,
            )
    return 1


def _run_doctor(settings: Settings) -> None:
    instructions_path, _ = load_project_instructions(settings, start=Path.cwd())
    config_path = settings.config_path.as_posix() if settings.config_path else "not found"
    ollama_binary = shutil.which("ollama") or "not found"
    ollama_version = _command_output(["ollama", "--version"]) if shutil.which("ollama") else "unavailable"
    ollama_status = "reachable"
    try:
        ollama_tags(settings.ollama_host)
    except FreedomCoderError:
        ollama_status = "not reachable"
    print(f"config: {config_path}")
    print(f"project instructions: {instructions_path.as_posix() if instructions_path else 'not found'}")
    print(f"default profile: {settings.default_profile}")
    print(f"default model: {settings.default_model or 'not set'}")
    print(f"ollama host: {settings.ollama_host}")
    print(f"ollama binary: {ollama_binary}")
    print(f"ollama version: {ollama_version}")
    print(f"ollama status: {ollama_status}")
    profile = load_profile(settings.default_profile)
    print(
        "default claude model: "
        f"{_resolve_claude_model_name(settings=settings, profile=profile, requested_model=None)}"
    )
    try:
        print(f"claude binary: {claude_binary()}")
        print(f"claude version: {claude_version()}")
    except FreedomCoderError:
        print("claude binary: not found")
        print("claude version: unavailable")


def _command_output(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return (completed.stdout or completed.stderr).strip() or "unknown"


def _normalize_passthrough_args(values: list[str]) -> list[str]:
    if values and values[0] == "--":
        return values[1:]
    return values


def _prepare_args(raw_args: list[str]) -> list[str]:
    if not raw_args:
        return ["claude-code", "launch"]
    first = raw_args[0]
    if first in {"-h", "--help", "help"}:
        return raw_args
    if first in KNOWN_COMMANDS:
        return raw_args
    return ["claude-code", "launch", *raw_args]


def _resolve_claude_model_name(
    *,
    settings: Settings,
    profile: ModelProfile,
    requested_model: str | None,
) -> str:
    if requested_model:
        return requested_model
    preferred = settings.default_model or profile.default_model_name
    try:
        installed = {name.removesuffix(":latest") for name in ollama_model_names(settings.ollama_host)}
    except FreedomCoderError:
        return preferred
    if preferred in installed:
        return preferred
    freedomcoder_models = sorted(name for name in installed if name.startswith("freedomcoder-"))
    if profile.default_model_name in freedomcoder_models:
        return profile.default_model_name
    tools_models = [name for name in freedomcoder_models if name.endswith("-tools")]
    if tools_models:
        return tools_models[0]
    if freedomcoder_models:
        return freedomcoder_models[0]
    return preferred
