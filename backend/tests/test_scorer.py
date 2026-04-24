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


if __name__ == "__main__":
    unittest.main()
