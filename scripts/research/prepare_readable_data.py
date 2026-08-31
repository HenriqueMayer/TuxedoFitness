#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pandas==3.0.5",
#   "pyarrow==25.0.1",
# ]
# ///
"""Convert downloaded NHANES XPT sources to readable CSV and compact Parquet.

The curated CSV files use descriptive column names and decoded categories.
The full Parquet files preserve every source column and its original name.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_ROOT = PROJECT_ROOT / "research"
RAW = RESEARCH_ROOT / "datasets" / "raw"
PROCESSED = RESEARCH_ROOT / "datasets" / "processed"
CURATED = PROCESSED / "curated"
FULL = PROCESSED / "full"

COLLECTIONS = {
    "nhanes_2021_2023": ("BMX_L", "DEMO_L", "PAQ_L", "MCQ_L"),
    "nhanes_2017_2018": ("BMX_J", "DEMO_J", "DXX_J", "PAQ_J", "MCQ_J"),
    "nhanes_2013_2014": ("BMX_H", "DEMO_H", "MGX_H"),
}

YES_NO = {1: "yes", 2: "no", 7: "refused", 9: "dont_know"}
SEX = {1: "male", 2: "female"}
EXAM_STATUS = {1: "interviewed_only", 2: "interviewed_and_examined"}
BODY_STATUS = {
    1: "complete_for_age_group",
    2: "partial_height_and_weight_only",
    3: "other_partial_exam",
    4: "not_examined",
}
DXA_STATUS = {
    1: "complete",
    2: "complete_but_invalid",
    3: "not_scanned_pregnancy",
    4: "not_scanned_weight_limit",
    5: "not_scanned_height_limit",
    6: "not_scanned_other_reason",
}
GRIP_STATUS = {
    1: "completed_both_hands",
    2: "completed_one_hand",
    3: "not_performed",
}
EFFORT_STATUS = {1: "maximal", 2: "questionable"}
FREQUENCY_UNIT = {"D": "day", "W": "week", "M": "month", "Y": "year"}

DICTIONARY: list[dict[str, str]] = []


def require_columns(frame: pd.DataFrame, table: str, columns: set[str]) -> None:
    missing = columns.difference(frame.columns)
    if missing:
        raise ValueError(f"{table} is missing required columns: {sorted(missing)}")
    if not frame["SEQN"].is_unique:
        raise ValueError(f"{table}.SEQN must be unique")


def load_sources() -> dict[str, dict[str, pd.DataFrame]]:
    loaded: dict[str, dict[str, pd.DataFrame]] = {}
    for collection, names in COLLECTIONS.items():
        loaded[collection] = {}
        for name in names:
            path = RAW / collection / f"{name}.xpt"
            if not path.exists():
                raise FileNotFoundError(
                    f"Missing {path}. Run `uv run python scripts/research/fetch_priority_datasets.py` first."
                )
            frame = pd.read_sas(path, format="xport")
            # SAS/XPORT numeric missing values can surface as the smallest
            # positive IBM floating-point value instead of NaN. Real NHANES
            # measurements never use this magnitude; normalize it before any
            # typing, joining, CSV export or Parquet conversion.
            numeric_columns = frame.select_dtypes(include="number").columns
            numeric = frame[numeric_columns]
            sas_missing = numeric.ne(0) & numeric.abs().lt(1e-70)
            frame[numeric_columns] = numeric.mask(sas_missing)
            require_columns(frame, name, {"SEQN"})
            loaded[collection][name] = frame
    return loaded


def identifier(values: pd.Series) -> pd.Series:
    return values.astype("Int64")


def integer(values: pd.Series, invalid: tuple[int, ...] = ()) -> pd.Series:
    return values.mask(values.isin(invalid)).astype("Int64")


def number(values: pd.Series, invalid: tuple[int, ...] = ()) -> pd.Series:
    return pd.to_numeric(values.mask(values.isin(invalid)), errors="coerce")


def decoded(values: pd.Series, mapping: dict[Any, str]) -> pd.Series:
    return values.map(mapping).astype("string")


def decoded_text(values: pd.Series, mapping: dict[str, str]) -> pd.Series:
    def convert(value: Any) -> Any:
        if pd.isna(value):
            return pd.NA
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        text = str(value).strip()
        return mapping.get(text, text) if text else pd.NA

    return values.map(convert).astype("string")


def response_status(values: pd.Series, refused: int = 7777, unknown: int = 9999) -> pd.Series:
    status = pd.Series("answered", index=values.index, dtype="string")
    status.loc[values.isna()] = pd.NA
    status.loc[values.eq(refused)] = "refused"
    status.loc[values.eq(unknown)] = "dont_know"
    return status


def select(frame: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    return frame[list(mapping)].rename(columns=mapping).copy()


def merge_one_to_one(left: pd.DataFrame, right: pd.DataFrame) -> pd.DataFrame:
    return left.merge(right, on="participant_id", how="left", validate="one_to_one")


def add_dictionary(
    dataset: str,
    column: str,
    description_pt: str,
    source: str,
    unit: str = "",
    caveat: str = "",
) -> None:
    DICTIONARY.append(
        {
            "dataset": dataset,
            "column": column,
            "description_pt": description_pt,
            "unit": unit,
            "source_variable": source,
            "caveat": caveat,
        }
    )


def add_common_dictionary(dataset: str) -> None:
    common = (
        ("participant_id", "Identificador público anonimizado do participante na coleta", "SEQN", "", "Válido somente dentro da mesma coleta NHANES"),
        ("age_years", "Idade na entrevista de triagem", "RIDAGEYR", "anos", "CSV curado contém somente adultos de 18 anos ou mais; idades mais altas podem ser agrupadas pelo CDC"),
        ("sex", "Sexo registrado na pesquisa", "RIAGENDR", "", "Valores decodificados como male/female"),
        ("interview_sample_weight", "Peso amostral da entrevista", "WTINT2YR", "", "Necessário para estimativas populacionais baseadas somente em entrevista"),
        ("exam_sample_weight", "Peso amostral do exame MEC", "WTMEC2YR", "", "Use quando a análise contém medidas do exame"),
        ("survey_stratum", "Estrato mascarado do desenho amostral", "SDMVSTRA", "", "Use com peso e PSU para estimar variância"),
        ("survey_psu", "Unidade primária mascarada do desenho amostral", "SDMVPSU", "", "Use com peso e estrato para estimar variância"),
    )
    for column, description, source, unit, caveat in common:
        add_dictionary(dataset, column, description, source, unit, caveat)


def current_population(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dataset = "population_reference_2021_2023.csv"
    demo = tables["DEMO_L"]
    bmx = tables["BMX_L"]
    paq = tables["PAQ_L"]
    mcq = tables["MCQ_L"]
    require_columns(
        demo,
        "DEMO_L",
        {"SEQN", "RIDSTATR", "RIAGENDR", "RIDAGEYR", "WTINT2YR", "WTMEC2YR", "SDMVSTRA", "SDMVPSU"},
    )
    require_columns(
        bmx,
        "BMX_L",
        {"SEQN", "BMDSTATS", "BMXWT", "BMXHT", "BMXBMI", "BMXLEG", "BMXARML", "BMXARMC", "BMXWAIST", "BMXHIP"},
    )
    require_columns(paq, "PAQ_L", {"SEQN", "PAD790Q", "PAD790U", "PAD800", "PAD810Q", "PAD810U", "PAD820", "PAD680"})
    require_columns(
        mcq,
        "MCQ_L",
        {"SEQN", "MCQ010", "MCQ160A", "MCQ160B", "MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F", "MCQ160P", "MCQ160L"},
    )

    output = select(
        demo,
        {
            "SEQN": "participant_id",
            "RIDSTATR": "exam_status",
            "RIAGENDR": "sex",
            "RIDAGEYR": "age_years",
            "WTINT2YR": "interview_sample_weight",
            "WTMEC2YR": "exam_sample_weight",
            "SDMVSTRA": "survey_stratum",
            "SDMVPSU": "survey_psu",
        },
    )
    output["participant_id"] = identifier(output["participant_id"])
    output["exam_status"] = decoded(output["exam_status"], EXAM_STATUS)
    output["sex"] = decoded(output["sex"], SEX)
    output["age_years"] = integer(output["age_years"])
    output["survey_stratum"] = integer(output["survey_stratum"])
    output["survey_psu"] = integer(output["survey_psu"])

    body = select(
        bmx,
        {
            "SEQN": "participant_id",
            "BMDSTATS": "body_measure_status",
            "BMXWT": "weight_kg",
            "BMXHT": "height_cm",
            "BMXBMI": "bmi_kg_m2",
            "BMXLEG": "upper_leg_length_cm",
            "BMXARML": "upper_arm_length_cm",
            "BMXARMC": "arm_circumference_cm",
            "BMXWAIST": "waist_circumference_cm",
            "BMXHIP": "hip_circumference_cm",
        },
    )
    body["participant_id"] = identifier(body["participant_id"])
    body["body_measure_status"] = decoded(body["body_measure_status"], BODY_STATUS)
    output = merge_one_to_one(output, body)

    activity = select(
        paq,
        {
            "SEQN": "participant_id",
            "PAD790Q": "moderate_leisure_frequency",
            "PAD790U": "moderate_leisure_frequency_unit",
            "PAD800": "moderate_leisure_minutes_per_session",
            "PAD810Q": "vigorous_leisure_frequency",
            "PAD810U": "vigorous_leisure_frequency_unit",
            "PAD820": "vigorous_leisure_minutes_per_session",
            "PAD680": "sedentary_minutes_per_day",
        },
    )
    activity["participant_id"] = identifier(activity["participant_id"])
    for column in ("moderate_leisure_frequency", "vigorous_leisure_frequency"):
        activity[f"{column}_response"] = response_status(activity[column])
        activity[column] = integer(activity[column], (7777, 9999))
    for column in (
        "moderate_leisure_minutes_per_session",
        "vigorous_leisure_minutes_per_session",
        "sedentary_minutes_per_day",
    ):
        activity[f"{column}_response"] = response_status(activity[column])
        activity[column] = integer(activity[column], (7777, 9999))
    for column in ("moderate_leisure_frequency_unit", "vigorous_leisure_frequency_unit"):
        activity[column] = decoded_text(activity[column], FREQUENCY_UNIT)
    output = merge_one_to_one(output, activity)

    conditions = select(
        mcq,
        {
            "SEQN": "participant_id",
            "MCQ010": "doctor_diagnosed_asthma",
            "MCQ160A": "doctor_diagnosed_arthritis",
            "MCQ160B": "doctor_diagnosed_congestive_heart_failure",
            "MCQ160C": "doctor_diagnosed_coronary_heart_disease",
            "MCQ160D": "doctor_diagnosed_angina",
            "MCQ160E": "doctor_diagnosed_heart_attack",
            "MCQ160F": "doctor_diagnosed_stroke",
            "MCQ160P": "doctor_diagnosed_copd_emphysema_or_chronic_bronchitis",
            "MCQ160L": "doctor_diagnosed_liver_condition",
        },
    )
    conditions["participant_id"] = identifier(conditions["participant_id"])
    for column in conditions.columns.difference(["participant_id"]):
        conditions[column] = decoded(conditions[column], YES_NO)
    output = merge_one_to_one(output, conditions)

    add_common_dictionary(dataset)
    metadata = (
        ("exam_status", "Situação de participação em entrevista e exame", "RIDSTATR", "", ""),
        ("body_measure_status", "Situação de completude das medidas corporais", "BMDSTATS", "", ""),
        ("weight_kg", "Peso corporal medido", "BMXWT", "kg", ""),
        ("height_cm", "Altura em pé medida", "BMXHT", "cm", ""),
        ("bmi_kg_m2", "IMC calculado pelo NHANES", "BMXBMI", "kg/m2", "Não é diagnóstico individual"),
        ("upper_leg_length_cm", "Comprimento da parte superior da perna", "BMXLEG", "cm", "Normalmente medido no lado direito; pode ser afetado por adiposidade extrema"),
        ("upper_arm_length_cm", "Comprimento da parte superior do braço", "BMXARML", "cm", "Normalmente medido no lado direito"),
        ("arm_circumference_cm", "Circunferência do braço", "BMXARMC", "cm", ""),
        ("waist_circumference_cm", "Circunferência da cintura", "BMXWAIST", "cm", ""),
        ("hip_circumference_cm", "Circunferência do quadril", "BMXHIP", "cm", "Disponível a partir de 12 anos"),
        ("moderate_leisure_frequency", "Frequência declarada de atividade moderada no lazer", "PAD790Q", "vezes", "Interpretar junto da unidade e do status da resposta"),
        ("moderate_leisure_frequency_unit", "Unidade da frequência moderada", "PAD790U", "day/week/month/year", ""),
        ("moderate_leisure_minutes_per_session", "Duração declarada de cada sessão moderada", "PAD800", "minutos", "Autorrelato; elegível a partir de 18 anos"),
        ("vigorous_leisure_frequency", "Frequência declarada de atividade vigorosa no lazer", "PAD810Q", "vezes", "Interpretar junto da unidade e do status da resposta"),
        ("vigorous_leisure_frequency_unit", "Unidade da frequência vigorosa", "PAD810U", "day/week/month/year", ""),
        ("vigorous_leisure_minutes_per_session", "Duração declarada de cada sessão vigorosa", "PAD820", "minutos", "Autorrelato; elegível a partir de 18 anos"),
        ("sedentary_minutes_per_day", "Tempo sedentário declarado em um dia típico", "PAD680", "minutos/dia", "Não inclui sono; elegível a partir de 18 anos"),
    )
    for column, description, source, unit, caveat in metadata:
        add_dictionary(dataset, column, description, source, unit, caveat)
    for column in (
        "moderate_leisure_frequency",
        "moderate_leisure_minutes_per_session",
        "vigorous_leisure_frequency",
        "vigorous_leisure_minutes_per_session",
        "sedentary_minutes_per_day",
    ):
        add_dictionary(dataset, f"{column}_response", "Estado da resposta numérica", "derived from source sentinel", "", "answered/refused/dont_know; vazio significa ausente ou fora da elegibilidade")
    condition_labels = {
        "doctor_diagnosed_asthma": ("Asma informada como diagnosticada por profissional", "MCQ010", "Elegível a partir de 1 ano"),
        "doctor_diagnosed_arthritis": ("Artrite informada como diagnosticada por profissional", "MCQ160A", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_congestive_heart_failure": ("Insuficiência cardíaca congestiva informada como diagnosticada", "MCQ160B", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_coronary_heart_disease": ("Doença coronariana informada como diagnosticada", "MCQ160C", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_angina": ("Angina informada como diagnosticada", "MCQ160D", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_heart_attack": ("Infarto informado como diagnosticado", "MCQ160E", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_stroke": ("AVC informado como diagnosticado", "MCQ160F", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_copd_emphysema_or_chronic_bronchitis": ("DPOC, enfisema ou bronquite crônica informados como diagnosticados", "MCQ160P", "Elegível a partir de 20 anos"),
        "doctor_diagnosed_liver_condition": ("Condição hepática informada como diagnosticada", "MCQ160L", "Elegível a partir de 20 anos"),
    }
    for column, (description, source, caveat) in condition_labels.items():
        add_dictionary(dataset, column, description, source, "yes/no/refused/dont_know", f"Autorrelato ou relato por procurador; {caveat}; vazio não significa no")
    return output.loc[output["age_years"].ge(18)].reset_index(drop=True)


def historical_body_composition(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dataset = "body_composition_2017_2018.csv"
    demo, bmx, dxx = tables["DEMO_J"], tables["BMX_J"], tables["DXX_J"]
    required_dxx = {
        "SEQN", "DXAEXSTS", "DXDTOBMC", "DXDTOBMD", "DXDTOFAT", "DXDTOLE", "DXDTOTOT", "DXDTOPF",
        "DXXTRFAT", "DXDTRLE", "DXXLAFAT", "DXDLALE", "DXXRAFAT", "DXDRALE", "DXXLLFAT", "DXDLLLE", "DXXRLFAT", "DXDRLLE",
    }
    require_columns(dxx, "DXX_J", required_dxx)

    output = select(
        dxx,
        {
            "SEQN": "participant_id",
            "DXAEXSTS": "dxa_exam_status",
            "DXDTOBMC": "total_bone_mineral_content_g",
            "DXDTOBMD": "total_bone_mineral_density_g_cm2",
            "DXDTOFAT": "total_fat_mass_g",
            "DXDTOLE": "total_lean_mass_excluding_bone_g",
            "DXDTOTOT": "total_mass_g",
            "DXDTOPF": "total_body_fat_percent",
            "DXXTRFAT": "trunk_fat_mass_g",
            "DXDTRLE": "trunk_lean_mass_excluding_bone_g",
            "DXXLAFAT": "left_arm_fat_mass_g",
            "DXDLALE": "left_arm_lean_mass_excluding_bone_g",
            "DXXRAFAT": "right_arm_fat_mass_g",
            "DXDRALE": "right_arm_lean_mass_excluding_bone_g",
            "DXXLLFAT": "left_leg_fat_mass_g",
            "DXDLLLE": "left_leg_lean_mass_excluding_bone_g",
            "DXXRLFAT": "right_leg_fat_mass_g",
            "DXDRLLE": "right_leg_lean_mass_excluding_bone_g",
        },
    )
    output["participant_id"] = identifier(output["participant_id"])
    output["dxa_exam_status"] = decoded(output["dxa_exam_status"], DXA_STATUS)

    demographics = select(
        demo,
        {
            "SEQN": "participant_id", "RIAGENDR": "sex", "RIDAGEYR": "age_years", "WTINT2YR": "interview_sample_weight",
            "WTMEC2YR": "exam_sample_weight", "SDMVSTRA": "survey_stratum", "SDMVPSU": "survey_psu",
        },
    )
    demographics["participant_id"] = identifier(demographics["participant_id"])
    demographics["sex"] = decoded(demographics["sex"], SEX)
    demographics["age_years"] = integer(demographics["age_years"])
    demographics["survey_stratum"] = integer(demographics["survey_stratum"])
    demographics["survey_psu"] = integer(demographics["survey_psu"])
    output = merge_one_to_one(output, demographics)

    body = select(
        bmx,
        {"SEQN": "participant_id", "BMXWT": "weight_kg", "BMXHT": "height_cm", "BMXBMI": "bmi_kg_m2", "BMXWAIST": "waist_circumference_cm"},
    )
    body["participant_id"] = identifier(body["participant_id"])
    output = merge_one_to_one(output, body)

    ordered = [
        "participant_id", "age_years", "sex", "interview_sample_weight", "exam_sample_weight", "survey_stratum", "survey_psu",
        "dxa_exam_status", "weight_kg", "height_cm", "bmi_kg_m2", "waist_circumference_cm",
        "total_mass_g", "total_fat_mass_g", "total_lean_mass_excluding_bone_g", "total_body_fat_percent",
        "total_bone_mineral_content_g", "total_bone_mineral_density_g_cm2", "trunk_fat_mass_g", "trunk_lean_mass_excluding_bone_g",
        "left_arm_fat_mass_g", "left_arm_lean_mass_excluding_bone_g", "right_arm_fat_mass_g", "right_arm_lean_mass_excluding_bone_g",
        "left_leg_fat_mass_g", "left_leg_lean_mass_excluding_bone_g", "right_leg_fat_mass_g", "right_leg_lean_mass_excluding_bone_g",
    ]
    output = output[ordered]

    add_common_dictionary(dataset)
    source_by_column = {
        "dxa_exam_status": "DXAEXSTS", "weight_kg": "BMXWT", "height_cm": "BMXHT", "bmi_kg_m2": "BMXBMI",
        "waist_circumference_cm": "BMXWAIST", "total_mass_g": "DXDTOTOT", "total_fat_mass_g": "DXDTOFAT",
        "total_lean_mass_excluding_bone_g": "DXDTOLE", "total_body_fat_percent": "DXDTOPF",
        "total_bone_mineral_content_g": "DXDTOBMC", "total_bone_mineral_density_g_cm2": "DXDTOBMD",
        "trunk_fat_mass_g": "DXXTRFAT", "trunk_lean_mass_excluding_bone_g": "DXDTRLE",
        "left_arm_fat_mass_g": "DXXLAFAT", "left_arm_lean_mass_excluding_bone_g": "DXDLALE",
        "right_arm_fat_mass_g": "DXXRAFAT", "right_arm_lean_mass_excluding_bone_g": "DXDRALE",
        "left_leg_fat_mass_g": "DXXLLFAT", "left_leg_lean_mass_excluding_bone_g": "DXDLLLE",
        "right_leg_fat_mass_g": "DXXRLFAT", "right_leg_lean_mass_excluding_bone_g": "DXDRLLE",
    }
    for column in ordered[7:]:
        unit = "" if column == "dxa_exam_status" else ("percent" if column.endswith("percent") else ("g/cm2" if column.endswith("g_cm2") else ("cm" if column.endswith("cm") else ("kg/m2" if column == "bmi_kg_m2" else ("kg" if column == "weight_kg" else "g")))))
        add_dictionary(dataset, column, column.replace("_", " "), source_by_column[column], unit, "Coleta histórica 2017-2018; DXA elegível principalmente para 8-59 anos")
    return output.loc[output["age_years"].ge(18)].reset_index(drop=True)


def historical_grip_strength(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    dataset = "grip_strength_2013_2014.csv"
    demo, bmx, mgx = tables["DEMO_H"], tables["BMX_H"], tables["MGX_H"]
    trials = ("MGXH1T1", "MGXH2T1", "MGXH1T2", "MGXH2T2", "MGXH1T3", "MGXH2T3")
    efforts = tuple(f"{trial}E" for trial in trials)
    require_columns(mgx, "MGX_H", {"SEQN", "MGDEXSTS", "MGDCGSZ", *trials, *efforts})

    output = select(
        mgx,
        {
            "SEQN": "participant_id", "MGDEXSTS": "grip_test_status", "MGDCGSZ": "combined_grip_strength_kg",
            "MGXH1T1": "hand_1_trial_1_kg", "MGXH2T1": "hand_2_trial_1_kg", "MGXH1T2": "hand_1_trial_2_kg",
            "MGXH2T2": "hand_2_trial_2_kg", "MGXH1T3": "hand_1_trial_3_kg", "MGXH2T3": "hand_2_trial_3_kg",
            "MGXH1T1E": "hand_1_trial_1_effort", "MGXH2T1E": "hand_2_trial_1_effort", "MGXH1T2E": "hand_1_trial_2_effort",
            "MGXH2T2E": "hand_2_trial_2_effort", "MGXH1T3E": "hand_1_trial_3_effort", "MGXH2T3E": "hand_2_trial_3_effort",
        },
    )
    output["participant_id"] = identifier(output["participant_id"])
    output["grip_test_status"] = decoded(output["grip_test_status"], GRIP_STATUS)
    for column in output.columns[output.columns.str.endswith("_effort")]:
        output[column] = decoded(output[column], EFFORT_STATUS)

    demographics = select(
        demo,
        {"SEQN": "participant_id", "RIAGENDR": "sex", "RIDAGEYR": "age_years", "WTINT2YR": "interview_sample_weight",
         "WTMEC2YR": "exam_sample_weight", "SDMVSTRA": "survey_stratum", "SDMVPSU": "survey_psu"},
    )
    demographics["participant_id"] = identifier(demographics["participant_id"])
    demographics["sex"] = decoded(demographics["sex"], SEX)
    demographics["age_years"] = integer(demographics["age_years"])
    demographics["survey_stratum"] = integer(demographics["survey_stratum"])
    demographics["survey_psu"] = integer(demographics["survey_psu"])
    output = merge_one_to_one(output, demographics)

    body = select(
        bmx,
        {"SEQN": "participant_id", "BMXWT": "weight_kg", "BMXHT": "height_cm", "BMXBMI": "bmi_kg_m2", "BMXLEG": "upper_leg_length_cm",
         "BMXARML": "upper_arm_length_cm", "BMXARMC": "arm_circumference_cm", "BMXWAIST": "waist_circumference_cm"},
    )
    body["participant_id"] = identifier(body["participant_id"])
    output = merge_one_to_one(output, body)

    leading = ["participant_id", "age_years", "sex", "interview_sample_weight", "exam_sample_weight", "survey_stratum", "survey_psu",
               "weight_kg", "height_cm", "bmi_kg_m2", "upper_leg_length_cm", "upper_arm_length_cm", "arm_circumference_cm", "waist_circumference_cm",
               "grip_test_status", "combined_grip_strength_kg"]
    output = output[leading + [column for column in output.columns if column not in leading]]

    add_common_dictionary(dataset)
    body_sources = {"weight_kg": "BMXWT", "height_cm": "BMXHT", "bmi_kg_m2": "BMXBMI", "upper_leg_length_cm": "BMXLEG",
                    "upper_arm_length_cm": "BMXARML", "arm_circumference_cm": "BMXARMC", "waist_circumference_cm": "BMXWAIST"}
    for column, source in body_sources.items():
        add_dictionary(dataset, column, column.replace("_", " "), source, "kg" if column == "weight_kg" else ("kg/m2" if column == "bmi_kg_m2" else "cm"), "Coleta histórica 2013-2014")
    add_dictionary(dataset, "grip_test_status", "Situação de conclusão do teste de preensão", "MGDEXSTS", "", "")
    add_dictionary(dataset, "combined_grip_strength_kg", "Soma da maior leitura de cada mão", "MGDCGSZ", "kg", "Não é média, 1RM ou medida de força corporal total")
    for trial, source in zip(
        ("hand_1_trial_1_kg", "hand_2_trial_1_kg", "hand_1_trial_2_kg", "hand_2_trial_2_kg", "hand_1_trial_3_kg", "hand_2_trial_3_kg"),
        trials,
    ):
        add_dictionary(dataset, trial, "Leitura individual do dinamômetro", source, "kg", "Hand 1/2 segue a identificação do protocolo, não uma inferência de dominância")
        add_dictionary(dataset, trial.removesuffix("_kg") + "_effort", "Avaliação do técnico sobre o esforço", source + "E", "maximal/questionable", "")
    return output.loc[output["age_years"].ge(18)].reset_index(drop=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def write_outputs(sources: dict[str, dict[str, pd.DataFrame]]) -> None:
    CURATED.mkdir(parents=True, exist_ok=True)
    FULL.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "generated_by": "scripts/research/prepare_readable_data.py",
        "outputs": [],
    }

    for collection, tables in sources.items():
        target = FULL / collection
        target.mkdir(parents=True, exist_ok=True)
        for table_name, frame in tables.items():
            path = target / f"{table_name}.parquet"
            frame.to_parquet(path, index=False, compression="zstd")
            manifest["outputs"].append(
                {"path": str(path.relative_to(RESEARCH_ROOT)), "rows": len(frame), "columns": len(frame.columns), "bytes": path.stat().st_size, "sha256": sha256(path), "kind": "full_source_parquet"}
            )

    curated = {
        "population_reference_2021_2023.csv": current_population(sources["nhanes_2021_2023"]),
        "body_composition_2017_2018.csv": historical_body_composition(sources["nhanes_2017_2018"]),
        "grip_strength_2013_2014.csv": historical_grip_strength(sources["nhanes_2013_2014"]),
    }
    for filename, frame in curated.items():
        path = CURATED / filename
        frame.to_csv(path, index=False, na_rep="", float_format="%.10g", lineterminator="\n")
        manifest["outputs"].append(
            {"path": str(path.relative_to(RESEARCH_ROOT)), "rows": len(frame), "columns": len(frame.columns), "bytes": path.stat().st_size, "sha256": sha256(path), "kind": "curated_readable_csv"}
        )

    dictionary = pd.DataFrame(DICTIONARY).sort_values(["dataset", "column"])
    dictionary_path = PROCESSED / "data_dictionary.csv"
    dictionary.to_csv(dictionary_path, index=False, na_rep="", lineterminator="\n")
    manifest["outputs"].append(
        {"path": str(dictionary_path.relative_to(RESEARCH_ROOT)), "rows": len(dictionary), "columns": len(dictionary.columns), "bytes": dictionary_path.stat().st_size, "sha256": sha256(dictionary_path), "kind": "data_dictionary"}
    )

    manifest_path = PROCESSED / "transformation_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sources = load_sources()
    write_outputs(sources)
    print(f"Readable data written to {PROCESSED.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
