#!/usr/bin/env python3
"""Publish a tour only after all isolated synthetic screenshots succeed."""

import os
import shutil
import struct
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    with tempfile.TemporaryDirectory(prefix="fitness-capture-") as directory:
        stage = Path(directory)
        env = {**os.environ, "FITNESS_CAPTURE_DIR": str(stage)}
        subprocess.run(
            [
                sys.executable,
                "scripts/run_e2e.py",
                "--config",
                ".github/preview/capture.config.js",
            ],
            cwd=ROOT,
            env=env,
            check=True,
        )
        expected = [
            f"{lang}-{surface}.png"
            for lang in ["en", "pt-br"]
            for surface in [
                "overview",
                "analysis",
                "history",
                "routines",
                "exercises",
                "prompt",
            ]
        ]
        if any(
            not (stage / name).is_file() or (stage / name).stat().st_size < 1000
            for name in expected
        ):
            raise RuntimeError("Incomplete captures; the public tour was not changed.")
        destination = ROOT / "preview/assets"
        destination.mkdir(parents=True, exist_ok=True)
        for name in expected:
            shutil.copy2(stage / name, destination / name)
        shutil.copy2(ROOT / "static/css/app.css", destination / "app.css")
        shutil.copytree(
            ROOT / "static/fonts", ROOT / "preview/fonts", dirs_exist_ok=True
        )
        shutil.copy2(
            ROOT / "static/js/theme-bootstrap.js", destination / "theme-bootstrap.js"
        )
        shutil.copy2(ROOT / "static/js/theme.js", destination / "theme.js")
        for lang in ["en", "pt-br"]:
            write_tour(lang)
    print("Published 12 synthetic captures and bilingual static tour files locally.")


def write_tour(lang):
    pt = lang == "pt-br"
    prefix = "../" if pt else ""
    labels = (
        [
            "Visão geral",
            "Análises",
            "Histórico",
            "Rotinas",
            "Exercícios",
            "Gerar prompt",
        ]
        if pt
        else [
            "Overview",
            "Analysis",
            "History",
            "Routines",
            "Exercises",
            "Generate prompt",
        ]
    )
    intro = "Conheça o Tuxedo Fitness" if pt else "Explore Tuxedo Fitness"
    note = (
        "Prévia estática com dados inteiramente sintéticos. Nenhuma conta real ou conexão Hevy é usada."
        if pt
        else "A static tour using entirely synthetic data. No real account or Hevy connection is used."
    )
    other = "../index.html" if pt else "pt-br/index.html"

    def asset_url(name):
        digest = sha256((ROOT / "preview/assets" / name).read_bytes()).hexdigest()[:16]
        return f"{prefix}assets/{name}?v={digest}"

    def dimensions(name):
        header = (ROOT / "preview/assets" / f"{lang}-{name}.png").read_bytes()[:24]
        width, height = struct.unpack(">II", header[16:24])
        return f'width="{width}" height="{height}"'

    sections = "".join(
        f'<section id="{name}" class="panel mb-8"><h2 class="mb-5 text-2xl font-semibold">{label}</h2><img class="w-full rounded-xl" src="{asset_url(f"{lang}-{name}.png")}" alt="{label} · Tuxedo Fitness" {dimensions(name)} loading="lazy"></section>'
        for name, label in zip(
            ["overview", "analysis", "history", "routines", "exercises", "prompt"],
            labels,
            strict=True,
        )
    )
    nav = "".join(
        f'<a class="btn-secondary" href="#{name}">{label}</a>'
        for name, label in zip(
            ["overview", "analysis", "history", "routines", "exercises", "prompt"],
            labels,
            strict=True,
        )
    )
    html = f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tuxedo Fitness · {intro}</title><script src="{asset_url("theme-bootstrap.js")}"></script><link rel="stylesheet" href="{asset_url("app.css")}"><script src="{asset_url("theme.js")}" defer></script></head><body class="bg-cream font-sans text-forest dark:bg-night dark:text-cream"><main class="mx-auto max-w-7xl px-4 py-10 sm:px-6"><header class="mb-10"><p class="eyebrow">Tuxedo / Fitness · 0.2.0</p><h1 class="page-title my-5">{intro}</h1><p class="muted">{note}</p><div class="my-6 flex gap-3"><a class="btn" href="{other}">{"English" if pt else "Português (Brasil)"}</a><button class="btn-secondary" type="button" data-theme-toggle>{"Alternar tema" if pt else "Toggle theme"}</button><a class="btn-secondary" href="https://github.com/henriquemayer/TuxedoFitness">GitHub</a></div><nav class="flex flex-wrap gap-3">{nav}</nav></header>{sections}</main></body></html>'''
    target = ROOT / "preview" / ("pt-br/index.html" if pt else "index.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html)


if __name__ == "__main__":
    main()
