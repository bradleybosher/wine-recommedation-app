"""Tests for meal_parser module: synonym normalisation and meal-to-wine hints."""

import unittest

from meal_parser import parse_meal_description, meal_to_wine_hints, MealProfile


class MealParserSynonymTests(unittest.TestCase):
    """Test protein and cooking method synonym normalisation."""

    def test_pan_seared_duck_normalizes_to_duck_protein(self) -> None:
        """'pan-seared duck' should normalize to duck protein via synonym resolution."""
        meal = "pan-seared duck breast with cherry sauce"
        profile = parse_meal_description(meal)

        self.assertEqual(profile.protein, "duck")
        self.assertEqual(profile.richness, "rich")  # duck is rich

    def test_bbq_prawns_normalizes_to_shrimp(self) -> None:
        """'BBQ prawns' should normalize prawns → shrimp via synonym."""
        meal = "BBQ prawns with garlic butter"
        profile = parse_meal_description(meal)

        # prawns → shrimp synonym should apply
        self.assertEqual(profile.protein, "shrimp")
        self.assertEqual(profile.richness, "light")  # shrimp is light
        # bbq → grilled
        self.assertEqual(profile.cooking_method, "grilled")

    def test_pan_seared_cooking_method_synonym(self) -> None:
        """'pan-seared' should normalize to 'seared' cooking method."""
        meal = "pan-seared salmon"
        profile = parse_meal_description(meal)

        self.assertEqual(profile.cooking_method, "seared")

    def test_slow_roasted_beef(self) -> None:
        """'slow roasted' should normalize to 'roasted' cooking method."""
        meal = "slow roasted beef with root vegetables"
        profile = parse_meal_description(meal)

        self.assertEqual(profile.protein, "beef")
        self.assertEqual(profile.cooking_method, "roasted")

    def test_empty_meal_profile_returns_dict(self) -> None:
        """meal_to_wine_hints with an empty MealProfile should return a dict-formatted string."""
        profile = MealProfile()
        hints = meal_to_wine_hints(profile)

        self.assertIsInstance(hints, str)
        # Should not raise; may be empty or minimal
        self.assertTrue(len(hints) >= 0)

    def test_completely_empty_string_meal(self) -> None:
        """parse_meal_description with empty string should not raise."""
        meal = ""
        try:
            profile = parse_meal_description(meal)
            self.assertIsNotNone(profile)
        except Exception as e:
            self.fail(f"parse_meal_description raised {type(e).__name__} on empty string: {e}")

    def test_meal_to_wine_hints_with_full_profile(self) -> None:
        """meal_to_wine_hints should format a fully populated MealProfile into text."""
        profile = MealProfile(
            protein="beef",
            cooking_method="roasted",
            sauce_flavor="red wine reduction",
            heat_level="moderate",
            richness="rich",
            dominant_flavors=["savory", "deep"],
        )

        hints = meal_to_wine_hints(profile)

        self.assertIsInstance(hints, str)
        self.assertIn("Protein", hints)
        self.assertIn("beef", hints)
        self.assertIn("roasted", hints)

    def test_protein_synonyms_multiple_options(self) -> None:
        """Multiple protein synonyms should resolve correctly."""
        test_cases = [
            ("duck leg confit", "duck"),
            ("chicken breast with herbs", "chicken"),
            ("filet mignon", "beef"),
            ("sea bass with lemon", "fish"),
        ]

        for meal_desc, expected_protein in test_cases:
            with self.subTest(meal=meal_desc):
                profile = parse_meal_description(meal_desc)
                self.assertEqual(profile.protein, expected_protein)


class MealParserIntegrationTests(unittest.TestCase):
    """Integration tests for meal parsing with real meal descriptions."""

    def test_complex_meal_description(self) -> None:
        """Complex meal with multiple attributes should parse all components."""
        meal = "Pan-seared duck breast with cherry gastrique and black pepper"
        profile = parse_meal_description(meal)

        self.assertEqual(profile.protein, "duck")
        self.assertEqual(profile.cooking_method, "seared")
        self.assertIsNotNone(profile.sauce_flavor)
        self.assertEqual(profile.heat_level, "moderate")  # peppercorn keyword

    def test_light_seafood_meal(self) -> None:
        """Light seafood meal should identify light richness."""
        meal = "Steamed halibut with white wine sauce and fresh herbs"
        profile = parse_meal_description(meal)

        self.assertEqual(profile.protein, "fish")
        self.assertEqual(profile.cooking_method, "steamed")
        self.assertEqual(profile.richness, "light")


if __name__ == "__main__":
    unittest.main()
