import ollama
import textstat
import time
import csv
import re


MODEL = "gpt-oss:20b"
INPUT_FILE = "CLEAR_1000_sample.csv"      
OUTPUT_FILE = "LLM_Flesch_Kincaid_write_2.csv"    
ENCODING= 'utf-8' #'windows-1252' #'utf-8'
DESIRED_GRADE_LEVEL = "5th" # adjust this to select the desired grade level output
METHOD = "FK" # "FK"-Flesch-Kincaid Grade Level, "SMOG"-SMOG, "ARI"-Automated Readability Index, "DC"-Dale-Chall

# Function to compute grade level using textstat
def compute_grade_level(text: str) -> int:
    """
    uncomment the return line for the desired grade level computation method
    """
    print(f"Computing grade level for text:\n {text}\n\n")
    if (METHOD == "FK"):
        return int(textstat.flesch_kincaid_grade(text)) # Flesch-Kincaid grade level
    elif (METHOD == "SMOG"):
        return int(textstat.smog_index(text))  # SMOG index grade level
    elif (METHOD == "ARI"):
        return int(textstat.automated_readability_index(text))  # Automated Readability Index grade level
    elif (METHOD == "DC"):
        return int(textstat.dale_chall_readability_score(text))  # Dale-Chall grade level
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

def query_ollama_iterative(prompt: str) -> tuple(str, str):
    messages = [{'role': 'user', 'content': prompt}]
    conversation = f"User: {prompt}\n\n"

    
    while True:
        response = ollama.chat(model=MODEL, messages=messages, tools=[compute_grade_level_tool])
        conversation += f"Model: {response['message']['content']}\n\n"
        tool_calls = response['message'].get('tool_calls', [])
        
        if not tool_calls:
            return response['message']['content'], conversation
        
        for call in tool_calls:
            tool_name = call[['function']'name']
            tool_args = call['function']['arguments']
            result = handle_tool_call(tool_name, tool_args)
            print(f"Tool '{tool_name}' -> {result}")

            conversation += f"Tool Call: {tool_name} with args {tool_args}\n"
            conversation += f"Tool Result: {result}\n\n"
            
            messages.append({'role': 'tool', 'name': tool_name, 'content': str(result)})


def query_ollama(prompt: str) -> tuple[str, str]:
    """
    Query Ollama model with single tool-call handling.
    Returns the final response as the first string, and the full conversation log as the second string.
    """
    conversation = f"User: {prompt}\n\n"
    response = ollama.chat(
        model=MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        tools=[compute_grade_level_tool],
    )
    conversation += f"Model: {response['message']['content']}\n\n"
    # Check if the model called a tool
    if 'tool_calls' in response['message'] and response['message']['tool_calls']:
        for call in response['message']['tool_calls']:
            tool_name = call['function']['name']
            tool_args = call['function']['arguments']
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
    return response['message']['content']


def main():

    start_time = time.time()
    with open(INPUT_FILE, newline='', encoding=ENCODING) as infile, \
         open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        header = next(reader)  # skip header row
        writer.writerow(["ID"] + [f"Rewritten Excerpt"] + ["Full Chat Log"])
        i = 0
        for row in reader:
            # Skip rows that are completely empty or only contain whitespace
            if not row or all(cell.strip() == "" for cell in row):
                print("Reached empty row — stopping.")
                break
            if i >= 1: # limit to first 1 sample for testing (remove when doing full run) IMPORTANT
                break
            i += 1

            excerpt_id = row[0].strip()
            excerpt_text = row[14].strip()

            prompt = (
                # The prompt for iterative rewriting (i.e. rewrite until the grade level is appropriate)
                #f"Please rewrite the following text to be suitable for a {DESIRED_GRADE_LEVEL}-grade reading level (make sure to compute the grade level of the excerpt before you rewrite it, and compute grade level of the rewritten text to double check it is within +- 1 grade level of desired grade).\n"
                # The prompt for a single rewrite (i.e. don't check the grade level of the rewritten text)
                f"Please rewrite the following text to be suitable for a {DESIRED_GRADE_LEVEL}-grade reading level (make sure to compute the grade level of the excerpt before you rewrite it).\n"
                # The rest of the prompt
                "Make sure the rewritten text is the last part of your response, and make sure the line 'Rewritten Excerpt:' precedes it (no bold or other formatting). (And if the text is already at the desired reading level, simply put 'Excerpt already at desired grade level.' in place of a rewritten excerpt.\n"
                "Excerpt:\n"
                f"{excerpt_text}"
            )
            

            response, log = query_ollama(prompt)
            parts = response.split('Rewritten Excerpt:', 1) # split the model response at "header" for rewritten excerpt 
            final_response = parts[-1] # Extract just the final rewritten excerpt (the entire chat log is preserved in 'log')
            writer.writerow([excerpt_id] + [final_response] +[log])
            #print("Model Response:\n", response)

if __name__ == "__main__":
    main()
