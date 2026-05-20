import pytest
from src.scorer import (
    score_keyword_match,
    score_exact_match,
    score_response_length,
    score_no_forbidden_words,
    aggregate_score
)

@pytest.fixture
def perfect_response():
    """A response that should pass all checks"""
    return "Your order will be delivered within 3-5 business days."

@pytest.fixture
def empty_response():
    """Edge case: model returned nothing"""
    return ""

@pytest.fixture
def hallucinated_response():
    """Response that contains forbidden/incorrect claims"""
    return "Your order will arrive tomorrow guaranteed, and you get a free gift."

@pytest.fixture
def too_long_response():
    """Response that exceeds acceptable length"""
    return "A" * 2000  


class TestKeywordMatch:

    def test_all_keywords_present_returns_perfect_score(self, perfect_response):
        keywords = ["delivered", "business days"]
        score = score_keyword_match(perfect_response, keywords)
        assert score == 1.0, "All keywords present should return 1.0"

    def test_no_keywords_present_returns_zero(self, perfect_response):
        keywords = ["refund", "cancelled", "unavailable"]
        score = score_keyword_match(perfect_response, keywords)
        assert score == 0.0, "No keywords present should return 0.0"

    def test_partial_keywords_returns_partial_score(self, perfect_response):
        keywords = ["delivered", "refund"]  # only "delivered" is present
        score = score_keyword_match(perfect_response, keywords)
        assert score == 0.5, "Half keywords present should return 0.5"

    def test_empty_response_returns_zero(self, empty_response):
        keywords = ["delivered"]
        score = score_keyword_match(empty_response, keywords)
        assert score == 0.0, "Empty response should return 0.0"

    def test_empty_keywords_list_returns_perfect_score(self, perfect_response):
        score = score_keyword_match(perfect_response, [])
        assert score == 1.0, "No keywords required should return 1.0"

    def test_case_insensitive_matching(self):
        response = "Your ORDER will be DELIVERED soon."
        keywords = ["order", "delivered"]
        score = score_keyword_match(response, keywords)
        assert score == 1.0, "Keyword matching should be case-insensitive"


class TestExactMatch:

    def test_exact_match_returns_one(self):
        response = "The return policy is 30 days."
        expected = "The return policy is 30 days."
        assert score_exact_match(response, expected) == 1.0

    def test_different_response_returns_zero(self):
        response = "Returns are accepted within 30 days."
        expected = "The return policy is 30 days."
        assert score_exact_match(response, expected) == 0.0

    def test_whitespace_differences_handled(self):
        response = "  The return policy is 30 days.  \n"
        expected = "The return policy is 30 days."
        assert score_exact_match(response, expected) == 1.0

    def test_empty_response_returns_zero(self, empty_response):
        expected = "The return policy is 30 days."
        assert score_exact_match(empty_response, expected) == 0.0

class TestResponseLength:

    def test_response_within_bounds_returns_one(self, perfect_response):
       
        score = score_response_length(perfect_response, min_chars=20, max_chars=500)
        assert score == 1.0

    def test_response_too_short_returns_zero(self):
        response = "Yes." 
        score = score_response_length(response, min_chars=20, max_chars=500)
        assert score == 0.0

    def test_response_too_long_returns_zero(self, too_long_response):
        score = score_response_length(too_long_response, min_chars=20, max_chars=500)
        assert score == 0.0

    def test_empty_response_returns_zero(self, empty_response):
        score = score_response_length(empty_response, min_chars=20, max_chars=500)
        assert score == 0.0

    def test_exactly_at_minimum_boundary(self):
        response = "A" * 20  
        score = score_response_length(response, min_chars=20, max_chars=500)
        assert score == 1.0, "Exactly at minimum should pass"

    def test_exactly_at_maximum_boundary(self):
        response = "A" * 500 
        score = score_response_length(response, min_chars=20, max_chars=500)
        assert score == 1.0, "Exactly at maximum should pass"

    def test_one_over_maximum_boundary(self):
        response = "A" * 501 
        score = score_response_length(response, min_chars=20, max_chars=500)
        assert score == 0.0, "One over maximum should fail"



class TestForbiddenWords:

    def test_no_forbidden_words_returns_one(self, perfect_response):
        forbidden = ["competitor", "free gift", "guaranteed tomorrow"]
        score = score_no_forbidden_words(perfect_response, forbidden)
        assert score == 1.0

    def test_forbidden_word_present_returns_zero(self, hallucinated_response):
        forbidden = ["free gift"]
        score = score_no_forbidden_words(hallucinated_response, forbidden)
        assert score == 0.0

    def test_empty_response_returns_zero(self, empty_response):
        forbidden = ["bad_word"]
        score = score_no_forbidden_words(empty_response, forbidden)
        assert score == 0.0

    def test_empty_forbidden_list_returns_one(self, perfect_response):
        score = score_no_forbidden_words(perfect_response, [])
        assert score == 1.0

    def test_case_insensitive_forbidden_detection(self):
        response = "I CANNOT help you with that."
        forbidden = ["cannot"]
        score = score_no_forbidden_words(response, forbidden)
        assert score == 0.0, "Forbidden word detection should be case-insensitive"

class TestAggregateScore:

    def test_all_perfect_scores_return_one(self):
        scores = [1.0, 1.0, 1.0, 1.0]
        assert aggregate_score(scores) == 1.0

    def test_all_zero_scores_return_zero(self):
        scores = [0.0, 0.0, 0.0, 0.0]
        assert aggregate_score(scores) == 0.0

    def test_mixed_scores_return_average(self):
        scores = [1.0, 0.5, 1.0, 0.5]
        result = aggregate_score(scores)
        assert result == 0.75

    def test_single_score_returned_as_is(self):
        assert aggregate_score([0.8]) == 0.8

    def test_empty_scores_raises_error(self):
        with pytest.raises(ValueError):
            aggregate_score([])

    def test_score_outside_range_raises_error(self):
        with pytest.raises(ValueError):
            aggregate_score([1.5, 0.5]) 

@pytest.mark.parametrize("response, keywords, expected_score", [
    ("Delivery takes 3-5 days.", ["delivery", "days"], 1.0),
    ("We cannot process your request.", ["refund"], 0.0),
    ("Your refund will be processed.", ["refund", "cancelled"], 0.5),
    ("", ["anything"], 0.0),
    ("Short answer.", [], 1.0),
])
def test_keyword_match_parametrized(response, keywords, expected_score):
    """
    Parametrized test: same logic, many data combinations.
    Add more rows to this table to expand coverage instantly.
    """
    assert score_keyword_match(response, keywords) == expected_score


class TestEdgeCases:

    def test_response_is_only_whitespace(self):
        response = "     \n\t   "
        score = score_keyword_match(response, ["answer"])
        assert score == 0.0, "Whitespace-only response should score 0"

    def test_response_with_special_characters(self):
        response = "Your order #12345 will arrive by 12/25. Cost: $49.99!"
        keywords = ["order", "arrive"]
        score = score_keyword_match(response, keywords)
        assert score == 1.0, "Special characters should not break matching"

    def test_response_with_numbers_only(self):
        response = "42"
        score = score_response_length(response, min_chars=20, max_chars=500)
        assert score == 0.0, "Number-only too-short response should fail length check"

    def test_unicode_response(self):
        response = "Votre commande arrivera dans 3 jours. 注文は3日で届きます。"
        keywords = ["commande", "注文"]
        score = score_keyword_match(response, keywords)
        assert score == 1.0, "Unicode characters should be handled correctly"