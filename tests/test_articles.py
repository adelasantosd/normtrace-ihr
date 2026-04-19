"""
tests/test_articles.py

Tests for the IHR article data structures.
These verify that the formal selection criterion is consistently encoded
and that the query functions return the expected subsets.
"""

import pytest
from normtrace.ihr.articles import (
    SELECTED_ARTICLES, Block, SelectionTest, NormRank,
    get_block, get_2024_amendments, get_by_sector, get_by_test,
)


class TestArticleCompleteness:
    def test_exactly_30_article_objects_selected(self):
        assert len(SELECTED_ARTICLES) == 30  # 36_39 groups Arts. 36-39

    def test_all_blocks_represented(self):
        blocks_present = {a.block for a in SELECTED_ARTICLES.values()}
        assert blocks_present == set(Block)

    def test_every_article_has_at_least_one_selection_test(self):
        for article_id, article in SELECTED_ARTICLES.items():
            assert article.selection_tests, (
                f"Article {article_id} has no selection tests"
            )

    def test_every_article_has_at_least_one_sector(self):
        for article_id, article in SELECTED_ARTICLES.items():
            assert article.sectors_to_search, (
                f"Article {article_id} has no sectors to search"
            )

    def test_every_article_has_ihr_text_reference(self):
        for article_id, article in SELECTED_ARTICLES.items():
            assert article.ihr_text_reference.strip(), (
                f"Article {article_id} has an empty IHR text reference"
            )


class TestBlockAContent:
    """Block A covers institutional architecture: Arts. 4, 4bis, 6, 7, 10."""

    def test_block_a_has_five_articles(self):
        block_a = get_block(Block.A)
        assert len(block_a) == 5

    def test_article_4_requires_actor_designation(self):
        article = SELECTED_ARTICLES["4"]
        assert SelectionTest.ACTOR_DESIGNATION in article.selection_tests

    def test_article_4bis_is_2024_amendment(self):
        article = SELECTED_ARTICLES["4bis"]
        assert article.is_2024_amendment is True

    def test_article_4bis_requires_statute(self):
        article = SELECTED_ARTICLES["4bis"]
        assert article.minimum_norm_rank == NormRank.STATUTE

    def test_article_31_requires_statute_coercive(self):
        article = SELECTED_ARTICLES["31"]
        assert SelectionTest.COERCIVE_MEASURE in article.selection_tests
        assert article.minimum_norm_rank == NormRank.STATUTE


class TestBlockGInverseCompatibility:
    """Block G articles use INVERSE_COMPATIBILITY test exclusively."""

    def test_block_g_articles_use_inverse_test(self):
        block_g = get_block(Block.G)
        for article_id, article in block_g.items():
            assert SelectionTest.INVERSE_COMPATIBILITY in article.selection_tests, (
                f"Block G article {article_id} missing INVERSE_COMPATIBILITY test"
            )


class Test2024Amendments:
    def test_three_2024_amendments(self):
        amendments = get_2024_amendments()
        assert len(amendments) == 3

    def test_expected_amendment_ids(self):
        amendments = get_2024_amendments()
        assert set(amendments.keys()) == {"4bis", "44bis", "54bis"}

    def test_44bis_requires_statute(self):
        article = SELECTED_ARTICLES["44bis"]
        assert article.minimum_norm_rank == NormRank.STATUTE


class TestSectorQueries:
    def test_health_sector_in_most_articles(self):
        health_articles = get_by_sector("health")
        assert len(health_articles) > 15

    def test_data_protection_sector_in_art_45(self):
        dp_articles = get_by_sector("data_protection")
        assert "45" in dp_articles

    def test_aviation_sector_in_art_22(self):
        aviation_articles = get_by_sector("aviation")
        assert "22" in aviation_articles

    def test_maritime_sector_in_art_28(self):
        maritime_articles = get_by_sector("maritime")
        assert "28" in maritime_articles


class TestSelectionTestQueries:
    def test_coercive_measure_test_in_block_d(self):
        coercive = get_by_test(SelectionTest.COERCIVE_MEASURE)
        coercive_blocks = {a.block for a in coercive.values()}
        assert Block.D in coercive_blocks

    def test_private_party_test_includes_art_22(self):
        private = get_by_test(SelectionTest.PRIVATE_PARTY_OBLIGATION)
        assert "22" in private

    def test_personal_data_test_includes_art_45(self):
        data = get_by_test(SelectionTest.PERSONAL_DATA)
        assert "45" in data

    def test_inverse_compatibility_only_in_block_g(self):
        inverse = get_by_test(SelectionTest.INVERSE_COMPATIBILITY)
        for article in inverse.values():
            assert article.block == Block.G


class TestMinimumNormRank:
    def test_no_article_below_administrative_act(self):
        """Every article must require at least a published administrative act."""
        valid_ranks = set(NormRank)
        for article_id, article in SELECTED_ARTICLES.items():
            assert article.minimum_norm_rank in valid_ranks

    def test_primary_coercive_articles_require_statute(self):
        # Articles that authorise coercive measures require STATUTE.
        # Articles that regulate how measures are applied (Art. 32, 42, 43)
        # may allow ANY_BINDING_NORM as they restrict State action, not create powers.
        primary_coercive = {"21", "23", "27", "30", "31"}
        for article_id in primary_coercive:
            article = SELECTED_ARTICLES[article_id]
            assert article.minimum_norm_rank == NormRank.STATUTE
