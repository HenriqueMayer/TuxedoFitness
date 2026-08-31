#!/usr/bin/env python3
"""Export private read-only Hevy routine and exercise-template snapshots."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

DEFAULT_API_BASE_URL = "https://api.hevyapp.com"
DEFAULT_HEVY_DIR = Path("var/private/hevy-snapshots")
DEFAULT_OUTPUT_DIR = DEFAULT_HEVY_DIR / "workout-routine"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--hevy-dir", type=Path, default=DEFAULT_HEVY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def load_env(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"Environment file not found: {path}")

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def validate_api_base_url(value: str) -> str:
    base_url = value.rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme != "https" or parsed.hostname != "api.hevyapp.com":
        raise SystemExit(
            "Refusing to transmit HEVY_API_KEY to an unexpected host: "
            f"{parsed.hostname!r}"
        )
    return base_url


def fetch_all_pages(
    *,
    base_url: str,
    api_key: str,
    path: str,
    collection_keys: tuple[str, ...],
    page_size: int,
) -> tuple[list[dict[str, Any]], int, str]:
    records: list[dict[str, Any]] = []
    page = 1
    page_count = 1
    resolved_collection_key = ""

    while page <= page_count:
        query = urlencode({"page": page, "pageSize": page_size})
        request = Request(
            f"{base_url}{path}?{query}",
            headers={
                "api-key": api_key,
                "Accept": "application/json",
                "User-Agent": "TuxedoFitness-Hevy-Exporter/1.0",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.load(response)
        except HTTPError as exc:
            raise SystemExit(f"Hevy API returned HTTP {exc.code} for {path}") from exc
        except URLError as exc:
            raise SystemExit(f"Could not reach the Hevy API for {path}: {exc.reason}") from exc

        page_count = int(body.get("page_count", page))
        page_number = int(body.get("page", page))
        if page_number != page:
            raise SystemExit(
                f"Unexpected page number for {path}: requested {page}, received {page_number}"
            )

        available_key = next(
            (key for key in collection_keys if isinstance(body.get(key), list)),
            None,
        )
        if available_key is None:
            raise SystemExit(
                f"Hevy response for {path} has none of the expected lists: "
                f"{', '.join(collection_keys)}"
            )
        if resolved_collection_key and available_key != resolved_collection_key:
            raise SystemExit(f"Hevy changed collection keys between pages for {path}")
        resolved_collection_key = available_key
        collection = body[available_key]
        records.extend(collection)
        page += 1

    return records, page_count, resolved_collection_key


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "routine"


def natural_key(value: str) -> list[Any]:
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", value)]


def format_number(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def markdown_cell(value: Any) -> str:
    """Keep generated table cells valid when Hevy text contains Markdown syntax."""
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def format_duration(seconds: Any) -> str:
    total = int(seconds)
    minutes, remainder = divmod(total, 60)
    if minutes:
        return f"{minutes}m {remainder:02d}s"
    return f"{remainder}s"


def format_set(training_set: dict[str, Any]) -> str:
    parts: list[str] = []
    weight = training_set.get("weight_kg")
    reps = training_set.get("reps")
    rep_range = training_set.get("rep_range")
    distance = training_set.get("distance_meters")
    duration = training_set.get("duration_seconds")
    custom_metric = training_set.get("custom_metric")

    if weight is not None:
        parts.append(f"{format_number(weight)} kg")
    if reps is not None:
        parts.append(f"{format_number(reps)} reps")
    if isinstance(rep_range, dict):
        start = rep_range.get("start")
        end = rep_range.get("end")
        if start is not None and end is not None:
            parts.append(f"faixa {format_number(start)}–{format_number(end)} reps")
    if distance is not None:
        parts.append(f"{format_number(distance)} m")
    if duration is not None:
        parts.append(format_duration(duration))
    if custom_metric is not None:
        parts.append(f"métrica personalizada: {format_number(custom_metric)}")

    return " × ".join(parts) if parts else "Sem alvo numérico"


def folder_label(folder_id: Any, folder_titles: dict[Any, str]) -> str:
    if folder_id is None:
        return "My Routines (padrão)"
    return folder_titles.get(folder_id, f"Pasta Hevy #{folder_id}")


def render_routine_markdown(
    routine: dict[str, Any],
    *,
    folder_titles: dict[Any, str],
    extracted_at: str,
) -> str:
    exercises = sorted(routine.get("exercises") or [], key=lambda item: item.get("index", 0))
    total_sets = sum(len(exercise.get("sets") or []) for exercise in exercises)
    lines = [
        f"# {routine.get('title') or 'Rotina sem título'}",
        "",
        f"- **ID Hevy:** `{routine.get('id')}`",
        f"- **Pasta:** {folder_label(routine.get('folder_id'), folder_titles)}",
        f"- **Criada em:** {routine.get('created_at') or 'não informado'}",
        f"- **Atualizada em:** {routine.get('updated_at') or 'não informado'}",
        f"- **Extraída em:** {extracted_at}",
        f"- **Exercícios:** {len(exercises)}",
        f"- **Séries prescritas:** {total_sets}",
        "",
    ]

    for fallback_index, exercise in enumerate(exercises, 1):
        exercise_index = exercise.get("index", fallback_index - 1) + 1
        lines.extend(
            [
                f"## {exercise_index}. {exercise.get('title') or 'Exercício sem título'}",
                "",
                f"- **Exercise template ID:** `{exercise.get('exercise_template_id')}`",
                f"- **Descanso:** {format_duration(exercise['rest_seconds']) if exercise.get('rest_seconds') is not None else 'não informado'}",
                f"- **Superset:** `{exercise.get('superset_id')}`" if exercise.get("superset_id") is not None else "- **Superset:** não",
            ]
        )
        if exercise.get("notes"):
            lines.append(f"- **Notas:** {exercise['notes']}")
        lines.extend(["", "| Série | Tipo | Prescrição |", "| ---: | --- | --- |"])

        sets = sorted(exercise.get("sets") or [], key=lambda item: item.get("index", 0))
        if not sets:
            lines.append("| — | — | Nenhuma série prescrita |")
        for fallback_set_index, training_set in enumerate(sets, 1):
            set_index = training_set.get("index", fallback_set_index - 1) + 1
            lines.append(
                f"| {set_index} | `{training_set.get('type') or 'unknown'}` | {format_set(training_set)} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_readme(
    routines: list[dict[str, Any]],
    *,
    folder_titles: dict[Any, str],
    extracted_at: str,
    filenames: dict[str, str],
) -> str:
    lines = [
        "# Rotinas atuais do Hevy",
        "",
        "Snapshot somente leitura das rotinas planejadas na conta Hevy.",
        "",
        f"- **Extraído em:** {extracted_at}",
        "- **Fonte:** `GET /v1/routines` com todas as páginas",
        f"- **Quantidade de rotinas:** {len(routines)}",
        "- **Snapshot consolidado:** [`routines.json`](routines.json)",
        "",
        "## Rotinas",
        "",
        "| Rotina | Pasta | Exercícios | Séries | Arquivo |",
        "| --- | --- | ---: | ---: | --- |",
    ]

    for routine in sorted(routines, key=lambda item: natural_key(item.get("title") or "")):
        exercises = routine.get("exercises") or []
        total_sets = sum(len(exercise.get("sets") or []) for exercise in exercises)
        filename = filenames[str(routine.get("id"))]
        lines.append(
            "| "
            f"{routine.get('title') or 'Rotina sem título'} | "
            f"{folder_label(routine.get('folder_id'), folder_titles)} | "
            f"{len(exercises)} | {total_sets} | [`{filename}`]({filename}) |"
        )

    lines.extend(
        [
            "",
            "## Atualização",
            "",
            "Execute a partir da raiz do repositório:",
            "",
            "```bash",
            "uv run python scripts/hevy/export_snapshot.py",
            "```",
            "",
            "A chave é lida de `.env`, enviada apenas no header `api-key` para",
            "`https://api.hevyapp.com` e nunca é gravada nestes arquivos.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_available_exercises_markdown(
    exercises: list[dict[str, Any]],
    *,
    extracted_at: str,
    extraction_date: str,
    pages: int,
) -> str:
    lines = [
        f"# Exercícios disponíveis no Hevy — {extraction_date}",
        "",
        "Snapshot somente leitura do catálogo de exercícios disponível na conta Hevy.",
        "",
        f"- **Extraído em:** {extracted_at}",
        "- **Fonte:** `GET /v1/exercise_templates` com todas as páginas",
        f"- **Páginas:** {pages}",
        f"- **Quantidade:** {len(exercises)}",
        "- **Dados completos:** o JSON desta mesma data é a fonte fiel dos campos retornados pela API.",
        "",
        "| # | ID | Exercício | Tipo | Equipamento | Músculo principal | Músculos secundários | Personalizado |",
        "| ---: | --- | --- | --- | --- | --- | --- | :---: |",
    ]
    for index, exercise in enumerate(
        sorted(exercises, key=lambda item: natural_key(item.get("title") or "")),
        1,
    ):
        secondary = ", ".join(str(item) for item in (exercise.get("secondary_muscle_groups") or []))
        lines.append(
            "| "
            f"{index} | `{markdown_cell(exercise.get('id'))}` | "
            f"{markdown_cell(exercise.get('title') or 'Sem título')} | "
            f"{markdown_cell(exercise.get('type'))} | "
            f"{markdown_cell(exercise.get('equipment'))} | "
            f"{markdown_cell(exercise.get('primary_muscle_group'))} | "
            f"{markdown_cell(secondary)} | "
            f"{'sim' if exercise.get('is_custom') else 'não'} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_hevy_readme(
    *,
    extracted_at: str,
    exercise_count: int,
    exercise_json_filename: str,
    exercise_markdown_filename: str,
) -> str:
    lines = [
        "# Exportações do Hevy",
        "",
        "Snapshots locais, somente leitura, obtidos da API Hevy.",
        "",
        f"- **Última extração:** {extracted_at}",
        "- **Rotinas planejadas:** [`workout-routine/README.md`](workout-routine/README.md)",
        f"- **Exercícios disponíveis nesta extração:** {exercise_count}",
        f"- **Catálogo JSON:** [`{exercise_json_filename}`]({exercise_json_filename})",
        f"- **Catálogo Markdown:** [`{exercise_markdown_filename}`]({exercise_markdown_filename})",
        "",
        "## Atualização",
        "",
        "Execute a partir da raiz do repositório:",
        "",
        "```bash",
        "uv run python scripts/hevy/export_snapshot.py",
        "```",
        "",
        "Os arquivos do catálogo usam a data da extração no nome. A chave é lida de `.env`, enviada apenas para `https://api.hevyapp.com` e nunca é gravada nos snapshots.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    env = load_env(args.env_file)
    api_key = env.get("HEVY_API_KEY", "")
    if not api_key or api_key in {"your-real-key", "replace-with-a-real-key"}:
        raise SystemExit("HEVY_API_KEY is missing or still uses the placeholder value")

    base_url = validate_api_base_url(env.get("HEVY_API_BASE_URL", DEFAULT_API_BASE_URL))
    routines, routine_pages, routines_collection_key = fetch_all_pages(
        base_url=base_url,
        api_key=api_key,
        path="/v1/routines",
        collection_keys=("routines",),
        page_size=10,
    )
    folders, folder_pages, folders_collection_key = fetch_all_pages(
        base_url=base_url,
        api_key=api_key,
        path="/v1/routine_folders",
        # The live API currently returns this endpoint under `routines`, while
        # the local Swagger snapshot documents `routine_folders`. Accept both.
        collection_keys=("routine_folders", "routines"),
        page_size=10,
    )
    exercises, exercise_pages, exercises_collection_key = fetch_all_pages(
        base_url=base_url,
        api_key=api_key,
        path="/v1/exercise_templates",
        collection_keys=("exercise_templates",),
        page_size=100,
    )

    extraction_moment = datetime.now().astimezone()
    extracted_at = extraction_moment.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    extraction_date = extraction_moment.date().isoformat()
    hevy_dir = args.hevy_dir
    output_dir = args.output_dir
    hevy_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    folder_titles = {folder.get("id"): folder.get("title", "") for folder in folders}
    filenames: dict[str, str] = {}
    used_filenames: set[str] = set()
    for routine in routines:
        routine_id = str(routine.get("id"))
        base_filename = f"{slugify(routine.get('title') or 'routine')}.md"
        filename = base_filename
        if filename in used_filenames:
            filename = f"{Path(base_filename).stem}-{slugify(routine_id)}.md"
        used_filenames.add(filename)
        filenames[routine_id] = filename
        (output_dir / filename).write_text(
            render_routine_markdown(
                routine,
                folder_titles=folder_titles,
                extracted_at=extracted_at,
            ),
            encoding="utf-8",
        )

    snapshot = {
        "schema_version": 1,
        "provider": "Hevy",
        "extracted_at": extracted_at,
        "source": {
            "routines_endpoint": "/v1/routines",
            "routine_pages": routine_pages,
            "routines_collection_key": routines_collection_key,
            "routine_folders_endpoint": "/v1/routine_folders",
            "routine_folder_pages": folder_pages,
            "routine_folders_collection_key": folders_collection_key,
        },
        "routine_count": len(routines),
        "routine_folder_count": len(folders),
        "routine_folders": folders,
        "routines": routines,
    }
    (output_dir / "routines.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(
        render_readme(
            routines,
            folder_titles=folder_titles,
            extracted_at=extracted_at,
            filenames=filenames,
        ),
        encoding="utf-8",
    )

    exercise_json_filename = f"available-exercise-{extraction_date}.json"
    exercise_markdown_filename = f"available-exercise-{extraction_date}.md"
    exercise_snapshot = {
        "schema_version": 1,
        "provider": "Hevy",
        "extraction_date": extraction_date,
        "extracted_at": extracted_at,
        "source": {
            "endpoint": "/v1/exercise_templates",
            "pages": exercise_pages,
            "collection_key": exercises_collection_key,
            "page_size": 100,
        },
        "exercise_template_count": len(exercises),
        "exercise_templates": exercises,
    }
    (hevy_dir / exercise_json_filename).write_text(
        json.dumps(exercise_snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (hevy_dir / exercise_markdown_filename).write_text(
        render_available_exercises_markdown(
            exercises,
            extracted_at=extracted_at,
            extraction_date=extraction_date,
            pages=exercise_pages,
        ),
        encoding="utf-8",
    )
    (hevy_dir / "README.md").write_text(
        render_hevy_readme(
            extracted_at=extracted_at,
            exercise_count=len(exercises),
            exercise_json_filename=exercise_json_filename,
            exercise_markdown_filename=exercise_markdown_filename,
        ),
        encoding="utf-8",
    )

    print(f"Exported {len(routines)} routines to {output_dir}")
    for routine in sorted(routines, key=lambda item: natural_key(item.get("title") or "")):
        print(f"- {routine.get('title')}: {filenames[str(routine.get('id'))]}")
    print(f"Exported {len(exercises)} exercise templates to {hevy_dir / exercise_json_filename}")


if __name__ == "__main__":
    main()
