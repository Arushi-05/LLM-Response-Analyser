import csv

def write_csv(results):

    with open("results.csv", "w", newline="", encoding="utf-8") as csvfile:

        writer = csv.writer(csvfile)

        writer.writerow([
            "Question",
            "Response",
            "Expected Answer",
            "Score",
            "Passed"
        ])

        for row in results:
            writer.writerow([
                row["question"],
                row["response"],
                row["expected_answer"],
                row["score"],
                row["passed"]
            ])