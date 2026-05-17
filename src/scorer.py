import re
from embedder import embedding_score

def keyword_score(response, expected_keywords):
    response = response.lower()
    matchedWords = []
    for keyword in expected_keywords:
        keyword = keyword.lower()
        if keyword in response:
            matchedWords.append(keyword)

    score = len(matchedWords) / len(expected_keywords)

    return {"matched_keywords": matchedWords, "keyword_score": round(score * 100, 2)}


def final_score(response, expected_keywords, expected_answer):

    keyword_result = keyword_score(response, expected_keywords)
    keyword_percent = keyword_result["keyword_score"]

    embedding_percent = embedding_score(expected_answer, response)

    total = (0.2 * keyword_percent) + (0.8 * embedding_percent)

    final_percent = round(total * 100, 2)

    passed = final_percent >= 75
    return {
        "matched_keywords": keyword_result["matched_keywords"],
        "keyword_score_percent": round(keyword_percent * 100, 2),
        "embedding_score_percent": round(embedding_percent * 100, 2),
        "final_score_percent": final_percent,
        "passed": passed,
    }
