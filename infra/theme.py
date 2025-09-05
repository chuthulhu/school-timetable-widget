from __future__ import annotations

from typing import Dict
from core.model import AppConfig


LIGHT_TOKENS: Dict[str, str] = {
    "header_bg": "#F2F2F2",
    "header_text": "#222222",
    "cell_bg": "#FFFFFF",
    "cell_text": "#222222",
    "border": "#DDDDDD",
    "current_bg": "#FFE696",
}


DARK_TOKENS: Dict[str, str] = {
    "header_bg": "#2C2C2C",
    "header_text": "#EAEAEA",
    "cell_bg": "#1E1E1E",
    "cell_text": "#EAEAEA",
    "border": "#3A3A3A",
    "current_bg": "#6B5E2E",
}


def compute_tokens(cfg: AppConfig) -> Dict[str, str]:
    base = LIGHT_TOKENS if (cfg.theme.preset or "light") == "light" else DARK_TOKENS
    merged = dict(base)
    # override with custom tokens if provided
    for k, v in (cfg.theme.tokens or {}).items():
        merged[k] = v
    return merged


def generate_stylesheet(tokens: Dict[str, str]) -> str:
    # Use dynamic properties: role=dayHeader|periodHeader|cell, current=true
    return f"""
QWidget {{
    background: transparent;
}}
QLabel[role="dayHeader"], QLabel[role="periodHeader"] {{
    background-color: {tokens['header_bg']};
    color: {tokens['header_text']};
    border: 1px solid {tokens['border']};
    padding: 6px 8px;
    font-weight: 600;
}}
QLabel[role="cell"] {{
    background-color: {tokens['cell_bg']};
    color: {tokens['cell_text']};
    border: 1px solid {tokens['border']};
    padding: 6px 8px;
}}
QLabel[role="cell"][current="true"] {{
    background-color: {tokens['current_bg']};
}}
"""


def get_stylesheet(cfg: AppConfig) -> str:
    return generate_stylesheet(compute_tokens(cfg))


