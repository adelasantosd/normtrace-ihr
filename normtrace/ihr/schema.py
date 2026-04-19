"""
normtrace/ihr/schema.py

Validation of LLM outputs against the expected schema.

The LLM produces JSON findings. This module validates that output before
it is accepted into the analysis. Outputs that do not conform are rejected
with a descriptive error; they are never silently accepted or partially used.

This is the boundary between the LLM as extraction engine and the module
as analytical framework. The LLM cannot produce a finding that the schema
does not permit; it cannot use coverage categories that are not defined in
articles.py; it cannot omit a required field.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from normtrace.ihr.articles import (
    Block, SituationType, AttentionLevel, SELECTED_ARTICLES
)
from normtrace.ihr.scoring import ArticleFinding, BlockScore, ChainAssessment


VALID_CHAIN_VALUES = {"ok", "weak", "missing"}
VALID_COVERAGE = {s.value for s in SituationType}
VALID_ATTENTION = {a.value for a in AttentionLevel}
VALID_BLOCKS = {b.value for b in Block}


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]

    @classmethod
    def ok(cls) -> "ValidationResult":
        return cls(valid=True, errors=[], warnings=[])

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.valid = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


class SchemaValidationError(ValueError):
    """Raised when an LLM output fails schema validation."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(
            f"LLM output failed schema validation ({len(errors)} error(s)):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )


def validate_chain(chain: dict, path: str) -> ValidationResult:
    result = ValidationResult.ok()
    required_links = ["norm", "actor", "authority", "enforceability"]
    for link in required_links:
        if link not in chain:
            result.add_error(f"{path}.chain.{link}: missing required field")
        elif chain[link] not in VALID_CHAIN_VALUES:
            result.add_error(
                f"{path}.chain.{link}: invalid value '{chain[link]}',"
                f" must be one of {sorted(VALID_CHAIN_VALUES)}"
            )
    return result


def validate_article_finding(data: dict, article_id: str) -> ValidationResult:
    result = ValidationResult.ok()
    path = f"articles.{article_id}"

    required = [
        "article_id", "coverage", "attention_level",
        "chain", "instruments_searched", "sources_found", "finding_text"
    ]
    for field in required:
        if field not in data:
            result.add_error(f"{path}: missing required field '{field}'")

    if "coverage" in data and data["coverage"] not in VALID_COVERAGE:
        result.add_error(
            f"{path}.coverage: invalid value '{data['coverage']}',"
            f" must be one of {sorted(VALID_COVERAGE)}"
        )

    if "attention_level" in data and data["attention_level"] not in VALID_ATTENTION:
        result.add_error(
            f"{path}.attention_level: invalid value '{data['attention_level']}',"
            f" must be one of {sorted(VALID_ATTENTION)}"
        )

    if "chain" in data and isinstance(data["chain"], dict):
        chain_result = validate_chain(data["chain"], path)
        result.errors.extend(chain_result.errors)
        result.warnings.extend(chain_result.warnings)
        if not chain_result.valid:
            result.valid = False

    if "instruments_searched" in data and not isinstance(data["instruments_searched"], list):
        result.add_error(f"{path}.instruments_searched: must be a list")

    if "sources_found" in data:
        if not isinstance(data["sources_found"], list):
            result.add_error(f"{path}.sources_found: must be a list")
        else:
            for i, src in enumerate(data["sources_found"]):
                if "name" not in src:
                    result.add_error(f"{path}.sources_found[{i}]: missing 'name'")

    if "finding_text" in data and not isinstance(data["finding_text"], str):
        result.add_error(f"{path}.finding_text: must be a string")

    # Cross-check: article_id in output must match the key
    if "article_id" in data and data["article_id"] != article_id:
        result.add_warning(
            f"{path}: article_id in output ('{data['article_id']}')"
            f" does not match expected ('{article_id}')"
        )

    return result


def validate_block_output(raw: dict) -> ValidationResult:
    """Validate the full output for one analytical block."""
    result = ValidationResult.ok()

    if "block" not in raw:
        result.add_error("root: missing required field 'block'")
    elif raw["block"] not in VALID_BLOCKS:
        result.add_error(
            f"root.block: invalid value '{raw['block']}',"
            f" must be one of {sorted(VALID_BLOCKS)}"
        )

    if "articles" not in raw:
        result.add_error("root: missing required field 'articles'")
    elif not isinstance(raw["articles"], dict):
        result.add_error("root.articles: must be an object")
    else:
        for article_id, finding in raw["articles"].items():
            finding_result = validate_article_finding(finding, article_id)
            result.errors.extend(finding_result.errors)
            result.warnings.extend(finding_result.warnings)
            if not finding_result.valid:
                result.valid = False

    for field in ["intersectorality_note", "articulation_gaps", "amendment_2024_gaps"]:
        if field not in raw:
            result.add_warning(f"root: recommended field '{field}' is missing")

    return result


def validate_and_parse_block(raw_json: str) -> tuple[dict, ValidationResult]:
    """
    Parse and validate a block output from the LLM.
    Raises SchemaValidationError if the output is structurally invalid.
    Returns (parsed_dict, validation_result) on success.
    """
    try:
        start = raw_json.find("{")
        end = raw_json.rfind("}") + 1
        if start == -1 or end == 0:
            raise SchemaValidationError(["No JSON object found in LLM output"])
        parsed = json.loads(raw_json[start:end])
    except json.JSONDecodeError as exc:
        raise SchemaValidationError([f"JSON parse error: {exc}"]) from exc

    result = validate_block_output(parsed)
    if not result.valid:
        raise SchemaValidationError(result.errors)

    return parsed, result


def parse_article_finding(data: dict, block: Block) -> ArticleFinding:
    """Convert a validated finding dict to an ArticleFinding object."""
    chain = ChainAssessment(
        norm=data["chain"]["norm"],
        actor=data["chain"]["actor"],
        authority=data["chain"]["authority"],
        enforceability=data["chain"]["enforceability"],
    )
    return ArticleFinding(
        article_id=data["article_id"],
        block=block,
        coverage=SituationType(data["coverage"]),
        attention_level=AttentionLevel(data["attention_level"]),
        chain=chain,
        instruments_searched=data.get("instruments_searched", []),
        sources_found=data.get("sources_found", []),
        finding_text=data["finding_text"],
        is_2024_gap=data.get("is_2024_gap", False),
    )


def parse_block_result(parsed: dict) -> BlockScore:
    """Convert a validated block output dict to a BlockScore object."""
    block = Block(parsed["block"])
    findings = [
        parse_article_finding(finding_data, block)
        for finding_data in parsed["articles"].values()
    ]

    from normtrace.ihr.scoring import score_block
    score = score_block(findings)

    gaps = [
        f.article_id for f in findings
        if f.attention_level in (AttentionLevel.PRIORITY, AttentionLevel.HIGH)
    ]
    articulation_gaps = [
        f.article_id for f in findings
        if f.coverage == SituationType.ARTICULATION_GAP
    ]
    amendment_2024_gaps = [
        f.article_id for f in findings if f.is_2024_gap
    ]

    return BlockScore(
        block=block,
        score=score,
        findings=findings,
        gaps=gaps,
        articulation_gaps=articulation_gaps,
        amendment_2024_gaps=amendment_2024_gaps,
        rationale=parsed.get("intersectorality_note", ""),
    )
