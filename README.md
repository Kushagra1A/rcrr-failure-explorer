# RCRR Failure Case Study: Nebula Frontier

A small, checked look at where **Nebula Frontier** loses points in Ur AI's public
[RCRR benchmark](https://github.com/ur-ai-net/rcrr-bench), built only from the data in that repo.

## What I did

1. Reproduced the published scores offline from the per-question results.
2. Found the questions Nebula Frontier failed while the strongest VLMs passed.
3. Read those failures one by one (in English translation), grouped them by failure type, and checked what I could against the data.
4. Tested my own first hypothesis ("v6 regressed from earlier Nebula versions"). It was wrong, and the result is below.

## Setup (matches the repo's published configuration)

- Reader: `gpt54mini`. Judge: `score_gemini35flash`. Nebula Frontier = `nebula_staging_tuned_v6`.
- Scoring I recovered from the data: all 1,410 questions (`kept` 1,053 + `mapping` 357), judge score 2 = 1.0, 1 = 0.5, 0 = 0.
- With that rule I get **94.4 for Frontier and 94.6 for Fable 5**, the same as the README table.

## Findings

**1. The README's "Charts" column is a subset.** It matches only the `mapping` chart questions (207 questions: Frontier 94.7, Fable 5 98.1). On the main `kept` chart set (389 questions) the two are close: Frontier 95.5, Fable 5 95.2. A chart-weakness claim therefore depends on which subset is used. (Fable 5 also helped author the chart gold answers, which the repo calls a "reference ceiling".) I could not reproduce the "Text & tables" column, so I make no claim about it.

**2. 14 questions where Frontier scored 0 and Fable 5, GPT-5.6 Sol and Gemini 3.1 Pro all scored 2** (out of 56 questions Frontier scored 0 on). Eight are from the `kept` set (5 table, 3 chart) and six are `mapping` chart questions. Failure types:

| Type | Count | Example |
|---|---|---|
| Wrong chart value or year | 6 | "Q4 plan at end-November": gold 871, answered 5,600 |
| Wrong number in a table | 4 | "Properties with planned works over 80M": gold 4, answered 5 |
| Answered "no information" where the others found the answer | 3 | Legend colour, tenant-consent footnote, sales channels |
| Vague answer | 1 | Named a "growth-stage flow" instead of the specific items |

Full table: [`failures14.csv`](failures14.csv).

**3. What I could check against the data.** In one case the wrong answer (5,600) is exactly the gold answer to a *different* question on the same page (the "revised budget" value), so Frontier read a neighbouring item in the same chart. A second case (a timeline year) is consistent with the same thing but could be a coincidence. For the other 12 I cannot say what went wrong without the page images.

**4. Six of the 14 come from one company (code 3623), on two pages.** These are not six independent failures.

**5. The judges mostly agree.** On Frontier's answers the two judges give the same score on 1,373 of 1,410 questions (97.4%), and only 4 are hard disagreements (0 vs 2). I found no format-only failures among the 14, so judge strictness is not what drives them.

**6. A hypothesis I got wrong.** The 14 failures made v6 look like a regression, with earlier Nebula versions passing many of them. Over all 1,410 questions, v6 failed 17 that `nebula_cloud` passed but passed 35 that `nebula_cloud` failed. Against `nebula_staging_tuned` it is 12 lost and 19 gained. The 14 looked bad only because I selected each system's worst questions. The real observation is that many questions flip between versions (52 and 31), so comparisons on single questions are weak evidence.

## Limits

- **Translations are LLM-made.** I cannot read Japanese, and the English in this repo is an LLM translation I could not verify myself.
- **No source PDFs and no converted Markdown.** I can say where the final answer was wrong, not why the converter produced it. Any cause beyond that would be a guess.
- **Each system was run once**, so differences between versions may partly be run-to-run noise.
- **Small samples.** Fourteen questions cannot support statistical claims about chart or table performance.
- I did not re-run the benchmark or evaluate new systems.

## Possible next steps

Find the source pages on the companies' IR sites and check the failures against the page layout. Add an interactive explorer over the same per-question data. Compare with the repo's paired per-page statistics.

## Reproduce

Clone the benchmark repo, then run the scripts here from its root folder. Everything is offline and uses only the files already in that repo.

Data and results belong to Ur AI under Apache-2.0. Source documents belong to their issuers.
