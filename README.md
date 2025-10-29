# Evaluating and Improving Readability Control in Large Language Models via Tool-Augmented Feedback

---

## Overview

{TODO: Write overview of repository}

### Tasks Completed

- [x] Create functions to calculate readability metrics (we made use of the [textstat](https://github.com/textstat/textstat) library for the sake of standardization)

- [x] Sample CLEAR corpus into 1000 excerpts and calculate heuristic readability metrics

- Run LLM on sampled excerpts to obtain inferred readability metrics:
  
  - [x] US Grade Level (1-12
  
  - [ ] Difficulty on scale 1-10

- [ ] Create Ollama tool(s) to allow LLM to generate readability metric for a given piece of text
  
  - [ ] Create Ollama tool(s) to allow LLM to refine output of simplified text by checking readability metric of simplified text, comparing against desired readability metric score, and deciding if simplified text falls within margin of desired score, or if further refinement should be done (and conduct further refinement)

- [ ] Test refinement tools on sampled excerpts

- [ ] Quantitatively analyze tool-augmented results

- [ ] Qualitatively analyze tool-augmented results

- [x] Analyze non-tool-assisted LLM ability to generate readability scores of excerpts from books of qualitatively "known" readability scores.
  
  - [ ] Potentially assess excerpts from more books of "known" qualitative readability score

## Running the Code

First one must install Ollama from their [GitHub](https://github.com/ollama/ollama) or [website](https://ollama.com/).

GPT-OSS-20b is used for this project, and can be installed with `ollama fetch gpt-oss:20b`

To run LLM inference of Grade Level or Difficulty (non-tool-assisted), serve ollama with `ollama serve`, and in another terminal run `python AskGradeLevel.py` or `python AskReadability.py`. These files grab excerpts from the `CLEAR_1000_sample.csv` file by default. Input and output files can be specified by modifying the python files.

{TODO: Insert more directions for running code here, and what different files do.}

{TODO: edit AskGradeLevel.py to take input parameters for input file, output file, input file rows for excerpt ID and excerpt text, and selection for which prompt to use (Grade Level or Score 1-10), input for row range (e.x. only want to analyse row50:row100}

## Notice of Fair Use

For the purpose of qualitative analysis, excerpts from several books which are not yet in the public domain were used[^1], all copyrights belong to their respective owners.

**Purpose and Character of Use:** The excerpts are being used for research and analytical purposes in an educational setting, specifically, for a class project. The text excerpts are being used for the sake of readability analysis. No commercial gain has been taken from these works or the use thereof.

**Nature of the Copyrighted Work:** While the excerpts are taken from creative works, rather than factual ones, we are interested in analyzing the linguistic structure and readability of creative works, which are often structured different from factual works. 

**Amount and Substantiality of the Portion Taken:** Each work not yet in the public domain used in our qualitative analysis only had an exceptionally small portion used. Specifically, 5 randomly selected paragraphs were taken from each book and recorded for use. This comes nowhere close to the full text, and is not representative of the "heart" of the work.

**Effect of the Use on the Potential Market:** These excerpts could not be used as a substitute for the full book, or be used to reconstruct the full book, and would thus have no impact on sales.

[^1]: Lasky, Kathryn (2010). Guardians of Ga'Hoole: The Siege. Scholastic. ISBN: 9780545283359.
  Lasky, Kathryn (2008). Guardians of Ga'Hoole: The War of the Ember. Scholastic Paperbacks. ISBN: 9780439888097.
  Lee, Harper (1960). To Kill A Mockingbird. HarperCollins. ISBN: 9780446310789.

## License

The contents of this repository are provided under a CC BY-NC-SA 4.0 DEED Attribution-NonCommercial-ShareAlike 4.0 International license (https://creativecommons.org/licenses/by-nc-sa/4.0/deed.en), with exceptions made for content as noted below.

> **Fair Use and Third-Party Content**
> 
> This repository includes short excerpts from copyrighted literary works for the purpose of linguistic and readability analysis.
> These excerpts are used under *fair use* (17 U.S.C. §107) for educational, non-commercial research.
> Copyright in those excerpts remains with their original authors or publishers.
> No part of those works is licensed under this repository’s main license.

In addition, the CommonLit CLEAR Corpus used in this and it's content are also provided under the CC BY-NC-SA 4.0 DEED Attribution-NonCommercial-ShareAlike 4.0 International license.
