import os
import json
import anthropic
from reporter import write_html_report
from scorer import final_score
from dotenv import load_dotenv
import os
from langsmith import traceable
from langsmith.wrappers import wrap_anthropic

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
# client = anthropic.Anthropic()
client = wrap_anthropic(anthropic.Anthropic())


@traceable(name="eval-question", run_type="chain")
def evaluate_question(item: dict) -> dict:
    question = item["question"]
    expected_keywords = item["expected_keywords"]
    expected_answer = item["expected_answer"]
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=450,
        system="Answer questions concisely in 2-3 sentences. No bullet points, no headers, no markdown formatting. Plain prose only.",
        messages=[{"role": "user", "content": question}],
    )

    modelAnswer = message.content[0].text
    evaluation = final_score(
        response=modelAnswer,
        expected_keywords=expected_keywords,
        expected_answer=expected_answer,
    )

    return {
        "question": question,
        "response": modelAnswer,
        "expected_answer": expected_answer,
        "expected_keywords": expected_keywords,
        "matched_keywords": evaluation["matched_keywords"],
        "keyword_score_percent": evaluation["keyword_score_percent"],
        "embedding_score_percent": evaluation["embedding_score_percent"],
        "score": evaluation["final_score_percent"],
        "passed": evaluation["passed"],
    }
    

@traceable(name="eval-run", run_type="chain")
def running_evals(question):

    results = []
    passed_count = 0
    for i, item in enumerate(question):

        if not item or "question" not in item:
            continue
        print(f"[{i+1}/{len(question)}] {item['question'][:60]}...")
        result = evaluate_question(item)
        results.append(result)
        if result["passed"]:
            passed_count += 1
            print(f" PASS — {result['score']:.1f}%")
        else:
            print(f" FAIL — {result['score']:.1f}%")

    return {"results": results, "passed_count": passed_count}



with open(
    "/Users/arushikapoor/Desktop/LLM Response Analyzer/data/testQuestions.json", "r"
) as file:
    questionsData = json.load(file)
output = running_evals(questionsData["questions"])
results = output["results"]
passed_count = output["passed_count"]
total = len(results)

write_html_report(results)

accuracy = (passed_count / total) * 100
print(f"\n{'='*40}")
print(f"RESULTS: {passed_count}/{total} passed")
print(f"Accuracy: {accuracy:.2f}%")
print(f"{'='*40}")
