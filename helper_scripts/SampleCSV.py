import csv
import random

INPUT_FILE = "CLEAR_Corpus_full.csv"
OUTPUT_FILE = "CLEAR_1000_sample.csv"
NUM_SAMPLES = 1000

def main():
    with open(INPUT_FILE, newline='', encoding='utf-8') as infile:
        reader = list(csv.reader(infile))
        if not reader:
            print("Input file is empty.")
            return
        
        header = reader[0]
        data_rows = reader[1:]
        
        # Remove completely blank rows (all cells empty or whitespace)
        data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
        
        # Randomly select up to 100 non-empty rows
        sampled_rows = random.sample(data_rows, min(NUM_SAMPLES, len(data_rows)))
        
    # Write header + sampled rows to new CSV
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(sampled_rows)
    
    print(f"Saved {len(sampled_rows)} random non-empty rows (plus header) to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()