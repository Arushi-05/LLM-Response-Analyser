import re
from typing import Optional
from embedder import embedding_score
from typing import List

def keyword_score(response: str, expected_keywords: list) -> dict:

    if not isinstance(response, str):
        return {
            "matched_keywords": [],
            "keyword_score": 0.0,
            "keyword_score_percent": 0.0,
        }

    if not response.strip():
        return {
            "matched_keywords": [],
            "keyword_score": 0.0,
            "keyword_score_percent": 0.0,
        }

    if not expected_keywords:
        return {
            "matched_keywords": [],
            "keyword_score": 1.0,
            "keyword_score_percent": 100.0,
        }

    response_lower = response.lower()
    matched_keywords = []

    for keyword in expected_keywords:
        if not isinstance(keyword, str):
            continue
        keyword_lower = keyword.lower()
        if len(keyword_lower.split()) == 1:

            pattern = r"\b" + re.escape(keyword_lower) + r"\b"
            if re.search(pattern, response_lower):
                matched_keywords.append(keyword)
        else:

            if keyword_lower in response_lower:
                matched_keywords.append(keyword)

    score = len(matched_keywords) / len(expected_keywords)

    return {
        "matched_keywords": matched_keywords,
        "keyword_score": round(score, 4),
        "keyword_score_percent": round(score * 100, 2),
    }


def final_score(
    response: str,
    expected_keywords: list,
    expected_answer: str,
    pass_threshold: float = 70.0,
) -> dict:

    if not isinstance(response, str) or not response.strip():
        return {
            "matched_keywords": [],
            "keyword_score_percent": 0.0,
            "embedding_score_percent": 0.0,
            "final_score_percent": 0.0,
            "passed": False,
            "error": "empty_or_invalid_response",
        }

    if not isinstance(expected_answer, str) or not expected_answer.strip():
        return {
            "matched_keywords": [],
            "keyword_score_percent": 0.0,
            "embedding_score_percent": 0.0,
            "final_score_percent": 0.0,
            "passed": False,
            "error": "empty_or_invalid_expected_answer",
        }

    keyword_result = keyword_score(response, expected_keywords)

    keyword_ratio = keyword_result["keyword_score"]
    embedding_ratio = float(embedding_score(expected_answer, response))

    combined_ratio = (0.2 * keyword_ratio) + (0.8 * embedding_ratio)

    final_percent = round(combined_ratio * 100, 2)

    return {
        "matched_keywords": keyword_result["matched_keywords"],
        "keyword_score_percent": keyword_result["keyword_score_percent"],
        "embedding_score_percent": round(embedding_ratio * 100, 2),
        "final_score_percent": final_percent,
        "passed": final_percent >= pass_threshold,
    }


#####these are the functions used for validating scorers functions-


def score_keyword_match(response: str, keywords: List[str]) -> float:
    """
    Score: what fraction of required keywords appear in the response?
    Returns 0.0 to 1.0
    """
    if not keywords:
        return 1.0
    if not response or not response.strip():
        return 0.0

    response_lower = response.lower()
    matches = sum(1 for kw in keywords if kw.lower() in response_lower)
    return matches / len(keywords)


def score_exact_match(response: str, expected: str) -> float:
    """
    Score: does the response exactly match the expected output?
    Returns 1.0 (match) or 0.0 (no match)
    """
    if not response or not response.strip():
        return 0.0
    return 1.0 if response.strip() == expected.strip() else 0.0


def score_response_length(response: str, min_chars: int, max_chars: int) -> float:
    """
    Score: is the response within acceptable length bounds?
    Returns 1.0 (within bounds) or 0.0 (out of bounds)
    """
    if not response:
        return 0.0
    length = len(response.strip())
    return 1.0 if min_chars <= length <= max_chars else 0.0


def score_no_forbidden_words(response: str, forbidden: List[str]) -> float:
    """
    Score: does the response avoid all forbidden words?
    Returns 1.0 (clean) or 0.0 (violation found)
    """
    if not forbidden:
        return 1.0
    if not response or not response.strip():
        return 0.0

    response_lower = response.lower()
    for word in forbidden:
        if word.lower() in response_lower:
            return 0.0
    return 1.0


def aggregate_score(scores: List[float]) -> float:
    """
    Combine multiple scores into one final score (simple average).
    Raises ValueError for empty list or out-of-range scores.
    """
    if not scores:
        raise ValueError("Cannot aggregate empty scores list")
    for s in scores:
        if not (0.0 <= s <= 1.0):
            raise ValueError(f"Score {s} is out of valid range [0.0, 1.0]")
    return sum(scores) / len(scores)