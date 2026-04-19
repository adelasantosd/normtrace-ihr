"""
tests/test_scoring.py

Tests for the C1 scoring engine.
All functions tested here are pure: no LLM, no network, no database.
"""

import pytest
from normtrace.ihr.articles import Block, SituationType, AttentionLevel
from normtrace.ihr.scoring import (
    ChainAssessment,
    ArticleFinding,
    BlockScore,
    compute_weighted_total,
    apply_weak_link_rule,
    score_from_situation,
    score_block,
    compute_c1_score,
    C1_WEIGHTS,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_finding(
    article_id: str,
    block: Block,
    coverage: SituationType,
    attention: AttentionLevel = AttentionLevel.MEDIUM,
    chain: dict = None,
) -> ArticleFinding:
    if chain is None:
        chain = {"norm": "ok", "actor": "ok", "authority": "ok", "enforceability": "ok"}
    return ArticleFinding(
        article_id=article_id,
        block=block,
        coverage=coverage,
        attention_level=attention,
        chain=ChainAssessment(**chain),
        instruments_searched=["Law A", "Law B"],
        sources_found=[{"name": "Law A", "article": "Art. 1"}],
        finding_text="Test finding.",
    )


def make_block_score(block: Block, score: int) -> BlockScore:
    return BlockScore(
        block=block,
        score=score,
        findings=[],
        gaps=[],
        articulation_gaps=[],
        amendment_2024_gaps=[],
        rationale="",
    )


# ---------------------------------------------------------------------------
# score_from_situation
# ---------------------------------------------------------------------------

class TestScoreFromSituation:
    def test_covered_returns_5(self):
        assert score_from_situation(SituationType.COVERED) == 5

    def test_strengthening_returns_4(self):
        assert score_from_situation(SituationType.STRENGTHENING) == 4

    def test_update_needed_returns_3(self):
        assert score_from_situation(SituationType.UPDATE_NEEDED) == 3

    def test_articulation_gap_returns_2(self):
        assert score_from_situation(SituationType.ARTICULATION_GAP) == 2

    def test_apparent_coverage_returns_2(self):
        assert score_from_situation(SituationType.APPARENT_COVERAGE) == 2

    def test_priority_attention_returns_1(self):
        assert score_from_situation(SituationType.PRIORITY_ATTENTION) == 1

    def test_incompatibility_returns_1(self):
        assert score_from_situation(SituationType.INCOMPATIBILITY) == 1


# ---------------------------------------------------------------------------
# score_block
# ---------------------------------------------------------------------------

class TestScoreBlock:
    def test_empty_findings_returns_1(self):
        assert score_block([]) == 1

    def test_all_covered_returns_5(self):
        findings = [
            make_finding("4", Block.A, SituationType.COVERED),
            make_finding("4bis", Block.A, SituationType.COVERED),
        ]
        assert score_block(findings) == 5

    def test_minimum_score_wins(self):
        findings = [
            make_finding("4", Block.A, SituationType.COVERED),
            make_finding("4bis", Block.A, SituationType.PRIORITY_ATTENTION),
        ]
        assert score_block(findings) == 1

    def test_mixed_returns_minimum(self):
        findings = [
            make_finding("4", Block.A, SituationType.COVERED),
            make_finding("6", Block.A, SituationType.ARTICULATION_GAP),
            make_finding("7", Block.A, SituationType.STRENGTHENING),
        ]
        assert score_block(findings) == 2


# ---------------------------------------------------------------------------
# ChainAssessment
# ---------------------------------------------------------------------------

class TestChainAssessment:
    def test_complete_chain(self):
        chain = ChainAssessment(norm="ok", actor="ok", authority="ok", enforceability="ok")
        assert chain.is_complete()
        assert chain.weakest_link() == "ok"
        assert chain.broken_links() == []

    def test_missing_link(self):
        chain = ChainAssessment(norm="ok", actor="missing", authority="ok", enforceability="ok")
        assert not chain.is_complete()
        assert chain.weakest_link() == "missing"
        assert chain.broken_links() == ["actor"]

    def test_weak_link(self):
        chain = ChainAssessment(norm="ok", actor="ok", authority="weak", enforceability="ok")
        assert not chain.is_complete()
        assert chain.weakest_link() == "weak"
        assert chain.broken_links() == ["authority"]

    def test_missing_takes_priority_over_weak(self):
        chain = ChainAssessment(norm="weak", actor="missing", authority="ok", enforceability="weak")
        assert chain.weakest_link() == "missing"
        assert sorted(chain.broken_links()) == sorted(["norm", "actor", "enforceability"])


# ---------------------------------------------------------------------------
# apply_weak_link_rule
# ---------------------------------------------------------------------------

class TestWeakLinkRule:
    def test_no_rule_needed(self):
        indicators = {
            "c1_1_legislation": 3, "c1_2_financing": 3,
            "c1_3_coordination": 3, "c1_4_preparedness": 3,
            "c1_5_accountability": 3,
        }
        result, applied = apply_weak_link_rule(indicators, 3.0)
        assert result == 3.0
        assert applied is False

    def test_rule_applied_caps_at_2_5(self):
        indicators = {
            "c1_1_legislation": 1, "c1_2_financing": 5,
            "c1_3_coordination": 5, "c1_4_preparedness": 5,
            "c1_5_accountability": 5,
        }
        high_total = 4.5
        result, applied = apply_weak_link_rule(indicators, high_total)
        assert result == 2.5
        assert applied is True

    def test_rule_does_not_raise_score(self):
        indicators = {
            "c1_1_legislation": 1, "c1_2_financing": 2,
            "c1_3_coordination": 1, "c1_4_preparedness": 1,
            "c1_5_accountability": 1,
        }
        low_total = 1.2
        result, applied = apply_weak_link_rule(indicators, low_total)
        assert result == 1.2
        assert applied is True


# ---------------------------------------------------------------------------
# compute_weighted_total
# ---------------------------------------------------------------------------

class TestComputeWeightedTotal:
    def test_all_fives(self):
        indicators = {k: 5 for k in C1_WEIGHTS}
        total = compute_weighted_total(indicators)
        assert abs(total - 5.0) < 0.001

    def test_all_ones(self):
        indicators = {k: 1 for k in C1_WEIGHTS}
        total = compute_weighted_total(indicators)
        assert abs(total - 1.0) < 0.001

    def test_weights_sum_to_one(self):
        assert abs(sum(C1_WEIGHTS.values()) - 1.0) < 0.001

    def test_known_values(self):
        indicators = {
            "c1_1_legislation": 2,
            "c1_2_financing": 1,
            "c1_3_coordination": 2,
            "c1_4_preparedness": 2,
            "c1_5_accountability": 1,
        }
        expected = (2*0.30) + (1*0.20) + (2*0.25) + (2*0.15) + (1*0.10)
        result = compute_weighted_total(indicators)
        assert abs(result - expected) < 0.001


# ---------------------------------------------------------------------------
# compute_c1_score (integration)
# ---------------------------------------------------------------------------

class TestComputeC1Score:
    def _all_blocks(self, score: int) -> dict:
        return {b: make_block_score(b, score) for b in Block}

    def test_all_covered_score_5(self):
        result = compute_c1_score(self._all_blocks(5))
        assert result.total_weighted == 5.0
        assert result.weak_link_applied is False

    def test_all_minimal_score_1(self):
        result = compute_c1_score(self._all_blocks(1))
        assert result.total_weighted == 1.0
        assert result.weak_link_applied is True

    def test_espar_delta_positive(self):
        result = compute_c1_score(
            self._all_blocks(2),
            espar_score=4,
            espar_reference_date="2024-Q3",
        )
        assert result.delta > 0
        assert result.overreporting_detected()

    def test_espar_delta_negative(self):
        result = compute_c1_score(
            self._all_blocks(4),
            espar_score=2,
            espar_reference_date="2024-Q3",
        )
        assert result.delta < 0
        assert not result.overreporting_detected()

    def test_weak_link_rule_in_full_computation(self):
        blocks = self._all_blocks(4)
        blocks[Block.F] = make_block_score(Block.F, 1)
        result = compute_c1_score(blocks)
        assert result.weak_link_applied is True
        assert result.total_weighted <= 2.5
