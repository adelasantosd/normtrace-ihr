# NormTrace-IHR: Module API Reference

**normtrace**, Version 1.0.0

---

## Overview

The `normtrace` package encodes the analytical framework for NormTrace-IHR.
The LLM is used as an extraction engine; the framework lives in this package.
All scoring is done by pure Python functions. The LLM cannot alter what is
analysed, what categories are available, or how scores are computed.

```
normtrace/
├── ihr/
│   ├── articles.py   IHR article objects with selection criteria
│   ├── scoring.py    C1 scoring engine (pure functions)
│   ├── prompts.py    Prompt construction from article objects
│   └── schema.py     LLM output validation
└── references/
    ├── legal_theory.yaml   Administrative law sources (YAML)
    └── references.bib      Same sources in BibTeX
```

---

## normtrace.ihr.articles

### `SELECTED_ARTICLES: dict[str, IHRArticle]`

Dictionary mapping article IDs to `IHRArticle` objects.
Contains 30 objects covering 29 IHR provisions (Arts. 36-39 grouped).

```python
from normtrace.ihr.articles import SELECTED_ARTICLES

art = SELECTED_ARTICLES['31']
print(art.minimum_norm_rank)  # NormRank.STATUTE
```

---

### `class IHRArticle`

Formal representation of an IHR provision selected for normative analysis.

| Attribute | Type | Description |
|-----------|------|-------------|
| `article_id` | `str` | IHR article identifier, e.g. `"31"`, `"4bis"`, `"36_39"` |
| `block` | `Block` | Analytical block (A through G) |
| `title` | `str` | Short descriptive title |
| `obligation` | `str` | What the State must do or enable |
| `selection_tests` | `list[SelectionTest]` | Tests that triggered inclusion in the selected set |
| `minimum_norm_rank` | `NormRank` | Minimum domestic normative rank required |
| `sectors_to_search` | `list[str]` | Domestic law sectors to search for this provision |
| `ihr_text_reference` | `str` | Direct quote or paraphrase from IHR text |
| `is_2024_amendment` | `bool` | True for provisions introduced by 2024 amendments |
| `notes` | `Optional[str]` | Methodological notes |

---

### `class Block(str, Enum)`

Thematic blocks grouping IHR provisions.

| Value | Topic |
|-------|-------|
| `A` | Institutional architecture |
| `B` | Core capacities |
| `C` | Points of entry |
| `D` | Measures on persons and goods |
| `E` | Data and documents |
| `F` | Additional measures and accountability |
| `G` | Inverse compatibility check |

---

### `class SelectionTest(str, Enum)`

The six tests that determine whether an IHR provision requires an express
domestic legal basis. Grounded in the principle of legality (Vedel & Delvolvé
1992; García de Enterría & Fernández 2020; Merkl 1931).

| Value | Triggers inclusion when... |
|-------|---------------------------|
| `COERCIVE_MEASURE` | Provision authorises or requires coercive measures restricting private rights |
| `ACTOR_DESIGNATION` | Provision requires designation of a specific institutional actor |
| `PERSONAL_DATA` | Provision requires sharing, restricting, or processing personal health data |
| `PRIVATE_PARTY_OBLIGATION` | Provision imposes obligations on private parties |
| `INTERSECTORAL_COORDINATION` | Provision requires binding coordination across institutions with distinct mandates |
| `INVERSE_COMPATIBILITY` | Provision limits State action; domestic law must not contradict it |

---

### `class NormRank(str, Enum)`

Minimum domestic normative rank required, derived from the reserve of law
doctrine (réserve de loi, Vorbehalt des Gesetzes, reserva de ley).

| Value | Description |
|-------|-------------|
| `STATUTE` | Formal legislation enacted by the legislature |
| `EXECUTIVE_REGULATION` | Regulation issued by the executive under statutory authority |
| `ADMINISTRATIVE_ACT` | Published administrative act with general binding effect |
| `ANY_BINDING_NORM` | Any instrument in the formal legal hierarchy |

---

### Query functions

```python
get_block(block: Block) -> dict[str, IHRArticle]
```
Returns all articles belonging to a given block.

```python
get_2024_amendments() -> dict[str, IHRArticle]
```
Returns articles introduced or substantially modified by the 2024 amendments.

```python
get_by_sector(sector: str) -> dict[str, IHRArticle]
```
Returns articles requiring search of a given domestic law sector.
Valid sectors: `health`, `migration`, `customs`, `aviation`, `maritime`,
`ports`, `animal_health`, `laboratory`, `biosafety`, `civil_protection`,
`armed_forces`, `transport`, `data_protection`, `budget`,
`executive_organisation`, `procurement`.

```python
get_by_test(test: SelectionTest) -> dict[str, IHRArticle]
```
Returns articles selected by a given test.

---

## normtrace.ihr.scoring

### `compute_c1_score`

```python
def compute_c1_score(
    block_scores: dict[Block, BlockScore],
    espar_score: Optional[int] = None,
    espar_reference_date: Optional[str] = None,
) -> C1Score
```

Primary entry point for C1 scoring. Derives indicator scores from block scores,
applies the weak-link rule, and computes the weighted total.

**Parameters**

- `block_scores`: Dict mapping each Block to a BlockScore, as produced by the
  LLM extraction pipeline and validated by the schema checker.
- `espar_score`: The State Party's self-reported e-SPAR score for C1, if available.
  Retrieve from `https://extranet.who.int/e-spar` with the consultation date recorded.
- `espar_reference_date`: Reference period, e.g. `"2024-Q3"`.

**Returns** `C1Score` with indicators, weighted total, weak-link flag, and delta.

---

### `class C1Score`

| Attribute | Type | Description |
|-----------|------|-------------|
| `c1_1_legislation` | `int` | Legislation indicator (1-5) |
| `c1_2_financing` | `int` | Financing indicator (1-5) |
| `c1_3_coordination` | `int` | Coordination indicator (1-5) |
| `c1_4_preparedness` | `int` | Preparedness indicator (1-5) |
| `c1_5_accountability` | `int` | Accountability indicator (1-5) |
| `total_weighted` | `float` | Weighted total after weak-link rule |
| `weak_link_applied` | `bool` | True if weak-link rule capped the total |
| `espar_score` | `Optional[int]` | e-SPAR self-reported score |
| `espar_reference_date` | `Optional[str]` | e-SPAR reference period |
| `delta` | `Optional[float]` | e-SPAR minus normative score (positive = over-reporting) |

**Methods**

- `overreporting_detected() -> bool`: True if delta > 0.5
- `summary() -> str`: Human-readable summary string
- `indicators -> dict[str, int]`: All five indicators as a dict

---

### C1 indicator weights

```python
C1_WEIGHTS: dict[str, float] = {
    'c1_1_legislation':   0.30,
    'c1_2_financing':     0.20,
    'c1_3_coordination':  0.25,
    'c1_4_preparedness':  0.15,
    'c1_5_accountability': 0.10,
}
```

---

### `apply_weak_link_rule`

```python
def apply_weak_link_rule(
    indicators: dict[str, int],
    weighted_total: float,
) -> tuple[float, bool]
```

If any indicator scores 1, the weighted total is capped at 2.5.
Returns the adjusted total and a flag indicating whether the rule was applied.

This encodes the principle that a broken link in the enablement chain makes
the whole chain operationally unreliable, regardless of the strength of
other links.

---

### `class ChainAssessment`

```python
@dataclass
class ChainAssessment:
    norm: str           # 'ok' | 'weak' | 'missing'
    actor: str
    authority: str
    enforceability: str
```

**Methods**

- `is_complete() -> bool`: True if all four links are 'ok'
- `weakest_link() -> str`: 'missing' > 'weak' > 'ok'
- `broken_links() -> list[str]`: Names of links that are not 'ok'

---

## normtrace.ihr.schema

### `validate_and_parse_block`

```python
def validate_and_parse_block(raw_json: str) -> tuple[dict, ValidationResult]
```

Parse and validate an LLM block output. Strips any text preceding the JSON object.

**Raises** `SchemaValidationError` if the output is structurally invalid or uses
values not defined in the article objects (coverage types, chain values).

**Returns** `(parsed_dict, validation_result)` on success.

---

### `SchemaValidationError`

```python
class SchemaValidationError(ValueError):
    errors: list[str]
```

Raised when LLM output fails validation. The `errors` attribute lists all
violations found, not just the first. This allows the calling code to
log all problems before deciding whether to retry the LLM call.

---

### `parse_block_result`

```python
def parse_block_result(parsed: dict) -> BlockScore
```

Convert a validated block output dict to a `BlockScore` object.
Calls `score_block()` internally; the score is computed from the findings,
not taken from any field in the LLM output.

---

## normtrace.ihr.prompts

### `build_system_prompt`

```python
def build_system_prompt(language: str = 'en') -> str
```

Build the system prompt for NormTrace-IHR analysis sessions.
The analytical framework is fixed; only the language instruction varies.
Valid values: `'en'`, `'es'`, `'fr'`.

---

### `build_corpus_discovery_prompt`

```python
def build_corpus_discovery_prompt(
    country_name: str,
    iso3: str,
    legal_system: str,
    is_federal: str,
    language: str = 'en',
) -> str
```

Build the corpus discovery prompt (Step 0-B). The sectors to search are
derived at call time from the `sectors_to_search` attributes of all article
objects. Changing the articles automatically changes what the discovery
prompt instructs the LLM to search.

---

### `build_block_prompt`

```python
def build_block_prompt(
    block: Block,
    country_name: str,
    corpus: list[dict],
    language: str = 'en',
) -> str
```

Build the analytical prompt for a single block. Article descriptions are
generated from `IHRArticle` objects, not from hardcoded strings. The
2024 amendment flag is automatically included for affected articles.

**`corpus`** is the list of validated corpus items (instruments confirmed
by the user), each as a dict with `name`, `type`, `sector`, `url`,
and `last_reform` keys.

---

### `build_scores_prompt`

```python
def build_scores_prompt(
    country_name: str,
    corpus: list[dict],
    block_results: dict[str, dict],
    language: str = 'en',
) -> str
```

Build the prompt for the SCORES block. Injects all block results as
structured context. Reform proposals in the output must use instrument
types consistent with the `minimum_norm_rank` of the relevant article.

---

### Output schemas

The expected JSON structure for LLM outputs is defined in:

```python
from normtrace.ihr.prompts import ARTICLE_FINDING_SCHEMA, BLOCK_RESULT_SCHEMA
```

These are JSON Schema objects that the validator in `schema.py` checks
outputs against. They are also injected into block prompts so the LLM
has the schema when generating its response.

---

## normtrace.references

### `legal_theory.yaml`

Machine-readable administrative law sources grounding the selection criterion.
Each entry has:

| Field | Description |
|-------|-------------|
| `id` | Unique identifier |
| `cite_key` | Matches key in `references.bib` |
| `author` | List of `{family, given}` or `{name}` dicts |
| `year` | Publication year |
| `title` | Work title |
| `tradition` | Legal traditions addressed |
| `doctrine` | Doctrines the work is cited for |
| `quote` | Key passage cited in methodology |
| `relevance` | How this source grounds the selection criterion |

```python
import yaml
with open('normtrace/references/legal_theory.yaml') as f:
    sources = yaml.safe_load(f)['sources']

# Query: sources grounding the reserve of law doctrine
reserve = [s for s in sources if any('reserva' in d or 'reserve' in d for d in s.get('doctrine', []))]
```

### `references.bib`

The same sources in BibTeX format. Compatible with Zenodo, Zotero, and all
standard citation managers. Import directly into your reference manager
to cite the sources underlying the NormTrace-IHR analytical framework.
