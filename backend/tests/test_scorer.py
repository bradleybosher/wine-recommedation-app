import unittest

from models import RecommendationResponse, TasteProfile
from scorer import score_recommendation


class ScoreConfidenceParsingTests(unittest.TestCase):
    def _build_response(self, confidence: str) -> RecommendationResponse:
        return RecommendationResponse(
            recommendations=[
                {
                    "rank": 1,
                    "wine_name": "Test Wine",
                    "reasoning": "Fits the profile.",
                    "confidence": confidence,
                }
            ],
            profile_match_summary="Summary",
        )

    def test_confidence_supports_explanatory_suffix(self) -> None:
        response = self._build_response("high — strong profile match")

        result = score_recommendation(response, wine_list_text="Test Wine")

        self.assertEqual(result.breakdown["confidence"], 1.0)

    def test_confidence_remains_case_insensitive(self) -> None:
        response = self._build_response("Medium — balanced match")

        result = score_recommendation(response, wine_list_text="Test Wine")

        self.assertEqual(result.breakdown["confidence"], 0.67)

    def test_budget_fit_still_works_with_confidence_prefixes(self) -> None:
        response = RecommendationResponse(
            recommendations=[
                {
                    "rank": 1,
                    "wine_name": "Budget Wine",
                    "reasoning": "Good fit.",
                    "confidence": "low — young vintage",
                    "price": 45,
                }
            ],
            profile_match_summary="Summary",
        )

        profile = TasteProfile(budget_min=30, budget_max=50)
        result = score_recommendation(response, wine_list_text="Budget Wine", profile=profile)

        self.assertEqual(result.breakdown["budget_fit"], 1.0)
        self.assertEqual(result.breakdown["confidence"], 0.33)


    def test_empty_recommendations_list_scores_low(self) -> None:
        """Empty recommendations list should yield low confidence and completeness."""
        response = RecommendationResponse(
            recommendations=[],
            profile_match_summary="No recommendations available.",
        )

        result = score_recommendation(response, wine_list_text="Test Wine")

        self.assertEqual(result.breakdown["confidence"], 0.0)
        self.assertEqual(result.breakdown["completeness"], 0.0)
        # Total should be very low when key dimensions are 0
        self.assertLess(result.total, 0.5)

    def test_all_recommendations_grounded_in_wine_list(self) -> None:
        """All wines found in list should yield grounding=1.0."""
        response = RecommendationResponse(
            recommendations=[
                {
                    "rank": 1,
                    "wine_name": "Château Margaux",
                    "reasoning": "Classic match.",
                    "confidence": "high",
                },
                {
                    "rank": 2,
                    "wine_name": "Domaine de la Romanée-Conti",
                    "reasoning": "Premium option.",
                    "confidence": "medium",
                },
                {
                    "rank": 3,
                    "wine_name": "Barolo Cannubi",
                    "reasoning": "Italian alternative.",
                    "confidence": "medium",
                },
            ],
            profile_match_summary="All wines present.",
        )
        wine_list_text = "Château Margaux 2015\nDomaine de la Romanée-Conti Pinot Noir\nBarolo Cannubi 2014"

        result = score_recommendation(response, wine_list_text=wine_list_text)

        self.assertEqual(result.breakdown["grounding"], 1.0)

    def test_no_wine_list_text_triggers_warning(self) -> None:
        """Empty wine_list_text should trigger a warning and neutral grounding."""
        response = RecommendationResponse(
            recommendations=[
                {
                    "rank": 1,
                    "wine_name": "Test Wine",
                    "reasoning": "Test.",
                    "confidence": "high",
                }
            ],
            profile_match_summary="Test.",
        )

        result = score_recommendation(response, wine_list_text="")

        self.assertIn("wine_list_text empty", " ".join(result.warnings))
        self.assertEqual(result.breakdown["grounding"], 0.5)

    def test_budget_fit_with_out_of_range_price(self) -> None:
        """Recommendations outside budget should reduce budget_fit below 1.0."""
        response = RecommendationResponse(
            recommendations=[
                {
                    "rank": 1,
                    "wine_name": "Expensive Wine",
                    "reasoning": "Too pricey.",
                    "confidence": "medium",
                    "price": 150,  # Outside budget
                },
                {
                    "rank": 2,
                    "wine_name": "Budget Wine",
                    "reasoning": "Within budget.",
                    "confidence": "medium",
                    "price": 35,  # Within budget
                },
            ],
            profile_match_summary="Mixed budget fit.",
        )
        profile = TasteProfile(budget_min=30, budget_max=50)

        result = score_recommendation(response, wine_list_text="Test", profile=profile)

        # With one in-range and one out-of-range, budget_fit should be 0.5
        self.assertEqual(result.breakdown["budget_fit"], 0.5)

    def test_scorer_never_raises_on_garbage_data(self) -> None:
        """Scorer should handle malformed data gracefully and return ScoringResult."""
        # Create a response with missing fields
        response = RecommendationResponse(
            recommendations=[
                {
                    "rank": 1,
                    "wine_name": "Garbage",
                    "reasoning": "Test",
                    "confidence": "invalid_confidence_level",
                    "price": None,
                }
            ],
            profile_match_summary="Test",
        )
        profile = TasteProfile(budget_min=20, budget_max=80)

        # Should not raise; should return a ScoringResult
        try:
            result = score_recommendation(response, wine_list_text=None, profile=profile)
            self.assertIsNotNone(result)
            self.assertIsInstance(result.total, float)
            self.assertIsInstance(result.breakdown, dict)
        except Exception as e:
            self.fail(f"scorer raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    unittest.main()
