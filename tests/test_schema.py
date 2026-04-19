"""
tests/test_schema.py

Tests for LLM output schema validation.
These tests verify that the validator correctly accepts valid outputs
and rejects invalid ones before they enter the analysis pipeline.
"""

import pytest
from normtrace.ihr.schema import (
    validate_block_output,
    validate_article_finding,
    validate_and_parse_block,
    SchemaValidationError,
    ValidationResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_FINDING = {
    "article_id": "4",
    "coverage": "articulation_gap",
    "attention_level": "high",
    "chain": {
        "norm": "ok",
        "actor": "weak",
        "authority": "missing",
        "enforceability": "missing",
    },
    "instruments_searched": ["General Health Law", "Migration Law"],
    "sources_found": [{"name": "General Health Law", "article": "Art. 13"}],
    "finding_text": "The health law designates the Ministry of Health generally but does not confer specific IHR notification powers.",
    "is_2024_gap": False,
}

VALID_BLOCK_OUTPUT = {
    "block": "A",
    "articles": {
        "4": VALID_FINDING,
    },
    "intersectorality_note": "The health and migration laws do not reference each other in POE contexts.",
    "articulation_gaps": ["4"],
    "amendment_2024_gaps": [],
}


# ---------------------------------------------------------------------------
# validate_article_finding
# ---------------------------------------------------------------------------

class TestValidateArticleFinding:
    def test_valid_finding_passes(self):
        result = validate_article_finding(VALID_FINDING, "4")
        assert result.valid
        assert result.errors == []

    def test_missing_required_field(self):
        bad = dict(VALID_FINDING)
        del bad["coverage"]
        result = validate_article_finding(bad, "4")
        assert not result.valid
        assert any("coverage" in e for e in result.errors)

    def test_invalid_coverage_value(self):
        bad = dict(VALID_FINDING)
        bad["coverage"] = "complete_failure"
        result = validate_article_finding(bad, "4")
        assert not result.valid
        assert any("coverage" in e for e in result.errors)

    def test_invalid_attention_level(self):
        bad = dict(VALID_FINDING)
        bad["attention_level"] = "extreme"
        result = validate_article_finding(bad, "4")
        assert not result.valid

    def test_invalid_chain_value(self):
        bad = dict(VALID_FINDING)
        bad["chain"] = dict(VALID_FINDING["chain"])
        bad["chain"]["norm"] = "partially"
        result = validate_article_finding(bad, "4")
        assert not result.valid
        assert any("norm" in e for e in result.errors)

    def test_missing_chain_link(self):
        bad = dict(VALID_FINDING)
        bad["chain"] = {"norm": "ok", "actor": "ok", "authority": "ok"}
        result = validate_article_finding(bad, "4")
        assert not result.valid
        assert any("enforceability" in e for e in result.errors)

    def test_article_id_mismatch_is_warning_not_error(self):
        finding = dict(VALID_FINDING)
        finding["article_id"] = "6"
        result = validate_article_finding(finding, "4")
        assert result.valid
        assert any("article_id" in w for w in result.warnings)

    def test_sources_found_must_have_name(self):
        bad = dict(VALID_FINDING)
        bad["sources_found"] = [{"article": "Art. 1"}]
        result = validate_article_finding(bad, "4")
        assert not result.valid


# ---------------------------------------------------------------------------
# validate_block_output
# ---------------------------------------------------------------------------

class TestValidateBlockOutput:
    def test_valid_block_passes(self):
        result = validate_block_output(VALID_BLOCK_OUTPUT)
        assert result.valid

    def test_invalid_block_letter(self):
        bad = dict(VALID_BLOCK_OUTPUT)
        bad["block"] = "Z"
        result = validate_block_output(bad)
        assert not result.valid

    def test_missing_articles_key(self):
        bad = {k: v for k, v in VALID_BLOCK_OUTPUT.items() if k != "articles"}
        result = validate_block_output(bad)
        assert not result.valid

    def test_invalid_article_propagates(self):
        bad = dict(VALID_BLOCK_OUTPUT)
        bad_finding = dict(VALID_FINDING)
        del bad_finding["finding_text"]
        bad["articles"] = {"4": bad_finding}
        result = validate_block_output(bad)
        assert not result.valid

    def test_missing_optional_fields_are_warnings(self):
        minimal = {
            "block": "A",
            "articles": {"4": VALID_FINDING},
        }
        result = validate_block_output(minimal)
        assert result.valid
        assert len(result.warnings) > 0


# ---------------------------------------------------------------------------
# validate_and_parse_block
# ---------------------------------------------------------------------------

class TestValidateAndParseBlock:
    def test_valid_json_string_parses(self):
        import json
        raw = json.dumps(VALID_BLOCK_OUTPUT)
        parsed, result = validate_and_parse_block(raw)
        assert result.valid
        assert parsed["block"] == "A"

    def test_json_with_preamble_strips_cleanly(self):
        import json
        raw = "Here is the analysis:\n" + json.dumps(VALID_BLOCK_OUTPUT) + "\nEnd."
        parsed, result = validate_and_parse_block(raw)
        assert result.valid

    def test_invalid_json_raises(self):
        with pytest.raises(SchemaValidationError):
            validate_and_parse_block("not json at all")

    def test_valid_json_but_invalid_schema_raises(self):
        import json
        bad = dict(VALID_BLOCK_OUTPUT)
        bad["block"] = "INVALID"
        with pytest.raises(SchemaValidationError):
            validate_and_parse_block(json.dumps(bad))

    def test_error_message_lists_all_violations(self):
        import json
        bad_finding = {
            "article_id": "4",
            "coverage": "not_a_real_type",
            "attention_level": "not_real",
            "chain": {"norm": "ok"},
            "instruments_searched": [],
            "sources_found": [],
            "finding_text": "ok",
        }
        bad = {
            "block": "A",
            "articles": {"4": bad_finding},
        }
        try:
            validate_and_parse_block(json.dumps(bad))
            assert False, "Should have raised"
        except SchemaValidationError as exc:
            assert len(exc.errors) >= 2
