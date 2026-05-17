# src/scorer.py

import re
from typing import Optional
from embedder import embedding_score


def keyword_score(response: str, expected_keywords: list) -> dict:
    
    if not isinstance(response, str):
        return {
            "matched_keywords": [],
            "keyword_score": 0.0,         
            "keyword_score_percent": 0.0   
        }

    if not response.strip():
        return {
            "matched_keywords": [],
            "keyword_score": 0.0,
            "keyword_score_percent": 0.0
        }

  
    if not expected_keywords:
        return {
            "matched_keywords": [],
            "keyword_score": 1.0,
            "keyword_score_percent": 100.0
        }

    response_lower = response.lower()
    matched_keywords = []

    for keyword in expected_keywords:
        if not isinstance(keyword, str):
            continue  
        keyword_lower = keyword.lower()
        if len(keyword_lower.split()) == 1:
     
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, response_lower):
                matched_keywords.append(keyword)
        else:
       
            if keyword_lower in response_lower:
                matched_keywords.append(keyword)

    score = len(matched_keywords) / len(expected_keywords) 

    return {
        "matched_keywords": matched_keywords,
        "keyword_score": round(score, 4),       
        "keyword_score_percent": round(score * 100, 2)  
    }


def final_score(
    response: str,
    expected_keywords: list,
    expected_answer: str,
    pass_threshold: float = 75.0
) -> dict:
  
    if not isinstance(response, str) or not response.strip():
        return {
            "matched_keywords": [],
            "keyword_score_percent": 0.0,
            "embedding_score_percent": 0.0,
            "final_score_percent": 0.0,
            "passed": False,
            "error": "empty_or_invalid_response"
        }

    if not isinstance(expected_answer, str) or not expected_answer.strip():
        return {
            "matched_keywords": [],
            "keyword_score_percent": 0.0,
            "embedding_score_percent": 0.0,
            "final_score_percent": 0.0,
            "passed": False,
            "error": "empty_or_invalid_expected_answer"
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