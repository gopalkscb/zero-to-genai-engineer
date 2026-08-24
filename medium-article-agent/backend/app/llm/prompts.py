"""Jinja2 prompt template loader."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import get_settings


def get_prompt_env() -> Environment:
    settings = get_settings()
    return Environment(
        loader=FileSystemLoader(str(settings.prompts_dir)),
        autoescape=select_autoescape(default=False),
    )


def render_prompt(template_name: str, **kwargs) -> str:
    env = get_prompt_env()
    template = env.get_template(template_name)
    return template.render(**kwargs)
