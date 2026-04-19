"""
normtrace/ihr/prompts.py

Prompt construction from structured data.

Prompts are not hardcoded strings. They are assembled from the article objects
in articles.py and the administrative law sources in references/legal_theory.yaml.
This means that changing a selection criterion in articles.py changes every prompt
that references that article, automatically and consistently.

The LLM receives prompts built by this module. It does not receive raw text
describing the methodology; it receives structured context derived from the
formal objects that encode the methodology.
"""

from __future__ import annotations

import json
from typing import Optional

from normtrace.ihr.articles import (
    SELECTED_ARTICLES, Block, IHRArticle, SelectionTest,
    get_block, get_2024_amendments
)


LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "en": (
        "Respond entirely in English. Use formal legal terminology appropriate"
        " for international public health law and comparative administrative law."
    ),
    "es": (
        "Responde completamente en español. Usa terminología jurídica formal"
        " apropiada para el derecho internacional de salud pública y el derecho"
        " administrativo comparado. Utiliza el estilo jurídico propio de los"
        " sistemas latinoamericanos y español."
    ),
    "fr": (
        "Réponds entièrement en français. Utilise une terminologie juridique formelle"
        " appropriée au droit international de la santé publique et au droit"
        " administratif comparé. Utilise le style juridique propre aux systèmes"
        " francophones de tradition romano-germanique."
    ),
}

# Output schema: the LLM must produce JSON matching this structure.
# The validator in schema.py checks that outputs conform to it.
ARTICLE_FINDING_SCHEMA = {
    "type": "object",
    "required": [
        "article_id", "coverage", "attention_level",
        "chain", "instruments_searched", "sources_found", "finding_text"
    ],
    "properties": {
        "article_id": {"type": "string"},
        "coverage": {
            "type": "string",
            "enum": [
                "covered", "articulation_gap", "strengthening",
                "update_needed", "priority_attention",
                "apparent_coverage", "incompatibility"
            ]
        },
        "attention_level": {
            "type": "string",
            "enum": ["priority", "high", "medium", "low"]
        },
        "chain": {
            "type": "object",
            "required": ["norm", "actor", "authority", "enforceability"],
            "properties": {
                "norm":           {"type": "string", "enum": ["ok", "weak", "missing"]},
                "actor":          {"type": "string", "enum": ["ok", "weak", "missing"]},
                "authority":      {"type": "string", "enum": ["ok", "weak", "missing"]},
                "enforceability": {"type": "string", "enum": ["ok", "weak", "missing"]},
            }
        },
        "instruments_searched": {"type": "array", "items": {"type": "string"}},
        "sources_found": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name":    {"type": "string"},
                    "article": {"type": "string"},
                    "url":     {"type": "string"},
                }
            }
        },
        "finding_text": {"type": "string"},
        "is_2024_gap":  {"type": "boolean"},
    }
}

BLOCK_RESULT_SCHEMA = {
    "type": "object",
    "required": ["block", "articles", "intersectorality_note", "articulation_gaps", "amendment_2024_gaps"],
    "properties": {
        "block": {"type": "string"},
        "articles": {
            "type": "object",
            "additionalProperties": ARTICLE_FINDING_SCHEMA
        },
        "intersectorality_note": {"type": "string"},
        "articulation_gaps":     {"type": "array", "items": {"type": "string"}},
        "amendment_2024_gaps":   {"type": "array", "items": {"type": "string"}},
    }
}


def _article_context(article: IHRArticle) -> str:
    """Format a single article object as structured context for the LLM."""
    tests = ", ".join(t.value for t in article.selection_tests)
    lines = [
        f"Article {article.article_id}: {article.title}",
        f"  Obligation: {article.obligation}",
        f"  Selection tests triggered: {tests}",
        f"  Minimum norm rank required: {article.minimum_norm_rank.value}",
        f"  Sectors to search: {', '.join(article.sectors_to_search)}",
        f"  IHR text: {article.ihr_text_reference}",
    ]
    if article.is_2024_amendment:
        lines.append("  Status: 2024 AMENDMENT -- this obligation may not yet be reflected in domestic law.")
    if article.notes:
        lines.append(f"  Methodological note: {article.notes}")
    return "\n".join(lines)


def _chain_instructions() -> str:
    return """
For each article, apply the four-link enablement chain across ALL instruments in the corpus:

  NORM: Does a legally binding instrument of appropriate rank exist?
    ok     = express statutory or regulatory basis, rank meets the minimum required
    weak   = general mandate applicable by inference; pre-IHR instrument; rank below minimum
    missing = no binding instrument found in corpus

  ACTOR: Is a specific institutional actor designated for this function?
    ok     = explicit designation in a published legal or administrative instrument
    weak   = designation implied from general mandate; no published instrument
    missing = no designated actor

  AUTHORITY: Is the actor explicitly conferred the power to take the required action?
    ok     = explicit power enumerated in a norm
    weak   = power implied from general mandate; contested scope
    missing = no express power found

  ENFORCEABILITY: Is there a mechanism to compel compliance and ensure accountability?
    ok     = sanctions for non-compliance by regulated parties; accountability mechanism
    weak   = sanctions exist but not specific to this function; accountability unclear
    missing = no enforcement mechanism found
"""


def build_system_prompt(language: str = "en") -> str:
    """
    Build the system prompt for NormTrace-IHR analysis sessions.
    Language instruction is injected; the analytical framework is fixed.
    """
    lang_instruction = LANGUAGE_INSTRUCTIONS.get(language, LANGUAGE_INSTRUCTIONS["en"])

    articles_summary = "\n".join(
        f"  [{a.block.value}] Art. {a.article_id}: {a.title}"
        for a in SELECTED_ARTICLES.values()
    )

    return f"""You are the analytical engine of NormTrace-IHR, a systematic tool for
assessing domestic legal implementation of the International Health Regulations
(IHR 2005 and 2024 amendments).

{lang_instruction}

Your role is extraction and assessment, not methodology design. The analytical
framework -- which articles are selected, what tests apply, what chain links are
required -- is defined in the code that builds this prompt. You apply that framework
to the instruments in the validated corpus.

The 29 IHR provisions selected for analysis are:
{articles_summary}

Selection criterion: provisions are included when they require an act of public
authority affecting private rights that cannot be activated by policy, protocol,
or institutional practice alone. The criterion is grounded in the principle of
legality (principe de legalite, principio de legalidad, Gesetzmassigkeit der
Verwaltung) and the reserve of law doctrine (reserve de loi, reserva de ley).

Coverage categories:
  covered           -- all four chain links present and robust
  articulation_gap  -- links exist across instruments but no legal coordinator
  strengthening     -- covered but could be made more robust
  update_needed     -- norm exists but predates IHR 2005 and needs revision
  priority_attention -- no coverage found in corpus
  apparent_coverage  -- instrument examined and found not applicable despite name
  incompatibility    -- existing norm contradicts an IHR prohibition

Tone: use constructive, opportunity-based language. Describe gaps as areas
that could benefit from normative attention, not as failures or violations.

Traceability: every finding must cite the specific instrument, article number,
and source URL where available. Without traceability the finding is not verifiable.
"""


def build_corpus_discovery_prompt(
    country_name: str,
    iso3: str,
    legal_system: str,
    is_federal: str,
    language: str = "en",
) -> str:
    """
    Build the corpus discovery prompt (Step 0-B).
    The sectors to search are derived from the article objects, not hardcoded.
    """
    all_sectors = sorted(set(
        sector
        for article in SELECTED_ARTICLES.values()
        for sector in article.sectors_to_search
    ))

    sector_list = "\n".join(f"  - {s}" for s in all_sectors)

    schema_json = json.dumps({
        "include": [{"name": "str", "instrument_type": "str", "sector": "str",
                     "url": "str", "last_reform_date": "str",
                     "last_reform_label": "str", "ihr_articles": "str",
                     "classification_reason": "str"}],
        "review":  [{"name": "str", "classification_reason": "str"}],
        "discard": [{"name": "str", "classification_reason": "str (note apparent coverage cases explicitly)"}],
        "lagunas": [{"name": "str", "classification_reason": "str"}],
    }, indent=2)

    return f"""Corpus discovery for {country_name} ({iso3}).

Legal system: {legal_system}
Federal structure: {is_federal}

The following sectors must be searched systematically. This list is derived
from the sectors_to_search attribute of the 29 selected IHR articles:

{sector_list}

For each sector, search:
1. The official legislative repository of {country_name}
2. Web sources for recent reforms not yet in official repositories
3. References in legal databases and secondary sources

For each instrument found, classify as:
  include  -- direct intersection with at least one of the 29 selected IHR provisions
  review   -- possible relevance; text examination needed to confirm
  discard  -- no intersection; document the reason (note 'apparent coverage' cases explicitly,
              where an instrument's name suggests relevance but its content does not engage
              any of the six selection tests)
  lagunas  -- instrument known to exist but text not obtained

Return only valid JSON in this exact structure:
{schema_json}

Be exhaustive. It is better to classify an instrument as 'review' than to omit it.
A discarded instrument with a documented reason is a valid analytical finding.
"""


def build_block_prompt(
    block: Block,
    country_name: str,
    corpus: list[dict],
    language: str = "en",
) -> str:
    """
    Build the analytical prompt for a single block.
    The article descriptions are generated from the IHRArticle objects,
    not from a hardcoded string.
    """
    articles = get_block(block)
    article_contexts = "\n\n".join(
        _article_context(a) for a in articles.values()
    )

    amendment_ids = [
        a.article_id for a in articles.values() if a.is_2024_amendment
    ]
    amendment_note = (
        f"\nNote: articles {', '.join(amendment_ids)} are 2024 amendments."
        " Flag explicitly if the corpus contains no instrument addressing these."
        if amendment_ids else ""
    )

    corpus_json = json.dumps(corpus, indent=2, ensure_ascii=False)
    schema_json = json.dumps(BLOCK_RESULT_SCHEMA, indent=2)

    return f"""Normative analysis -- Block {block.value} -- {country_name}

{_chain_instructions()}

Articles to analyse in this block:

{article_contexts}
{amendment_note}

Validated corpus (instruments confirmed by the user for inclusion):
{corpus_json}

Instructions:
1. For each article, search ALL instruments in the corpus before reaching a conclusion.
   Do not stop at the first instrument that appears to provide coverage.
2. Document which instruments were searched under instruments_searched, including
   those that were searched and found not applicable.
3. Identify intersectoral gaps: cases where links exist across instruments but
   no instrument coordinates them.
4. Note articulation_gaps separately from complete absences.
5. For 2024 amendments, flag explicitly even if IHR 2005 obligations are covered.

Return only valid JSON conforming exactly to this schema:
{schema_json}
"""


def build_scores_prompt(
    country_name: str,
    corpus: list[dict],
    block_results: dict[str, dict],
    language: str = "en",
) -> str:
    """
    Build the prompt for the SCORES block.
    Block results are injected as structured data.
    """
    blocks_json = json.dumps(block_results, indent=2, ensure_ascii=False)

    reform_schema = json.dumps({
        "priority": "high | medium | low",
        "instrument_recommended": "statute | executive_regulation | administrative_act | any_binding_norm",
        "instrument_reason": "why this instrument and not a lower-rank one",
        "ihr_article": "article_id",
        "current_gap": "description of the gap",
        "proposed_text": "draft provision or amendment",
        "lateral_effects": "impact on other instruments in the corpus",
        "viability": "technical | requires_sectoral_consultation | structural_reform",
    }, indent=2)

    return f"""Final scoring and reform proposals -- {country_name}

Block results:
{blocks_json}

Based on the block findings above, produce:

1. Reform proposals for each gap at priority or high attention level.
   For each proposal, the instrument_recommended must match the minimum_norm_rank
   of the IHR article being addressed. Do not recommend a lower-rank instrument
   where the reserve of law doctrine requires a statute.

   Each proposal must follow this structure:
   {reform_schema}

2. A main_finding: a 2-3 sentence synthesis of the country's overall normative
   situation with respect to IHR implementation. This should characterise the
   pattern of gaps (e.g. dispersed coverage without articulation, systematic
   absence in a sector, 2024 amendment gap only) rather than list all findings.

Return only valid JSON:
{{
  "reform_proposals": [...],
  "main_finding": "..."
}}
"""
