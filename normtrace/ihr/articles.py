"""
normtrace/ihr/articles.py

Formal representation of the 29 IHR provisions selected for normative analysis.
Each article is a data object carrying the analytical criteria that determine
how it is assessed. The selection criterion and the four-link enablement chain
are encoded here as structured data, not as narrative in a prompt.

The LLM receives these structures as context when building analytical prompts.
It does not determine which articles are selected or what tests apply to each.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Block(str, Enum):
    """Thematic analytical blocks grouping IHR provisions by subject matter."""
    A = "A"  # Institutional architecture
    B = "B"  # Core capacities
    C = "C"  # Points of entry
    D = "D"  # Measures on persons and goods
    E = "E"  # Data and documents
    F = "F"  # Additional measures and accountability
    G = "G"  # Inverse compatibility check


class SelectionTest(str, Enum):
    """
    The six tests that determine whether an IHR provision requires an express
    domestic legal basis. A provision is selected when it triggers at least one.

    Grounded in the principle of legality as expressed in:
      - Vedel & Delvolvé (1992), principe de legalite
      - García de Enterría & Fernández (2020), principio de legalidad
      - Merkl (1931), Gesetzmässigkeit der Verwaltung
      - Dicey (1885), rule of law
    """
    COERCIVE_MEASURE = "coercive_measure"
    # Provision authorises or requires application of coercive measures
    # restricting the rights of private persons (quarantine, denial of entry,
    # detention of conveyances, compulsory medical examination).

    ACTOR_DESIGNATION = "actor_designation"
    # Provision requires designation of a specific institutional actor
    # with a defined mandate. A general ministerial mandate is insufficient.

    PERSONAL_DATA = "personal_data"
    # Provision requires sharing, restricting, or processing personal health data.
    # Domestic data protection law typically requires a statutory exception clause.

    PRIVATE_PARTY_OBLIGATION = "private_party_obligation"
    # Provision imposes obligations on private parties (carriers, operators,
    # healthcare providers). International treaty obligations do not bind
    # private parties directly; domestic transposition is required.

    INTERSECTORAL_COORDINATION = "intersectoral_coordination"
    # Provision requires binding coordination across institutions with distinct
    # statutory mandates. Protocol or MOU is insufficient where mandates conflict.

    INVERSE_COMPATIBILITY = "inverse_compatibility"
    # Provision limits or prohibits State action. Existing domestic law must
    # not contradict this prohibition. This is a check for over-legislation
    # rather than under-legislation.


class NormRank(str, Enum):
    """
    Minimum normative rank required to satisfy the provision, derived from the
    reserve of law doctrine (réserve de loi / Vorbehalt des Gesetzes / reserva de ley).
    See García de Enterría & Fernández (2020), ch. 4; Vedel & Delvolvé (1992), ch. 6.
    """
    STATUTE = "statute"
    # Formal legislation enacted by the legislature. Required when the provision
    # involves restriction of fundamental rights or imposition of obligations
    # on private parties.

    EXECUTIVE_REGULATION = "executive_regulation"
    # Regulation issued by the executive under statutory authority. Acceptable
    # when the enabling statute exists and the regulation fills operational detail.

    ADMINISTRATIVE_ACT = "administrative_act"
    # Published administrative act with general and external binding effect.
    # Acceptable for actor designation where statute confers the relevant powers.

    ANY_BINDING_NORM = "any_binding_norm"
    # Any instrument in the formal legal hierarchy (statute, regulation, or act).
    # Used where the provision requires legal basis but the reserve of law
    # doctrine does not mandate parliamentary-level instrument specifically.


class AttentionLevel(str, Enum):
    """Classification of a gap's urgency for normative action."""
    PRIORITY = "priority"    # Exposure in a PHEIC scenario; no functional substitute
    HIGH = "high"            # Legally vulnerable; contestable in court
    MEDIUM = "medium"        # Covered but fragile; dependent on administrative practice
    LOW = "low"              # Covered; 2024 amendment update recommended


class SituationType(str, Enum):
    """Outcome categories for the coverage analysis of each provision."""
    COVERED = "covered"
    ARTICULATION_GAP = "articulation_gap"       # Pieces exist, no legal coordinator
    STRENGTHENING = "strengthening"             # Covered but could be more robust
    UPDATE_NEEDED = "update_needed"             # Pre-IHR 2005 norm, needs revision
    PRIORITY_ATTENTION = "priority_attention"   # No coverage found
    APPARENT_COVERAGE = "apparent_coverage"     # Instrument name misleads; content irrelevant
    INCOMPATIBILITY = "incompatibility"         # Existing norm contradicts IHR


@dataclass
class IHRArticle:
    """
    Formal representation of an IHR provision selected for normative analysis.
    This object carries all the analytical metadata needed to assess the provision
    and to build the LLM prompt for it. The LLM does not determine these values.
    """
    article_id: str                           # e.g. "4", "4bis", "31", "annex_1a"
    block: Block
    title: str                                # Short descriptive title
    obligation: str                           # What the State must do or enable
    selection_tests: list[SelectionTest]      # Which tests triggered selection
    minimum_norm_rank: NormRank
    sectors_to_search: list[str]              # Which sectors of domestic law to search
    ihr_text_reference: str                   # Direct quote or paraphrase from IHR text
    is_2024_amendment: bool = False           # True for provisions introduced in 2024
    notes: Optional[str] = None              # Methodological notes on this article


# ---------------------------------------------------------------------------
# The 29 selected provisions, as structured objects
# ---------------------------------------------------------------------------

SELECTED_ARTICLES: dict[str, IHRArticle] = {

    # BLOCK A -- Institutional architecture

    "4": IHRArticle(
        article_id="4",
        block=Block.A,
        title="National IHR Focal Point",
        obligation=(
            "Designate a National IHR Focal Point accessible at all times for"
            " communications with WHO Contact Points."
        ),
        selection_tests=[SelectionTest.ACTOR_DESIGNATION],
        minimum_norm_rank=NormRank.ADMINISTRATIVE_ACT,
        sectors_to_search=["health", "executive_organisation"],
        ihr_text_reference=(
            "Art. 4.1: Each State Party shall designate or establish a National IHR"
            " Focal Point and the authorities responsible within its respective"
            " jurisdiction for the implementation of health measures under these Regulations."
        ),
    ),

    "4bis": IHRArticle(
        article_id="4bis",
        block=Block.A,
        title="National IHR Authority (2024)",
        obligation=(
            "Designate or establish a National IHR Authority with an explicit"
            " intersectoral coordination mandate."
        ),
        selection_tests=[
            SelectionTest.ACTOR_DESIGNATION,
            SelectionTest.INTERSECTORAL_COORDINATION,
        ],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "executive_organisation", "civil_protection"],
        ihr_text_reference=(
            "Art. 4.2bis (2024): States Parties shall take measures to implement"
            " paragraphs 1, 1bis and 2 of this Article, including, as appropriate,"
            " adjusting their domestic legislative and/or administrative arrangements."
        ),
        is_2024_amendment=True,
        notes=(
            "This is the only IHR provision that explicitly names domestic legislative"
            " adjustment as a required response. It serves as an interpretive anchor"
            " for the application of the selection criterion across all other provisions."
        ),
    ),

    "6": IHRArticle(
        article_id="6",
        block=Block.A,
        title="Notification to WHO",
        obligation=(
            "Notify WHO of all events that may constitute a public health emergency"
            " of international concern within 24 hours of assessment."
        ),
        selection_tests=[
            SelectionTest.ACTOR_DESIGNATION,
            SelectionTest.INTERSECTORAL_COORDINATION,
            SelectionTest.PERSONAL_DATA,
        ],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "data_protection", "executive_organisation"],
        ihr_text_reference=(
            "Art. 6.1: Each State Party shall notify WHO, by the most efficient"
            " means of communication available, by way of the National IHR Focal"
            " Point, and within 24 hours of assessment of public health information..."
        ),
    ),

    "7": IHRArticle(
        article_id="7",
        block=Block.A,
        title="Information sharing during unexpected events",
        obligation=(
            "Share with WHO all available public health information on unexpected"
            " or unusual public health events."
        ),
        selection_tests=[
            SelectionTest.ACTOR_DESIGNATION,
            SelectionTest.PERSONAL_DATA,
        ],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "data_protection"],
        ihr_text_reference=(
            "Art. 7: If a State Party has evidence of an unexpected or unusual"
            " public health event within its territory... it shall provide to WHO"
            " all relevant public health information..."
        ),
    ),

    "10": IHRArticle(
        article_id="10",
        block=Block.A,
        title="Verification of information",
        obligation=(
            "Respond to WHO requests for verification of information within 24 hours."
        ),
        selection_tests=[SelectionTest.ACTOR_DESIGNATION],
        minimum_norm_rank=NormRank.ADMINISTRATIVE_ACT,
        sectors_to_search=["health", "executive_organisation"],
        ihr_text_reference=(
            "Art. 10.1: WHO shall request verification from the State Party in whose"
            " territory the event is allegedly occurring..."
        ),
    ),

    # BLOCK B -- Core capacities

    "5": IHRArticle(
        article_id="5",
        block=Block.B,
        title="Surveillance: mandatory notification chain",
        obligation=(
            "Develop, strengthen, and maintain core capacities for surveillance"
            " from community level to national level, with mandatory notification"
            " obligations covering all sectors of the health system."
        ),
        selection_tests=[
            SelectionTest.PRIVATE_PARTY_OBLIGATION,
            SelectionTest.ACTOR_DESIGNATION,
        ],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "animal_health", "laboratory"],
        ihr_text_reference=(
            "Art. 5.1 + Annex 1A: Each State Party shall develop, strengthen and"
            " maintain, as soon as possible but no later than five years from the"
            " entry into force of these Regulations for that State Party, the"
            " capacity to detect, assess, notify and report events..."
        ),
        notes=(
            "The notification chain from community to national level requires that"
            " private healthcare providers and laboratories be legally obligated to"
            " report. This obligation cannot rest on professional codes of conduct alone."
        ),
    ),

    "13": IHRArticle(
        article_id="13",
        block=Block.B,
        title="Public health response: intersectoral coordination",
        obligation=(
            "Develop and maintain public health response capacities, with binding"
            " intersectoral coordination across health, civil protection, and"
            " other relevant sectors."
        ),
        selection_tests=[
            SelectionTest.INTERSECTORAL_COORDINATION,
            SelectionTest.ACTOR_DESIGNATION,
        ],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "civil_protection", "armed_forces", "transport"],
        ihr_text_reference=(
            "Art. 13.1 + Annex 1A: Each State Party shall develop, strengthen and"
            " maintain... the capacity to respond promptly and effectively to public"
            " health risks and public health emergencies of international concern."
        ),
    ),

    "46": IHRArticle(
        article_id="46",
        block=Block.B,
        title="Transport of biological substances",
        obligation=(
            "Facilitate transport of biological substances, diagnostic specimens,"
            " and reagents across borders for verification purposes."
        ),
        selection_tests=[SelectionTest.PRIVATE_PARTY_OBLIGATION],
        minimum_norm_rank=NormRank.EXECUTIVE_REGULATION,
        sectors_to_search=["health", "customs", "biosafety"],
        ihr_text_reference=(
            "Art. 46: States Parties shall, subject to national law and taking into"
            " account relevant international guidelines, facilitate the transport,"
            " entry, exit, processing and disposal of biological substances..."
        ),
    ),

    # BLOCK C -- Points of entry

    "19": IHRArticle(
        article_id="19",
        block=Block.C,
        title="General obligations at points of entry",
        obligation=(
            "Designate points of entry and assign competent sanitary authorities"
            " with IHR responsibilities at each designated point."
        ),
        selection_tests=[
            SelectionTest.ACTOR_DESIGNATION,
            SelectionTest.INTERSECTORAL_COORDINATION,
        ],
        minimum_norm_rank=NormRank.ADMINISTRATIVE_ACT,
        sectors_to_search=["health", "migration", "customs", "aviation", "ports"],
        ihr_text_reference=(
            "Art. 19: Each State Party shall... designate the airports, ports and"
            " ground crossings which shall develop the capacities provided in"
            " Annex 1B... and appoint competent authorities at each..."
        ),
    ),

    "20": IHRArticle(
        article_id="20",
        block=Block.C,
        title="Airports and ports: designated capacities",
        obligation=(
            "Ensure designated airports and ports develop and maintain the core"
            " capacities specified in Annex 1B."
        ),
        selection_tests=[
            SelectionTest.ACTOR_DESIGNATION,
            SelectionTest.PRIVATE_PARTY_OBLIGATION,
        ],
        minimum_norm_rank=NormRank.EXECUTIVE_REGULATION,
        sectors_to_search=["health", "aviation", "ports"],
        ihr_text_reference="Art. 20 + Annex 1B.",
    ),

    "21": IHRArticle(
        article_id="21",
        block=Block.C,
        title="Health measures at points of entry",
        obligation=(
            "Authorise competent authorities to apply health measures to conveyances,"
            " cargo, containers, and goods, including inspection, quarantine, and"
            " decontamination."
        ),
        selection_tests=[
            SelectionTest.COERCIVE_MEASURE,
            SelectionTest.ACTOR_DESIGNATION,
        ],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "customs", "aviation", "maritime", "ports"],
        ihr_text_reference=(
            "Art. 21: The competent authority shall... take measures to control or"
            " prevent the spread of disease, including inspection, quarantine,"
            " isolation, decontamination, disinsection, disinfection..."
        ),
    ),

    "22": IHRArticle(
        article_id="22",
        block=Block.C,
        title="Operator obligations: notification before arrival",
        obligation=(
            "Impose on operators of conveyances (aircraft, ships, land transport)"
            " the obligation to report cases of illness and health conditions"
            " before arrival at a point of entry."
        ),
        selection_tests=[SelectionTest.PRIVATE_PARTY_OBLIGATION],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["aviation", "maritime", "transport"],
        ihr_text_reference=(
            "Art. 22: The operator of a conveyance shall report to the competent"
            " authority... any suspected case or death on board..."
        ),
        notes=(
            "Aviation law and maritime law must each impose this obligation on"
            " carriers. A general health regulation is insufficient because carriers"
            " are private parties regulated under sectoral transport law."
        ),
    ),

    "28": IHRArticle(
        article_id="28",
        block=Block.C,
        title="Ships and aircraft: free pratique and health declarations",
        obligation=(
            "Establish legal instruments for free pratique, the Maritime Declaration"
            " of Health, and the Health Part of the Aircraft General Declaration."
        ),
        selection_tests=[
            SelectionTest.PRIVATE_PARTY_OBLIGATION,
            SelectionTest.ACTOR_DESIGNATION,
        ],
        minimum_norm_rank=NormRank.EXECUTIVE_REGULATION,
        sectors_to_search=["maritime", "aviation", "health", "ports"],
        ihr_text_reference="Art. 28 + Annexes 1B, 8.",
    ),

    "29": IHRArticle(
        article_id="29",
        block=Block.C,
        title="Civilian and non-military vessels and aircraft",
        obligation=(
            "Apply IHR health measures to civilian vessels and aircraft, with"
            " designated competent authority at each point of entry."
        ),
        selection_tests=[SelectionTest.ACTOR_DESIGNATION],
        minimum_norm_rank=NormRank.ADMINISTRATIVE_ACT,
        sectors_to_search=["maritime", "aviation", "health"],
        ihr_text_reference="Art. 29.",
    ),

    # BLOCK D -- Measures on persons and goods

    "23": IHRArticle(
        article_id="23",
        block=Block.D,
        title="Health measures and information on arrival and departure",
        obligation=(
            "Authorise competent authorities to require travellers to provide"
            " health information and to undergo medical examination."
        ),
        selection_tests=[
            SelectionTest.COERCIVE_MEASURE,
            SelectionTest.INTERSECTORAL_COORDINATION,
        ],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "migration"],
        ihr_text_reference=(
            "Art. 23.1: The competent authority may require travellers... to provide"
            " information on their itinerary and destination, provide contact"
            " information, and undergo non-invasive medical examination..."
        ),
    ),

    "24": IHRArticle(
        article_id="24",
        block=Block.D,
        title="Obligations of operators of conveyances",
        obligation=(
            "Impose obligations on conveyance operators regarding health measures,"
            " implementation of health controls, and cooperation with competent authorities."
        ),
        selection_tests=[SelectionTest.PRIVATE_PARTY_OBLIGATION],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["aviation", "maritime", "transport"],
        ihr_text_reference="Art. 24.",
    ),

    "27": IHRArticle(
        article_id="27",
        block=Block.D,
        title="Affected conveyances",
        obligation=(
            "Authorise application of health measures to affected conveyances,"
            " including decontamination and disinsection at the operator's expense."
        ),
        selection_tests=[
            SelectionTest.COERCIVE_MEASURE,
            SelectionTest.PRIVATE_PARTY_OBLIGATION,
        ],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "aviation", "maritime", "customs"],
        ihr_text_reference="Art. 27.",
    ),

    "30": IHRArticle(
        article_id="30",
        block=Block.D,
        title="Travellers under public health surveillance",
        obligation=(
            "Establish a legal basis for placing travellers under public health"
            " observation, with documented procedures for surveillance and contact."
        ),
        selection_tests=[SelectionTest.COERCIVE_MEASURE],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "migration"],
        ihr_text_reference="Art. 30.",
    ),

    "31": IHRArticle(
        article_id="31",
        block=Block.D,
        title="Health measures applicable to travellers",
        obligation=(
            "Establish a statutory basis for compulsory health measures applicable"
            " to travellers, including medical examination, vaccination, prophylaxis,"
            " and quarantine."
        ),
        selection_tests=[SelectionTest.COERCIVE_MEASURE],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "migration"],
        ihr_text_reference=(
            "Art. 31.2: When evidence of an imminent public health risk is found,"
            " the State Party may, in accordance with its national legislation and"
            " to the extent necessary to control such a risk, compel the traveller..."
        ),
        notes=(
            "The phrase 'in accordance with its national legislation' makes this the"
            " most explicit self-limiting provision in the IHR. Domestic statutory"
            " basis is a textual condition of the power's existence, not merely a"
            " procedural constraint on its exercise."
        ),
    ),

    "32": IHRArticle(
        article_id="32",
        block=Block.D,
        title="Treatment of travellers under health measures",
        obligation=(
            "Ensure travellers subjected to health measures receive dignified treatment,"
            " including access to food, water, accommodation, and consular assistance."
        ),
        selection_tests=[SelectionTest.COERCIVE_MEASURE],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "migration"],
        ihr_text_reference="Art. 32.",
    ),

    "42": IHRArticle(
        article_id="42",
        block=Block.D,
        title="Implementation of health measures",
        obligation=(
            "Apply health measures under the IHR in a transparent, non-discriminatory,"
            " and proportionate manner."
        ),
        selection_tests=[SelectionTest.COERCIVE_MEASURE],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health"],
        ihr_text_reference="Art. 42.",
    ),

    # BLOCK E -- Data and documents

    "45": IHRArticle(
        article_id="45",
        block=Block.E,
        title="Personal health data: protection and sharing",
        obligation=(
            "Ensure personal health data collected under the IHR is processed"
            " with confidentiality and shared with WHO only in a manner consistent"
            " with domestic data protection law."
        ),
        selection_tests=[SelectionTest.PERSONAL_DATA],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "data_protection"],
        ihr_text_reference=(
            "Art. 45.1: Health information collected or received by a State Party"
            " pursuant to these Regulations from another State Party or from WHO"
            " which refers to an identified or identifiable person shall be kept"
            " confidential and processed anonymously..."
        ),
        notes=(
            "This provision creates a tension with Arts. 6, 7, and 10, which require"
            " data sharing with WHO. Domestic data protection law must contain an"
            " explicit statutory exception for IHR/PHEIC purposes, or this tension"
            " is unresolved."
        ),
    ),

    "36_39": IHRArticle(
        article_id="36_39",
        block=Block.E,
        title="Health documents and vaccination certificates",
        obligation=(
            "Designate authorities for issuing International Certificates of"
            " Vaccination and other IHR health documents."
        ),
        selection_tests=[SelectionTest.ACTOR_DESIGNATION],
        minimum_norm_rank=NormRank.ADMINISTRATIVE_ACT,
        sectors_to_search=["health", "migration"],
        ihr_text_reference="Arts. 36-39 + Annexes 6-7.",
    ),

    # BLOCK F -- Additional measures and accountability

    "43": IHRArticle(
        article_id="43",
        block=Block.F,
        title="Additional health measures",
        obligation=(
            "Where the State applies health measures beyond those recommended by"
            " WHO, ensure they have a scientific basis, are reported to WHO within"
            " 48 hours, and are reviewed every 90 days."
        ),
        selection_tests=[SelectionTest.COERCIVE_MEASURE],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "civil_protection"],
        ihr_text_reference=(
            "Art. 43: States Parties may implement health measures, in accordance"
            " with their national law and obligations under international law, that"
            " achieve the same or greater level of health protection than WHO"
            " recommendations, provided that such measures are otherwise consistent"
            " with these Regulations."
        ),
        notes=(
            "The 2024 amendments introduced a mandatory 90-day review cycle and"
            " a 48-hour notification obligation. Most existing domestic frameworks"
            " do not operationalise either of these requirements."
        ),
    ),

    "44bis": IHRArticle(
        article_id="44bis",
        block=Block.F,
        title="Access to health products during PHEICs (2024)",
        obligation=(
            "Establish mechanisms for timely and equitable access to health"
            " products (diagnostics, vaccines, therapeutics) during PHEICs."
        ),
        selection_tests=[
            SelectionTest.ACTOR_DESIGNATION,
            SelectionTest.PRIVATE_PARTY_OBLIGATION,
        ],
        minimum_norm_rank=NormRank.STATUTE,
        sectors_to_search=["health", "procurement", "customs"],
        ihr_text_reference=(
            "Art. 44bis (2024): States Parties shall collaborate with each other"
            " and with WHO, to the extent possible, to support access to and"
            " the financing of health products required for response to a PHEIC..."
        ),
        is_2024_amendment=True,
        notes=(
            "This provision has no antecedent in IHR 2005. Most domestic legal"
            " frameworks have no health product emergency procurement mechanism"
            " specifically linked to PHEIC declarations."
        ),
    ),

    "54": IHRArticle(
        article_id="54",
        block=Block.F,
        title="Reporting and accountability to WHO",
        obligation=(
            "Report periodically to WHO on the implementation of the IHR,"
            " including through the e-SPAR mechanism."
        ),
        selection_tests=[SelectionTest.ACTOR_DESIGNATION],
        minimum_norm_rank=NormRank.ADMINISTRATIVE_ACT,
        sectors_to_search=["health", "executive_organisation"],
        ihr_text_reference="Art. 54.",
    ),

    "54bis": IHRArticle(
        article_id="54bis",
        block=Block.F,
        title="Implementation review mechanism (2024)",
        obligation=(
            "Participate in a structured review of IHR implementation,"
            " including reporting to the legislature or equivalent accountability body."
        ),
        selection_tests=[SelectionTest.ACTOR_DESIGNATION],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "executive_organisation", "budget"],
        ihr_text_reference="Art. 54bis (2024).",
        is_2024_amendment=True,
    ),

    # BLOCK G -- Inverse compatibility check

    "25": IHRArticle(
        article_id="25",
        block=Block.G,
        title="Conveyances and goods in transit",
        obligation=(
            "Ensure domestic law does not impose additional health measures on"
            " conveyances or goods in transit unless there is demonstrated risk."
        ),
        selection_tests=[SelectionTest.INVERSE_COMPATIBILITY],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["customs", "health", "maritime", "aviation"],
        ihr_text_reference="Art. 25.",
    ),

    "33": IHRArticle(
        article_id="33",
        block=Block.G,
        title="Goods in transit",
        obligation=(
            "Ensure domestic law does not subject goods in transit to IHR health"
            " measures except in cases of evidence of contamination."
        ),
        selection_tests=[SelectionTest.INVERSE_COMPATIBILITY],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["customs", "health"],
        ihr_text_reference="Art. 33.",
    ),

    "40_41": IHRArticle(
        article_id="40_41",
        block=Block.G,
        title="Charges for health measures at points of entry",
        obligation=(
            "Ensure that charges for IHR health measures are non-discriminatory"
            " and limited to the cost of services rendered."
        ),
        selection_tests=[SelectionTest.INVERSE_COMPATIBILITY],
        minimum_norm_rank=NormRank.ANY_BINDING_NORM,
        sectors_to_search=["health", "customs", "migration", "aviation", "ports"],
        ihr_text_reference="Arts. 40-41.",
    ),
}


def get_block(block: Block) -> dict[str, IHRArticle]:
    """Return all articles belonging to a given block."""
    return {k: v for k, v in SELECTED_ARTICLES.items() if v.block == block}


def get_2024_amendments() -> dict[str, IHRArticle]:
    """Return articles introduced or substantially modified by the 2024 amendments."""
    return {k: v for k, v in SELECTED_ARTICLES.items() if v.is_2024_amendment}


def get_by_sector(sector: str) -> dict[str, IHRArticle]:
    """Return articles that require searching a given domestic law sector."""
    return {
        k: v for k, v in SELECTED_ARTICLES.items()
        if sector in v.sectors_to_search
    }


def get_by_test(test: SelectionTest) -> dict[str, IHRArticle]:
    """Return articles selected by a given test."""
    return {
        k: v for k, v in SELECTED_ARTICLES.items()
        if test in v.selection_tests
    }
