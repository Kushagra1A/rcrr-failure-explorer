"""
RCRR failure case study: all checks in one script.

Run from the root of the cloned rcrr-bench repo:
    python rcrr_case_study.py

Offline, no API keys. Reads only files already in the repo and writes failures14.csv.
Setup follows the repo's published configuration: reader gpt54mini, judge gemini35flash.
Scoring recovered from the data: judge score 2 = 1.0, 1 = 0.5, 0 = 0,
over the 'kept' + 'mapping' questions (1,410 in total).
"""
import csv
import glob
import json
import re
from collections import Counter, defaultdict

READER = "gpt54mini"
JUDGE = "score_gemini35flash"      # published judge
JUDGE_OTHER = "score_gpt54mini"    # the second judge
FRONTIER = "nebula_staging_tuned_v6"
TOP_VLMS = ["fable5_img", "gpt56sol_img", "gemini31pro_img"]
MAIN = ("kept", "mapping")         # 'review' questions are left out


def load(system):
    path = f"experiments/v3/{READER}/{system}.jsonl"
    with open(path, encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def main_rows(data):
    return {t: r for t, r in data.items() if r["v3_status"] in MAIN}


def half_credit(data, statuses, cell=None):
    vals = [r[JUDGE] / 2 for r in data.values()
            if r["v3_status"] in statuses and (cell is None or r["cell"] == cell)]
    return round(100 * sum(vals) / len(vals), 1), len(vals)


def load_questions():
    qs = {}
    for f in glob.glob("public_data/qa*/**/*.json", recursive=True):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if isinstance(data, list):
            for q in data:
                if isinstance(q, dict) and "task_id" in q:
                    qs[q["task_id"]] = q
    return qs


def numbers(text):
    return set(re.findall(r"\d[\d,\.]*\d|\d", str(text)))


# ---------------------------------------------------------------- 1. reproduce
print("=" * 70)
print("1. REPRODUCE THE PUBLISHED SCORES (half credit, kept + mapping)")
print("=" * 70)
F = load(FRONTIER)
V = {s: load(s) for s in TOP_VLMS}
for name, data in [(FRONTIER, F), ("fable5_img", V["fable5_img"])]:
    overall, n = half_credit(data, MAIN)
    map_chart, n1 = half_credit(data, ("mapping",), "jp_chart")
    kept_chart, n2 = half_credit(data, ("kept",), "jp_chart")
    print(f"{name:26} overall {overall} (n={n}) | "
          f"mapping charts {map_chart} (n={n1}) | kept charts {kept_chart} (n={n2})")
print("README says: Frontier 94.4 overall / 94.7 charts; Fable 5 94.6 / 98.1")

# ------------------------------------------------------------- 2. the failures
print("\n" + "=" * 70)
print("2. QUESTIONS FRONTIER FAILED THAT ALL THREE TOP VLMS PASSED")
print("=" * 70)
Fm = main_rows(F)
fail_all = [t for t, r in Fm.items() if r[JUDGE] == 0]
fail14 = [t for t in fail_all
          if all(t in V[s] and V[s][t][JUDGE] == 2 for s in V)]
frontier_only = [t for t, r in Fm.items() if r[JUDGE] == 2 and
                 all(t in V[s] and V[s][t][JUDGE] == 0 for s in V)]
print("Frontier scored 0 on:", len(fail_all), "questions")
print("...and all three VLMs scored 2 on:", len(fail14))
print("Frontier 2 and all three VLMs 0 on:", len(frontier_only))
print("By status/cell:", dict(Counter((Fm[t]["v3_status"], Fm[t]["cell"]) for t in fail14)))
print("By company (securities code):",
      dict(Counter(t.split("_")[1] for t in fail14)))

qs = load_questions()
out = []
for t in fail14:
    q = qs.get(t, {})
    out.append({
        "task_id": t, "status": Fm[t]["v3_status"], "cell": Fm[t]["cell"],
        "level": Fm[t]["level"],
        "question": q.get("question", "NOT FOUND"), "gold": q.get("answer", ""),
        "frontier_answer": Fm[t]["answer"],
        "fable5_answer": V["fable5_img"][t]["answer"],
        "gpt56sol_answer": V["gpt56sol_img"][t]["answer"],
        "gemini31pro_answer": V["gemini31pro_img"][t]["answer"],
    })
with open("failures14.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print("Wrote failures14.csv with", len(out), "rows")

# ------------------------------------------------------- 3. judge agreement
print("\n" + "=" * 70)
print("3. DO THE TWO JUDGES AGREE? (Frontier answers, kept + mapping)")
print("=" * 70)
pairs = Counter((r[JUDGE_OTHER], r[JUDGE]) for r in Fm.values())
agree = sum(v for (a, b), v in pairs.items() if a == b)
hard = pairs[(0, 2)] + pairs[(2, 0)]
print("Score pairs (gpt54mini judge, gemini35flash judge):", dict(pairs))
print(f"Same score on {agree} of {len(Fm)} ({100 * agree / len(Fm):.1f}%); "
      f"hard disagreements (0 vs 2): {hard}")

# ---------------------------------------------- 4. trace wrong numbers
print("\n" + "=" * 70)
print("4. IS A WRONG NUMBER THE GOLD ANSWER OF ANOTHER QUESTION ON THE PAGE?")
print("=" * 70)
for row in out:
    t = row["task_id"]
    page = t.rsplit("_", 1)[0]
    wrong = numbers(row["frontier_answer"]) - numbers(row["gold"])
    print(f"\n{t} | Frontier: {row['frontier_answer'][:50]}")
    if not wrong:
        print("   (no wrong numbers to trace)")
        continue
    found = False
    for other_id, q in qs.items():
        if other_id != t and other_id.rsplit("_", 1)[0] == page:
            shared = wrong & numbers(q.get("answer", ""))
            if shared:
                found = True
                print("   number", shared, "is the gold answer of", other_id)
                print("   that question:", q.get("question", "")[:70])
    if not found:
        print("   wrong number", wrong, "not found in other gold answers on this page")
print("\nNote: small numbers such as years can match by coincidence.")

# --------------------------------------------- 5. version-to-version churn
print("\n" + "=" * 70)
print("5. HOW MUCH DO RESULTS FLIP BETWEEN NEBULA VERSIONS? (kept + mapping)")
print("=" * 70)
for other in ["nebula_cloud", "nebula_staging_tuned"]:
    O = main_rows(load(other))
    lost = sum(1 for t, r in Fm.items() if t in O and r[JUDGE] == 0 and O[t][JUDGE] == 2)
    won = sum(1 for t, r in Fm.items() if t in O and r[JUDGE] == 2 and O[t][JUDGE] == 0)
    print(f"v6 vs {other}: v6 failed/other passed = {lost}, "
          f"v6 passed/other failed = {won}, flips in total = {lost + won}")
print("Each system was run once, so some flips may be run-to-run noise.")
