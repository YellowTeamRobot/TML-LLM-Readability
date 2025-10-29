'''
This file calculated the the (traditional) readability metrics from the sampled CLEAR excerpts, and wrote to output file.
'''
import csv
import re
import textstat

def process_csv(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8', newline='') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:

        reader = csv.reader(infile)
        writer = csv.writer(outfile)

        header = next(reader, None)  # Skip header
        writer.writerow(['ID', 'Excerpt', 'Flesch-Kincaid Grade Level', 'Flesch Reading Ease', 'Automated Readability Index', 'SMOG', 'Dale Chall'])

        for row in reader:
            if len(row) < 4:
                continue  # Skip incomplete rows

            excerpt_id = row[0].strip()
            text_excerpt = row[3].strip()

            if not text_excerpt:
                continue  # Skip blank entries

            grade = textstat.flesch_kincaid_grade(text_excerpt)
            flesch_reading_ease = textstat.flesch_reading_ease(text_excerpt)
            ari = textstat.automated_readability_index(text_excerpt)
            smog = textstat.smog_index(text_excerpt)
            dale_chall = textstat.dale_chall_readability_score(text_excerpt)
            writer.writerow([excerpt_id, text_excerpt, grade, flesch_reading_ease, ari, smog, dale_chall])

if __name__ == "__main__":
    input_csv = "CLEAR_1000_sample.csv"     # change this to your input file
    output_csv = "CLEAR_1000_sample_with_Scores.csv"   # desired output file
    process_csv(input_csv, output_csv)
    print(f"Saved results to {output_csv}")
