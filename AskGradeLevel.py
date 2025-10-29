import csv
import subprocess
import statistics
import re
import time

INPUT_FILE = "CLEAR_1000_sample_with_Scores.csv"      # your input csv
OUTPUT_FILE = "1000_sample_Output_GradeLevel.csv"    # where results will be saved
MODEL = "gpt-oss:20b"
NUM_SAMPLES = 5
ENCODING= 'utf-8' #'windows-1252' #'utf-8'

def query_ollama(prompt: str) -> str:
    """Call Ollama CLI with given prompt and return model response text."""
    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt,
        text=True,
        capture_output=True
    )
    return result.stdout.strip()

def extract_grade(response: str) -> int | None:
    """Extract the numeric grade from model response like 'Grade Level: 8'."""
    match = re.search(r"Grade\s*Level\s*:\s*(\d+)", response)
    if match:
        return int(match.group(1))
    return None

def main():
    start_time = time.time()
    with open(INPUT_FILE, newline='', encoding=ENCODING) as infile, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        header = next(reader)  # skip header row
        writer.writerow(["ID"] + [f"Run {i+1}" for i in range(NUM_SAMPLES)] + ["Average"])
        
        for row in reader:
            # Skip rows that are completely empty or only contain whitespace
            if not row or all(cell.strip() == "" for cell in row):
                print("Reached empty row — stopping.")
                break

            excerpt_id = row[0].strip()
            #excerpt_text = row[14].strip()
            excerpt_text = row[1].strip()
            #excerpt_text = row[3].strip()

            prompt = (
                "Please give the US school grade level (1-12) (13-18 are also acceptable for college level text) for the difficulty of the text excerpt below. "
                "Format your output strictly as 'Grade Level: {number}'.\n"
                f"{excerpt_text}"
            )

            grades = []
            for i in range(NUM_SAMPLES):
                print(f"Processing ID {excerpt_id}, sample {i+1}/{NUM_SAMPLES}...")
                #print(f"\n{excerpt_text}\n")
                response = query_ollama(prompt)
                grade = extract_grade(response)
                if grade is not None:
                    grades.append(grade)
                else:
                    grades.append("")  # if extraction fails, leave blank
            
            avg = round(statistics.mean(g for g in grades if isinstance(g, (int, float))) ,2) if any(isinstance(g, (int, float)) for g in grades) else ""
            
            writer.writerow([excerpt_id] + grades + [avg])

    end_time = time.time()
    print(f"Done in {end_time-start_time} seconds. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
