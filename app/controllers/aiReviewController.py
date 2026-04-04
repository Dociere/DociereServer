import json
import re

# -------------------------------------------------------
# Category labels used in the prompt and returned in JSON
# -------------------------------------------------------
CATEGORY_DESCRIPTIONS = {
    "grammar":   "grammar, spelling, punctuation, and sentence fluency in text content",
    "syntax":    (
        "LaTeX command correctness and compilation safety — this INCLUDES: "
        "(a) math expressions written outside $...$ or \\[...\\] delimiters, "
        "(b) unclosed environments (\\begin without \\end), "
        "(c) undefined or misspelled LaTeX commands, "
        "(d) missing required arguments to commands, "
        "(e) improperly escaped special characters (&, %, $, #, _, {, }) in text mode"
    ),
    "structure": "academic structure, logical flow, argument coherence, and section organisation",
    "style":     "academic tone, word choice, formality, and clarity",
}

STRICTNESS_DESCRIPTIONS = {
    "light":  "Only flag clear, obvious errors. Do not nitpick.",
    "normal": "Flag meaningful improvements while ignoring trivial ones.",
    "strict": "Be thorough. Flag every possible improvement, including minor stylistic ones.",
}


def generate_review_prompt(latex_content, review_options=None):
    """
    Build a numbered-line review prompt for the LLM.

    Parameters
    ----------
    latex_content : str
        The raw LaTeX source to review.
    review_options : dict, optional
        {
          "categories": ["grammar", "syntax", "structure", "style"],   # subset allowed
          "strictness": "light" | "normal" | "strict"
        }
    """
    if review_options is None:
        review_options = {}

    # Resolve categories
    requested_cats = review_options.get("categories") or list(CATEGORY_DESCRIPTIONS.keys())
    # Only keep recognised categories
    active_cats = [c for c in requested_cats if c in CATEGORY_DESCRIPTIONS]
    if not active_cats:
        active_cats = list(CATEGORY_DESCRIPTIONS.keys())

    # Resolve strictness
    strictness = review_options.get("strictness", "normal")
    if strictness not in STRICTNESS_DESCRIPTIONS:
        strictness = "normal"

    category_block = "\n".join(
        f'  - "{cat}": review for {CATEGORY_DESCRIPTIONS[cat]}'
        for cat in active_cats
    )
    strictness_note = STRICTNESS_DESCRIPTIONS[strictness]

    # Prepend line numbers to the content
    lines = latex_content.split("\n")
    numbered_lines = [f"{i + 1}: {line}" for i, line in enumerate(lines)]
    numbered_content = "\n".join(numbered_lines)

    prompt = f"""You are an expert academic LaTeX Editor and Reviewer.
Your task is to carefully review the following LaTeX document for issues.

REVIEW SCOPE — produce suggestions ONLY for these categories:
{category_block}

STRICTNESS: {strictness_note}

{'CRITICAL: When "syntax" is in scope, you MUST flag ALL math expressions that appear outside LaTeX math mode (i.e. not inside $...$, \\(...\\), \\[...\\], or math environments like equation/align). These are compilation errors.' if 'syntax' in active_cats else ''}

OUTPUT FORMAT — return ONLY a valid JSON array. Each element must have ALL these fields:
[
  {{
    "line": <integer: exact 1-indexed line number from the DOCUMENT CONTENT below>,
    "original_text": "<the exact string from that line being corrected>",
    "suggestion": "<your improved replacement>",
    "reasoning": "<brief explanation>",
    "type": "<one of: {', '.join(active_cats)}>"
  }}
]

STRICT RULES:
1. Output ONLY the JSON array. No markdown fences, no extra text.
2. "type" must be one of: {json.dumps(active_cats)}. Discard suggestions outside these categories.
3. Escape LaTeX backslashes in JSON strings (e.g. \\\\textbf not \\textbf).
4. SKIP these — they are intentional boilerplate that should NOT be changed:
   - \\documentclass, \\usepackage, \\begin{{document}}, \\end{{document}}
   - Standard author/title/date macros with placeholder text
   - Structural commands that are already correct (\\section, \\subsection, etc.)
5. "original_text" must be a verbatim substring of the line at "line" (no line-number prefix).
6. Return at most 25 suggestions. Prioritise errors that would cause compilation failure first.
7. If you find zero issues, return: []

DOCUMENT CONTENT (line numbers shown as prefix for reference only):
{numbered_content}
"""
    return prompt


def parse_review_response(raw_text):
    """
    Parse the LLM response into a validated list of suggestion dicts.
    Returns {{"success": True, "suggestions": [...]}} or an error dict.
    """
    # Strip any accidental markdown code fences
    text = re.sub(r"^```(json)?\s*", "", raw_text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Attempt aggressive repair: fix unescaped backslashes in string values
        repaired = _repair_json(text)
        try:
            data = json.loads(repaired)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse JSON after repair: {str(e)}",
                "raw_text": text[:500],
            }

    if not isinstance(data, list):
        return {
            "success": False,
            "error": "AI response is not a JSON array.",
            "raw_text": text[:500],
        }

    # Validate and sanitise each suggestion
    valid = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if not all(k in item for k in ("line", "original_text", "suggestion", "reasoning")):
            continue
        # Coerce types
        try:
            item["line"] = int(item["line"])
        except (ValueError, TypeError):
            continue
        item["type"] = item.get("type", "grammar")
        valid.append(item)

    return {"success": True, "suggestions": valid}


# -------------------------------------------------------
# Internal JSON repair helper
# -------------------------------------------------------
def _repair_json(json_str):
    """Fix unescaped backslashes inside JSON string values."""
    VALID_ESCAPES = set('"\\bfnrtu/')
    result = []
    i = 0
    in_string = False
    while i < len(json_str):
        ch = json_str[i]
        if ch == '"' and (i == 0 or json_str[i - 1] != "\\"):
            in_string = not in_string
            result.append(ch)
            i += 1
        elif in_string and ch == "\\":
            if i + 1 < len(json_str):
                nxt = json_str[i + 1]
                if nxt in VALID_ESCAPES:
                    result.append(ch)
                    result.append(nxt)
                    i += 2
                else:
                    result.append("\\\\")
                    i += 1
            else:
                result.append("\\\\")
                i += 1
        else:
            result.append(ch)
            i += 1
    return "".join(result)
