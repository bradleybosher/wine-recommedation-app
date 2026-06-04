"""Tests for backend.retrieval — tiered profile-signal ranking (no LLM)."""

from models import TasteProfile
from retrieval import rank_wine_list


def _make_profile(**kwargs) -> TasteProfile:
    return TasteProfile(**kwargs)


def _list_text(lines: list[str]) -> str:
    return "\n".join(lines)


class TestRankWineList:
    def test_noop_when_below_limit(self):
        wine_list = _list_text([f"Wine {i}" for i in range(10)])
        profile = _make_profile(preferred_grapes=["pinot noir"])
        assert rank_wine_list(wine_list, profile, limit=40) == wine_list

    def test_truncates_to_first_lines_when_no_positive_signals(self):
        # 50 generic lines, empty profile → first 40 retained, original order
        lines = [f"Wine {i:02d}" for i in range(50)]
        profile = _make_profile()
        result = rank_wine_list(_list_text(lines), profile, limit=40)
        result_lines = result.splitlines()
        assert len(result_lines) == 40
        assert result_lines[0] == "Wine 00"
        assert result_lines[-1] == "Wine 39"

    def test_producer_match_ranks_highest(self):
        # 50 lines, only one mentions the producer — it should appear in top results
        lines = [f"Generic Wine {i}" for i in range(49)] + ["Domaine Leroy Chambertin 2018"]
        profile = _make_profile(top_producers=["Domaine Leroy"])
        result = rank_wine_list(_list_text(lines), profile, limit=10)
        assert "Domaine Leroy Chambertin 2018" in result.splitlines()

    def test_grape_match_with_synonym_expansion(self):
        # Profile prefers "syrah" → should also match a line containing "shiraz"
        lines = [f"Filler wine {i}" for i in range(49)] + ["Penfolds Grange Shiraz 2015"]
        profile = _make_profile(preferred_grapes=["syrah"])
        result = rank_wine_list(_list_text(lines), profile, limit=10)
        assert "Penfolds Grange Shiraz 2015" in result.splitlines()

    def test_region_match_with_sub_appellation_expansion(self):
        # Profile prefers "burgundy" → should match a line for "Gevrey-Chambertin"
        lines = [f"Random Italian wine {i}" for i in range(49)] + ["Gevrey-Chambertin 1er Cru"]
        profile = _make_profile(preferred_regions=["burgundy"])
        result = rank_wine_list(_list_text(lines), profile, limit=10)
        assert "Gevrey-Chambertin 1er Cru" in result.splitlines()

    def test_avoided_token_penalises_match(self):
        # The avoided-token penalty (-2.0) should outweigh a grape match (+1.0),
        # dropping the oaky line below the clean preferred-grape line.
        lines = (
            [f"Filler {i}" for i in range(48)]
            + ["Heavily oaky California Pinot Noir 2020"]
            + ["Burgundian Pinot Noir 2018"]
        )
        profile = _make_profile(
            preferred_grapes=["pinot noir"],
            avoided_style_tokens=["oaky"],
        )
        result = rank_wine_list(_list_text(lines), profile, limit=10).splitlines()
        # Clean preferred match must appear; oaky-penalised line should be excluded
        # by the higher-scoring filler lines (baseline 0.25 beats -0.75 of the oaky line)
        assert "Burgundian Pinot Noir 2018" in result
        assert "Heavily oaky California Pinot Noir 2020" not in result

    def test_accent_insensitive_match(self):
        lines = [f"Filler {i}" for i in range(49)] + ["Côte-Rôtie La Mouline 2017"]
        profile = _make_profile(preferred_regions=["rhône"])
        result = rank_wine_list(_list_text(lines), profile, limit=5)
        assert "Côte-Rôtie La Mouline 2017" in result.splitlines()

    def test_empty_wine_list_returns_empty(self):
        profile = _make_profile(preferred_grapes=["pinot noir"])
        assert rank_wine_list("", profile, limit=40) == ""

    def test_malformed_lines_do_not_crash(self):
        # Lines without prices, mixed whitespace
        lines = ["", "   ", "Wine with no price"] + [f"Filler {i}" for i in range(50)]
        profile = _make_profile(preferred_grapes=["pinot noir"])
        result = rank_wine_list(_list_text(lines), profile, limit=10)
        # Should not raise; returns at most 10 non-empty lines
        assert len(result.splitlines()) <= 10
