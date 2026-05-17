from sklearn.metrics.pairwise import cosine_similarity

_model = None

def _get_model():
   
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embedding_score(expected_answer: str, response: str) -> float:
    model = _get_model()

    embeddings = model.encode([expected_answer, response])

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )[0][0]

    return float(max(0.0, min(1.0, similarity)))