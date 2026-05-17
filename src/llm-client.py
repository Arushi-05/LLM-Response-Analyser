import os
import json
import anthropic
from scorer import final_score
from reporter import write_csv
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic()

with open("data/testQusetions.json", "r") as file:
    questionsData = json.load(file)
results = []
passed_count = 0
for item in questionsData["questions"]:
    question = item["question"]
    expected_keywords = item["expected_keywords"]
    expected_answer = item["expected_answer"]
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=150,
        messages=[{"role": "user", "content": question}],
    )

    modelAnswer = message.content[0].text
    evaluation = final_score(
        response=modelAnswer,
        expected_keywords=expected_keywords,
        expected_answer=expected_answer,
    )

    if evaluation["passed"]:
        passed_count += 1

    results.append(
        {
            "question": question,
            "response": modelAnswer,
            "expected_answer": expected_answer,
            "score": evaluation["final_score_percent"],
            "passed": evaluation["passed"],
        }
    )
write_csv(results)

total = len(results)
accuracy = (passed_count / total) * 100

print(f"\n{passed_count}/{total} passed")
print(f"Accuracy: {accuracy:.2f}%")
