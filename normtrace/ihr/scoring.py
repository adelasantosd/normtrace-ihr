"""
normtrace/ihr/scoring.py

C1 normative scoring engine.

All functions here are pure: they take structured data and return a score.
No LLM is involved. The LLM provides the findings dictionary; this module
computes the score from those findings.

The scoring rubric is calibrated to the WHO e-SPAR 1-5 scale for Core
Capacity 1 (Legislation, Policy and Financing), to allow direct comparison.
See: WHO e-SPAR, https://extranet.who.int/e-spar
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from normtrace.ihr.articles import Block, SituationType, AttentionLevel


# ---------------------------------------------------------------------------
# Score descriptors
# ---------------------------------------------------------------------------

SCORE_DESCRIPTORS: dict[int, str] = {
    5: (
        "Express norm of appropriate rank; actor designated with specific IHR mandate;"
        " authority explicitly conferred; enforceability mechanism present;"
        " preparedness financing mandated rather than discretionary."
    ),
    4: (
        "Express norm with designated actor; partial enforceability or contingent"
        " financing; minor gaps in intersectoral coordination."
    ),
    3: (
        "General applicable norm; actor inferred from general mandate; no explicit"
        " intersectoral coordination instrument; coordination administrative only."
    ),
    2: (
        "Partial or outdated sectoral norm (pre-IHR 2005); actor without specific"
        " IHR mandate; coordination by protocol without statutory basis."
    ),
    1: (
        "No domestic normative basis; reliance on IHR promulgation decree as"
        " self-executing norm without domestic institutional infrastructure."
    ),
}

# Weights for the five C1 indicators, matching e-SPAR methodology
C1_WEIGHTS: dict[str, float] = {
    "c1_1_legislation": 0.30,
    "c1_2_financing": 0.20,
    "c1_3_coordination": 0.25,
    "c1_4_preparedness": 0.15,
    "c1_5_accountability": 0.10,
}


@dataclass
class ChainAssessment:
    """
    Assessment of the four-link enablement chain for a single provision.
    Each link is: 'ok', 'weak', or 'missing'.
    """
    norm: str
    actor: str
    authority: str
    enforceability: str

    def is_complete(self) -> bool:
        return all(
            v == "ok"
            for v in [self.norm, self.actor, self.authority, self.enforceability]
        )

    def weakest_link(self) -> str:
        """Returns 'missing' if any link is missing, 'weak' if any is weak, else 'ok'."""
        values = [self.norm, self.actor, self.authority, self.enforceability]
        if "missing" in values:
            return "missing"
        if "weak" in values:
            return "weak"
        return "ok"

    def broken_links(self) -> list[str]:
        names = ["norm", "actor", "authority", "enforceability"]
        values = [self.norm, self.actor, self.authority, self.enforceability]
        return [n for n, v in zip(names, values) if v != "ok"]


@dataclass
class ArticleFinding:
    """
    Normalised finding for a single IHR article, produced by LLM extraction
    and validated by the schema checker before being accepted.
    """
    article_id: str
    block: Block
    coverage: SituationType
    attention_level: AttentionLevel
    chain: ChainAssessment
    instruments_searched: list[str]
    sources_found: list[dict]   # [{name, article, url}]
    finding_text: str
    is_2024_gap: bool = False


@dataclass
class BlockScore:
    """Aggregated score for a single block, derived from its article findings."""
    block: Block
    score: int                          # 1-5
    findings: list[ArticleFinding]
    gaps: list[str]                     # article_ids with priority or high attention
    articulation_gaps: list[str]        # article_ids with dispersed coverage
    amendment_2024_gaps: list[str]      # article_ids with 2024-specific gaps
    rationale: str


@dataclass
class C1Score:
    """
    Full C1 normative score for one analysis.
    Computed from block scores; comparable with e-SPAR.
    """
    c1_1_legislation: int
    c1_2_financing: int
    c1_3_coordination: int
    c1_4_preparedness: int
    c1_5_accountability: int
    total_weighted: float
    weak_link_applied: bool
    espar_score: Optional[int]
    espar_reference_date: Optional[str]
    delta: Optional[float]

    @property
    def indicators(self) -> dict[str, int]:
        return {
            "c1_1_legislation": self.c1_1_legislation,
            "c1_2_financing": self.c1_2_financing,
            "c1_3_coordination": self.c1_3_coordination,
            "c1_4_preparedness": self.c1_4_preparedness,
            "c1_5_accountability": self.c1_5_accountability,
        }

    def overreporting_detected(self) -> bool:
        if self.delta is None:
            return False
        return self.delta > 0.5

    def summary(self) -> str:
        lines = [
            f"C1 normative score: {self.total_weighted:.2f} / 5",
        ]
        if self.espar_score:
            lines.append(f"e-SPAR score: {self.espar_score} ({self.espar_reference_date})")
            sign = "+" if self.delta > 0 else ""
            lines.append(f"Delta: {sign}{self.delta:.1f}")
            if self.overreporting_detected():
                lines.append("Normative over-reporting detected.")
        if self.weak_link_applied:
            lines.append("Note: weak-link rule applied (one or more indicators = 1).")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pure scoring functions
# ---------------------------------------------------------------------------

def score_from_situation(situation: SituationType) -> int:
    """
    Derive a provisional score from the situation type of a finding.
    This is used as input to the indicator-level scoring, not as the final score.
    """
    mapping = {
        SituationType.COVERED: 5,
        SituationType.STRENGTHENING: 4,
        SituationType.UPDATE_NEEDED: 3,
        SituationType.ARTICULATION_GAP: 2,
        SituationType.APPARENT_COVERAGE: 2,
        SituationType.PRIORITY_ATTENTION: 1,
        SituationType.INCOMPATIBILITY: 1,
    }
    return mapping.get(situation, 1)


def derive_c1_indicators(
    block_scores: dict[Block, BlockScore]
) -> dict[str, int]:
    """
    Map block scores to C1 indicator scores.

    The mapping is grounded in the e-SPAR indicator definitions:
    - C1.1 Legislation: determined primarily by Blocks A, D, E
    - C1.2 Financing: determined by Block F (budget mandate)
    - C1.3 Coordination: determined by Blocks A, B, C
    - C1.4 Preparedness: determined by Blocks B, F
    - C1.5 Accountability: determined by Block F (reporting)
    """
    def block_score(b: Block) -> int:
        return block_scores[b].score if b in block_scores else 1

    c1_1 = min(
        block_score(Block.A),
        block_score(Block.D),
        block_score(Block.E),
    )
    c1_2 = block_score(Block.F)
    c1_3 = min(
        block_score(Block.A),
        block_score(Block.B),
        block_score(Block.C),
    )
    c1_4 = min(block_score(Block.B), block_score(Block.F))
    c1_5 = block_score(Block.F)

    return {
        "c1_1_legislation": c1_1,
        "c1_2_financing": c1_2,
        "c1_3_coordination": c1_3,
        "c1_4_preparedness": c1_4,
        "c1_5_accountability": c1_5,
    }


def apply_weak_link_rule(
    indicators: dict[str, int],
    weighted_total: float,
) -> tuple[float, bool]:
    """
    Apply the weak-link rule: if any single indicator scores 1,
    the weighted aggregate cannot exceed 2.5.

    Returns the (possibly adjusted) total and a flag indicating
    whether the rule was applied.

    Grounded in the administrative law principle that a broken link
    in the enablement chain makes the entire chain operationally unreliable.
    """
    if any(v == 1 for v in indicators.values()):
        return min(weighted_total, 2.5), True
    return weighted_total, False


def compute_weighted_total(indicators: dict[str, int]) -> float:
    """Compute the weighted C1 total from indicator scores."""
    return sum(
        indicators[k] * C1_WEIGHTS[k]
        for k in C1_WEIGHTS
        if k in indicators
    )


def compute_c1_score(
    block_scores: dict[Block, BlockScore],
    espar_score: Optional[int] = None,
    espar_reference_date: Optional[str] = None,
) -> C1Score:
    """
    Compute the full C1 normative score from block scores.
    This is the primary entry point for scoring.

    Parameters
    ----------
    block_scores:
        Dict mapping Block to BlockScore, as produced by the LLM extraction
        and validated by the schema checker.
    espar_score:
        The State Party's self-reported e-SPAR score for C1 (if available).
    espar_reference_date:
        The reference period of the e-SPAR score, e.g. '2024-Q3'.

    Returns
    -------
    C1Score
        Full score object with indicators, weighted total, and e-SPAR delta.
    """
    indicators = derive_c1_indicators(block_scores)
    weighted = compute_weighted_total(indicators)
    total, weak_link_applied = apply_weak_link_rule(indicators, weighted)

    delta = None
    if espar_score is not None:
        delta = round(espar_score - total, 2)

    return C1Score(
        c1_1_legislation=indicators["c1_1_legislation"],
        c1_2_financing=indicators["c1_2_financing"],
        c1_3_coordination=indicators["c1_3_coordination"],
        c1_4_preparedness=indicators["c1_4_preparedness"],
        c1_5_accountability=indicators["c1_5_accountability"],
        total_weighted=round(total, 2),
        weak_link_applied=weak_link_applied,
        espar_score=espar_score,
        espar_reference_date=espar_reference_date,
        delta=delta,
    )


def score_block(findings: list[ArticleFinding]) -> int:
    """
    Derive a block-level score (1-5) from a list of article findings.
    Uses the minimum score across all findings in the block, reflecting
    the weak-link logic at the block level.
    """
    if not findings:
        return 1
    scores = [score_from_situation(f.coverage) for f in findings]
    return min(scores)
