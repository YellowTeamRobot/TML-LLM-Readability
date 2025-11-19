import csv
import textstat
import math


ORIGINAL_FILE = "data/CLEAR_1000_sample.csv"
REWRITE_FILE = "data/rewrite/FK_seed7.csv"
OUTPUT_FILE = "data/rewrite/FK_GradeLevel_Comparison_seed7.csv"
ENCODING = "utf-8"


def compute_grade_level(text):
    if not text.strip():
        return float("nan")
    return float(textstat.flesch_kincaid_grade(text))


def load_original_texts(path):
    id_to_text = {}
    with open(path, newline="", encoding=ENCODING) as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if not row or all(cell.strip()=="" for cell in row):
                continue
            excerpt_id = row[0].strip()
            original_text = row[1].strip()
            id_to_text[excerpt_id] = original_text
    return id_to_text


def main():
    id_to_original = load_original_texts(ORIGINAL_FILE)

    with open(REWRITE_FILE, newline="", encoding=ENCODING) as rew_f,\
         open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as out_f:

        rew_reader = csv.DictReader(rew_f)
        writer = csv.writer(out_f)

        writer.writerow([
            "ID",
            "Original_Grade",
            "Target_Grade",
            "Rewritten_Grade",
            "Distance_to_Target",
            "Improvement_Toward_Target",
            "Directional_Consistency"
        ])

        for row in rew_reader:
            ID = row["ID"].strip()
            target_grade = float(row["Desired Grade Level"])
            rewritten_text = row["Rewritten Excerpt"].strip()

            # Read FK score from file instead of recomputing
            rewritten_fk = row["Flesch-Kincaid Grade Level (of Rewritten)"]
            if rewritten_fk == "" or rewritten_fk is None:
                print(f"Missing FK score for ID {ID}, skipping.")
                continue
            rewritten_fk = float(rewritten_fk)

            if ID not in id_to_original:
                print(f"Warning: No original text found for ID {ID}")
                continue

            original_text = id_to_original[ID]
            og = compute_grade_level(original_text)

            if math.isnan(og):
                print(f"Original text returned NaN for ID {ID}, skipping.")
                continue

            # Compute metrics
            dist = abs(rewritten_fk - target_grade)

            og_gap = abs(og - target_grade)
            rg_gap = abs(rewritten_fk - target_grade)
            improvement = og_gap - rg_gap

            diff_rew = rewritten_fk - og
            diff_tgt = target_grade - og
            directional = 1 if diff_rew * diff_tgt > 0 else 0

            writer.writerow([
                ID,
                round(og, 3),
                target_grade,
                round(rewritten_fk, 3),
                round(dist, 3),
                round(improvement, 3),
                directional,
            ])

    print(f"Done! Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
