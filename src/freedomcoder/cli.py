from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from freedomcoder.config import load_project_instructions, load_settings
from freedomcoder.errors import FreedomCoderError, RuntimeIntegrationError
from freedomcoder.hf import download_profile_quant
from freedomcoder.ollama import chat, create_model, ollama_tags, render_modelfile
from freedomcoder.models import Settings
from freedomcoder.profiles import format_profile, list_profiles, load_profile
from freedomcoder.prompting import build_task_prompt, collect_file_contexts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="freedomcoder",
        description="Local-first coding-agent tooling centered on the Heretic 27B GGUF lineage.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Inspect local configuration and runtime availability.")

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
    create_parser.add_argument("--gguf", type=Path, required=True, help="Path to the GGUF file.")
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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
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
            if not args.gguf.is_file():
                raise RuntimeIntegrationError(f"GGUF file not found: {args.gguf}")
            modelfile_text = render_modelfile(
                profile,
                gguf_path=args.gguf,
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


def _command_output(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return (completed.stdout or completed.stderr).strip() or "unknown"
