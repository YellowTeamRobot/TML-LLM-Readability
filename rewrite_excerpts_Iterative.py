import ollama
import textstat
import time
import csv
import re
import random
import json


MODEL = "gpt-oss:20b"
INPUT_FILE = "CLEAR_1000_sample.csv"      
OUTPUT_FILE = "Rewrite_Iter_FK_seed7_Final.csv"    
ENCODING= 'utf-8' #'windows-1252' #'utf-8'
#DESIRED_GRADE_LEVEL = "5th" # adjust this to select the desired grade level output
METHOD = "FK" # "FK"-Flesch-Kincaid Grade Level, "SMOG"-SMOG, "ARI"-Automated Readability Index, "DC"-Dale-Chall, "LLM"-get grade level from csv of LLM output by ID number, "LLM-C"-get corrected LLM grade level from csv by ID number, "None", don't get grade level of input text
PRECOMPUTED_GRADE_LEVEL = None #

START_ROW = 1 # set to 1 to start from beginning, or to a higher number to resume from that row (make sure to change output file to not overwrite existing)
SEED_VALUE = 7 # seed value for reproducibility of random grades to rewrite to. Values used in testing: 7, 303, 253478
random.seed(SEED_VALUE)
DESIRED_GRADE_LEVELS = [random.randint(1, 12) for _ in range(2000)]

# Function to compute grade level using textstat
def compute_grade_level(text: str) -> int:
    print(f"\n\n -------------------- \nComputing grade level for text:\n {text}\n")
    if (METHOD == "FK"):
        return int(textstat.flesch_kincaid_grade(text)) # Flesch-Kincaid grade level
    elif (METHOD == "SMOG"):
        return int(textstat.smog_index(text))  # SMOG index grade level
    elif (METHOD == "ARI"):
        return int(textstat.automated_readability_index(text))  # Automated Readability Index grade level
    elif (METHOD == "DC"):
        return int(textstat.dale_chall_readability_score(text))  # Dale-Chall grade level
    elif (METHOD == "LLM" or METHOD == "LLM-C"):
        return int(PRECOMPUTED_GRADE_LEVEL)
    else:
        return int(textstat.flesch_kincaid_grade(text)) # Flesch-Kincaid grade level

# Tool definition
compute_grade_level_tool = {
    'type': 'function',
    'function': {
        'name': 'compute_grade_level',
        'description': 'Compute the U.S. grade level of a given piece of text.',
        'parameters': {
            'type': 'object',
            'required': ['text'],
            'properties': {
                'text': {'type': 'string', 'description': 'The text whose grade level should be computed'}
            }
        }
    }
}

# Tool handler
def handle_tool_call(tool_name, tool_args):
    if tool_name == 'compute_grade_level':
        text = tool_args.get('text', '')
        grade = compute_grade_level(text)
        return {'grade_level': grade}
    return {}

def query_ollama_iterative(prompt: str) -> tuple[str, str, int]:
    messages = [{'role': 'user', 'content': prompt}]
    conversation = f"User: {prompt}\n\n"

    desired_grade = int(re.search(r"a (\d{1,2})", prompt).group(1))


    i = 0 #number of rewrites
    while True:
        response = ollama.chat(model=MODEL, messages=messages, tools=[compute_grade_level_tool])
        conversation += f"Model: {response['message']['content']}\n\n"
        tool_calls = response['message'].get('tool_calls', [])
        
        if not tool_calls:
            return response['message']['content'], conversation, i
        for call in tool_calls:
            tool_name = call['function']['name']
            tool_args = call['function']['arguments']
            result = handle_tool_call(tool_name, tool_args)
            print(f"Tool '{tool_name}' -> {result}\n--------------------\n")

            conversation += f"Tool Call: {tool_name} with args {tool_args}\n"
            conversation += f"Tool Result: {result}\n\n"
            
            messages.append({'role': 'tool', 'name': tool_name, 'arguments': tool_args, 'content': str(result)})
            if i > 0:  # after checking the first grade level and giving LLM chance to write that it is already at or below desired level
                output_grade = result.get('grade_level', None)
                output_text = tool_args.get('text', '')
                if desired_grade-1 <= output_grade <= desired_grade+1:
                    print(f"Desired grade level reached.\n{output_text}\n")
                    conversation += f"Model: The following excerpt is at a {output_grade} grade level.\nRewritten Excerpt:\n {output_text}"
                    return f"Rewritten Excerpt:{output_text}", conversation, i
            i += 1

def get_llm_score(csv_filename, ID, use_corrected=False):
    """
    Returns the uncorrected or corrected LLM score for a given ID.

    Args:
        csv_filename (str): Path to the CSV file.
        ID (str or int): The ID to look up.
        use_corrected (bool): If True, return corrected score; else uncorrected.

    Returns:
        int or None: The requested score, or None if not found or invalid.
    """
    with open(csv_filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        col_name = "corrected LLM score" if use_corrected else "uncorrected LLM score"

        for row in reader:
            if str(row["ID"]) == str(ID):
                val = row.get(col_name, "")
                try:
                    return int(val)
                except ValueError:
                    return None
    return None


def query_ollama(prompt: str) -> tuple[str, str]:
    """
    Query Ollama model with single tool-call handling.
    Returns the final response as the first string, and the full conversation log as the second string.
    """
    conversation = f"User: {prompt}\n\n"
    response = ollama.chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        tools = [] if METHOD in ["None", "LLM", "LLM-C"] else [compute_grade_level_tool], # use heuristic tool if METHOD is not "LLM", otherwise LLM decides
    )
    conversation += f"Model: {response['message']['content']}\n\n"
    # Check if the model called a tool
    if 'tool_calls' in response['message'] and response['message']['tool_calls']:
        for call in response['message']['tool_calls']:
            tool_name = call['function']['name']
            #tool_args = call['function']['arguments']
            raw_args = call['function']['arguments']
            # Parse if JSON string; otherwise keep as-is
            if isinstance(raw_args, str):
                try:
                    tool_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    # fallback: maybe the model gave something malformed
                    print("Warning: invalid JSON arguments, passing raw text.")
                    tool_args = {"text": raw_args}
            else:
                tool_args = raw_args
            # Execute tool
            tool_result = handle_tool_call(tool_name, tool_args)
            print(f"Tool result: {tool_result}\n")

            conversation += f"Tool Call: {tool_name} with args {tool_args}\n"
            conversation += f"Tool Result: {tool_result}\n\n"
            
            # Feed tool result back into the conversation
            followup = ollama.chat(
                model=MODEL,
                messages=[
                    {'role': 'user', 'content': prompt},
                    {'role': 'tool', 'name': tool_name, 'content': str(tool_result)}
                ]
            )
            #print(f"{followup['message']['content']}\n\n")
            conversation += f"Model: {followup['message']['content']}\n\n"
            return followup['message']['content'], conversation
    
    # If no tool call, just return model output
    return response['message']['content'], conversation


MAX_RETRIES = 5
RETRY_DELAY = 1.0  # seconds between attempts
def safe_query_ollama(prompt):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            #num_rewrites = 1
            #response, log = query_ollama(prompt) # Use this for single tool-call handling
            response, log, num_rewrites = query_ollama_iterative(prompt) # Use this for iterative tool-call handling
            return response, log, num_rewrites

        except ollama._types.ResponseError as e:
            # Check if it looks like a JSON or tool call parse issue
            if "error parsing tool call" in str(e):
                print(f"Ollama tool-call parse error on attempt {attempt}: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue  # retry
                else:
                    print("Maximum retries reached. Skipping this excerpt.")
                    return None, None
            else:
                # Some other error (network, model crash, etc.)
                raise  # don’t suppress unknown issues

def main():

    start_time = time.time()
    with open(INPUT_FILE, newline='', encoding=ENCODING) as infile, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        header = next(reader)  # skip header row
        writer.writerow(["ID"] + [f"Desired Grade Level"] + [f"Rewritten Excerpt"] + ["Number of Rewrites"] + ["Rewritten Flesch-Kincaid"] + ["Rewritten ARI"] + ["Rewritten SMOG"] + ["Full Chat Log"])
        i = 0
        for row in reader:
            # Skip rows that are completely empty or only contain whitespace
            if not row or all(cell.strip() == "" for cell in row):
                print("Reached empty row — stopping.")
                break
            #if i >= 4: # limit to first few samples for testing (remove when doing full run) IMPORTANT
            #    break
            i += 1
            if i < START_ROW:
                continue  # skip to desired start row

            desired_grade_level = DESIRED_GRADE_LEVELS[i-1]  # get desired grade level for this excerpt
            suffix = lambda n: f"{n}{'th' if 11 <= n % 100 <= 13 else {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th')}"
            dgl_str = suffix(desired_grade_level) # string form to give to LLM

            excerpt_id = row[0].strip()
            excerpt_text = row[14].strip()

            if METHOD == "LLM":
                PRECOMPUTED_GRADE_LEVEL = suffix(get_llm_score("1000_sample_orig_corrected.csv", excerpt_id, use_corrected=False))
                #print(f"Precomputed LLM grade level for ID {excerpt_id}: {PRECOMPUTED_GRADE_LEVEL}")
            if METHOD == "LLM-C":
                PRECOMPUTED_GRADE_LEVEL = suffix(get_llm_score("1000_sample_orig_corrected.csv", excerpt_id, use_corrected=True))

            if METHOD == "None":
                prompt = (
                    # The prompt to use when the LLM won't calculate a grade level before rewriting (at least not explicitly)
                    f"Please rewrite the following text to be suitable for a {dgl_str}-grade reading level).\n"
                    # The rest of the prompt
                    "Make sure the rewritten text is the last part of your response, and make sure the line 'Rewritten Excerpt:' precedes it (no bold or other formatting). (If you believe the text is already at or below the desired reading level, simply put 'Excerpt already at or below desired grade level.' in place of a rewritten excerpt.\n"
                    "Excerpt:\n"
                    f"{excerpt_text}"
                )
            elif METHOD in ["LLM", "LLM-C"]:
                prompt = (
                    # The prompt to use when the LLM won't calculate a grade level before rewriting (at least not explicitly)
                    f"Please rewrite the following text to be suitable for a {dgl_str}-grade reading level). The excerpt is currently at {PRECOMPUTED_GRADE_LEVEL}-grade level.\n"
                    # The rest of the prompt
                    "Make sure the rewritten text is the last part of your response, and make sure the line 'Rewritten Excerpt:' precedes it (no bold or other formatting). (If you believe the text is already at or below the desired reading level, simply put 'Excerpt already at or below desired grade level.' in place of a rewritten excerpt.\n"
                    "Excerpt:\n"
                    f"{excerpt_text}"
                )
            else:
                prompt = (
                    # --- The prompt for iterative rewriting (i.e. rewrite until the grade level is appropriate) ---
                    #f"Please rewrite the following text to be suitable for a {dgl_str}-grade reading level (make sure to compute the grade level of the excerpt before you rewrite it, and put your rewritten text as the input to the compute grade level function, if the function says the grade level is is within +- 1 grade level of desired grade then you can stop. (And if the text is already at or below the desired reading level, simply print 'Excerpt already at or below desired grade level.')"
                    f"You are tasked with rewriting the following text excerpt to be suitable for a {dgl_str}-grade reading level. First, you must compute the grade level of the excerpt with the compute_grade_level function. If the text is already at or below the {dgl_str}-grade reading level, print 'Excerpt already at or below desired grade level.' and terminate. If the text excerpt is above the {dgl_str}-grade reading level, rewrite the text and input it into the compute_grade_level function to check the grade level of the rewritten text. Continue this process iteratively until the grade level of the rewritten text is within one grade level of the desired {dgl_str}-grade reading level. And print the last rewritten excerpt preceded by the line 'Rewritten Excerpt:' (no bold or other formatting).\n"
                    # --- The prompt for a single rewrite (i.e. don't check the grade level of the rewritten text) ---
                    #f"Please rewrite the following text to be suitable for a {dgl_str}-grade reading level (make sure to compute the grade level of the excerpt before you rewrite it).\n"
                    #"Make sure the rewritten text is the last part of your response, and make sure the line 'Rewritten Excerpt:' precedes it (no bold or other formatting). (And if the text is already at or below the desired reading level, simply put 'Excerpt already at or below desired grade level.' in place of a rewritten excerpt.\n"
                    "Excerpt:\n"
                    f"{excerpt_text}"
                )
            

            response, log, num_rewrites = safe_query_ollama(prompt)
            parts = response.split('Rewritten Excerpt:', 1) # split the model response at "header" for rewritten excerpt 
            final_response = parts[-1] # Extract just the final rewritten excerpt (the entire chat log is preserved in 'log')
            print(f"\nFinal Response: {final_response}\n\n")
            writer.writerow([excerpt_id] + [desired_grade_level] + [final_response] + [num_rewrites] + [int(textstat.flesch_kincaid_grade(final_response))] + [int(textstat.automated_readability_index(final_response))] + [int(textstat.smog_index(final_response))] +[log])
            #print("Model Response:\n", response)
    end_time = time.time()
    print(f"Done in {end_time-start_time} seconds. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
