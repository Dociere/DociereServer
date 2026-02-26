from flask import Blueprint, request, jsonify
import os
import re
import logging
import json
from dotenv import load_dotenv
from google import genai
import render_strategies as rs
import difflib

load_dotenv()
logger = logging.getLogger(__name__)
latex_bp = Blueprint("latex", __name__)

# Initialize API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY is missing in environment variables.")

client = genai.Client(api_key=GEMINI_API_KEY)

# 1. Template Registry
TEMPLATE_REGISTRY = {
  "ai4x": ["Introduction", "Main Content", "Related Work", "Acknowledgments", "Appendices"],
  "springer_nature": ["Introduction", "Results", "Discussion", "Methods", "Conclusion", "Declarations", "Supplementary Information", "Acknowledgments", "Appendices"],
  "ieee_transmag": ["Introduction", "Methodology", "Results", "Conclusion", "Acknowledgment", "Appendices", "Biographies"],
  "ieee_tmi": ["Introduction", "Guidelines for Manuscript Preparation", "Math", "Units", "Guidelines for Graphics Preparation", "Conclusion", "Appendix", "Acknowledgment", "References"],
  "ieee_journal": ["Introduction", "System Model", "Methodology", "Results", "Conclusion", "Acknowledgments", "Appendices", "Biographies"],
  "ieee_tns": ["Introduction", "Structure of Paper", "Experimental Setup", "Data Analysis", "Conclusion", "Appendix", "Acknowledgment", "References"],
  "ieee_journal_letters": ["Introduction", "System Model", "Methodology", "Results", "Conclusion", "Appendix", "Acknowledgment", "References"],
  "mdpi": ["Introduction", "Materials and Methods", "Results", "Discussion", "Conclusions", "Author Contributions", "Funding", "Institutional Review Board Statement", "Informed Consent Statement", "Data Availability Statement", "Acknowledgments", "Conflicts of Interest"],
  "acm_manuscript": ["Introduction", "Related Work", "Methodology", "Experiments", "Results", "Conclusion", "Acknowledgments", "Appendices"],
  "cell_press": ["Introduction", "Results", "Discussion", "Methods", "Resource Availability", "Acknowledgments", "Author Contributions", "Declaration of Interests", "Declaration of Generative AI", "Figure Legends", "Tables"],
  "acs": ["Introduction", "Results and discussion", "Experimental", "Conclusion", "Acknowledgements", "Supporting information"],
  "frontiers": ["Introduction", "Material and Methods", "Results", "Discussion", "Conflict of Interest Statement", "Author Contributions", "Funding", "Acknowledgments", "Data Availability Statement"],
  "elsarticle": ["Introduction", "Methodology", "Results", "Discussion", "Conclusion", "Acknowledgments", "Appendices", "References"],
  "ajp": ["Introduction", "Theory", "Experiment", "Results", "Conclusion", "Appendix", "Acknowledgments"],
  "aip": ["Lead Paragraph", "Introduction", "Theory", "Results", "Conclusion", "Acknowledgments", "Data Availability Statement", "Appendix"],
  "science": ["Introduction", "Results", "Discussion", "Materials and Methods", "Acknowledgments", "Supplementary Materials"],
  "rsc": ["Introduction", "Graphics and tables", "Equations", "Conclusions", "Author contributions", "Conflicts of interest", "Data availability", "Acknowledgements"],
  "asm_journal": ["Importance", "Introduction", "Materials and Methods", "Results", "Discussion", "Acknowledgments", "Funding", "Conflicts of Interest", "Data Availability Statement", "References"],
  "asme": ["Introduction", "Methodology", "Results", "Discussion", "Conclusion", "Acknowledgment", "Funding Data", "Nomenclature", "Appendices"],
  "ams_tran": ["Introduction", "Main Results", "Proofs", "Conclusion", "References"],
  "ios_book_article": ["Introduction", "Typographical Style and Layout", "Illustrations", "Equations", "Fine Tuning", "Submitting the Manuscript", "References"],
  "spie_journal": ["Introduction", "Methodology", "Results", "Discussion", "Conclusion", "Appendices", "Disclosures", "Code, Data, and Materials Availability", "Acknowledgments", "Biographies"],
  "ieee": ["Introduction", "Methodology", "Results and Discussions", "Conclusion"],
  "mla": ["Abstract", "Introduction", "Body Paragraphs", "Conclusion", "Works Cited"]
}

# 2. Mapping Template Keys to Render Functions
RENDERER_MAP = {
    "ai4x": "generate_ai4x_latex",
    "springer_nature": "generate_springer_latex",
    "ieee_transmag": "generate_transmag_latex",
    "ieee_tmi": "generate_tmi_latex",
    "ieee_journal": "generate_ieee_journal_latex",
    "ieee_tns": "generate_tns_latex",
    "ieee_journal_letters": "generate_ieee_journal_letters_latex",
    "mdpi": "generate_mdpi_latex",
    "acm_manuscript": "generate_acm_latex",
    "cell_press": "generate_cell_press_latex",
    "acs": "generate_acs_latex",
    "frontiers": "generate_frontiers_latex",
    "elsarticle": "generate_elsarticle_latex",
    "ajp": "generate_ajp_latex",
    "aip": "generate_aip_latex",
    "science": "generate_science_latex",
    "rsc": "generate_rsc_latex",
    "asm_journal": "generate_asm_latex",
    "asme": "generate_asme_latex",
    "ams_tran": "generate_ams_tran_latex",
    "ios_book_article": "generate_ios_press_latex",
    "spie_journal": "generate_spie_latex",
    "ieee": "generate_ieee_journal_latex",
    "mla": "generate_mla_latex"
}

def repair_json(json_str):
    """Aggressively repair JSON with unescaped LaTeX backslashes."""
    # 1. Strip Markdown code blocks
    json_str = re.sub(r'^```(json)?\s*', '', json_str, flags=re.IGNORECASE)
    json_str = re.sub(r'\s*```$', '', json_str)
    json_str = json_str.strip()

    # 2. Remove trailing commas (common AI error)
    json_str = re.sub(r',\s*([\]}])', r'\1', json_str)

    # 3. Character-level backslash repair inside JSON string values.
    #    Walk through the string; when inside a quoted value, ensure every
    #    backslash that is NOT already a valid JSON escape is doubled.
    VALID_ESCAPES = set('"\\bfnrtu/')
    result = []
    i = 0
    in_string = False
    while i < len(json_str):
        ch = json_str[i]
        if ch == '"' and (i == 0 or json_str[i - 1] != '\\'):
            in_string = not in_string
            result.append(ch)
            i += 1
        elif in_string and ch == '\\':
            # Check what follows the backslash
            if i + 1 < len(json_str):
                next_ch = json_str[i + 1]
                if next_ch in VALID_ESCAPES:
                    # Already a valid JSON escape – keep as-is
                    result.append(ch)
                    result.append(next_ch)
                    i += 2
                else:
                    # Not a valid JSON escape (LaTeX command like \section)
                    # Double the backslash so JSON sees \\
                    result.append('\\\\')
                    i += 1  # leave next_ch to be processed normally
            else:
                # Trailing backslash – escape it
                result.append('\\\\')
                i += 1
        else:
            result.append(ch)
            i += 1

    return ''.join(result)

# --- UTILS ---
def validate_latex_security(latex_content):
    """Scans LaTeX content for dangerous commands."""
    forbidden_patterns = [
        r"\\write18", r"\\immediate", r"\\input", r"\\include", r"\\openin", 
        r"\\openout", r"\\newwrite", r"\\usepackage.*{shellesc}", r"\\xdef", r"\\catcode"
    ]
    for pattern in forbidden_patterns:
        if re.search(pattern, latex_content, re.IGNORECASE):
            return False, f"Forbidden command detected: {pattern}"
    return True, "Safe"

def clean_latex_response(text):
    text = re.sub(r'^```(latex|tex)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()

def clean_json_response(text):
    text = re.sub(r'^```(json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    return text.strip()

@latex_bp.route('/generate-boilerplate', methods=['POST'])
def generate_boilerplate():
    """Generate per-file content for multifile templates."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body provided"}), 400

        title = data.get('title', '')
        user_idea = data.get('userIdea', '')
        template_files = data.get('templateFiles', {})

        if not user_idea or not title:
            return jsonify({"success": False, "error": "Missing title or userIdea"}), 400

        if not template_files:
            return jsonify({"success": False, "error": "No template files provided"}), 400

        # Build a description of what each file should contain
        file_descriptions = []
        for file_key in template_files:
            # Skip non-content files
            if file_key.endswith('.gitkeep') or file_key.endswith('.cls') or file_key.endswith('.sty') or file_key.endswith('.pdf'):
                continue
            if file_key == 'main.tex' or file_key == 'authors.tex' or file_key == 'ccs.tex':
                continue  # main.tex is the template skeleton, don't generate for it
            
            file_descriptions.append(file_key)

        if not file_descriptions:
            return jsonify({"success": True, "fileContents": {}})

        prompt = f"""You are an expert academic LaTeX content generator.

Task: Generate content for a research paper titled "{title}" based on this idea: "{user_idea}"

Generate content for EACH of the following template files. Each file will be \\input{{}} into the main document(\\input{{}} already exists), so output ONLY the body content — NO \\documentclass, NO \\begin{{document}},NO \\input{{}},  NO \\section{{}} commands (the main.tex already has the section headings).

CRITICAL RULES:
1. NO MARKDOWN — use \\textbf{{}} and \\textit{{}} instead of **bold** and *italic*
2. ESCAPE special characters in text: & % $ # _ {{ }} ~ ^ \\
3. NO \\section{{}} or \\subsection{{}} commands unless the file is specifically a section body that needs subsections
4. For abstract.tex: plain text only, no commands
5. For keywords.tex: comma-separated keywords only
6. For title.tex: just the title text
7. For references.tex: \\bibitem entries only (no \\begin{{thebibliography}})
8. For section files (sections/*.tex): body content only, may include \\subsection{{}} if appropriate
9. For acknowledgment.tex: plain acknowledgment text
10. NO LATEX COMMENTS (%) to avoid commenting out subsequent code

CRITICAL JSON RULES:
- Every backslash in LaTeX commands MUST be escaped as a double-backslash in the JSON string value.
  For example: \\textbf{{bold}} must appear as \\\\textbf{{bold}} in the JSON string.
  \\subsection{{Title}} must appear as \\\\subsection{{Title}} in the JSON string.
  \\cite{{ref}} must appear as \\\\cite{{ref}} in the JSON string.
- Do NOT include any control characters, literal newlines, or unescaped special characters.
- Use \\n for newlines inside JSON string values.
- Do NOT add trailing commas after the last key-value pair.
- Do NOT wrap the output in markdown code blocks.

CRITICAL OUTPUT FORMAT:
Return ONLY valid JSON. No markdown code blocks. No extra text before or after.
The JSON should map each filename to its generated content:
{{
    {', '.join([f'"{f}": "content for {f}"' for f in file_descriptions])}
}}

Generate substantive, academic-quality content for each file based on the paper topic."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type='application/json',
            )
        )
        raw_text = response.text

        # Parse JSON response — should be valid since we used JSON mode
        file_contents = None
        try:
            file_contents = json.loads(raw_text)
        except json.JSONDecodeError as e1:
            logger.warning(f"JSON parse failed even with JSON mode: {e1}. Attempting cleanup...")
            cleaned_json = clean_json_response(raw_text)
            try:
                file_contents = json.loads(cleaned_json)
            except json.JSONDecodeError as e2:
                repaired_json = repair_json(cleaned_json)
                try:
                    file_contents = json.loads(repaired_json)
                except json.JSONDecodeError as e3:
                    logger.warning(f"JSON parse failed after repair: {e3}. Retrying with stricter prompt...")

        # Retry with a stricter prompt if all parsing attempts failed
        if file_contents is None:
            retry_prompt = f"""Generate a JSON object mapping filenames to LaTeX content for a paper titled "{title}" about: "{user_idea}"

Files to generate: {json.dumps(file_descriptions)}

RULES:
- Output ONLY body content for each file (no \\documentclass, no \\begin{{document}}, no \\section{{}}).
- All LaTeX backslashes MUST be double-escaped in JSON (e.g. \\\\textbf not \\textbf).
- Use \\n for newlines inside strings.
- NO trailing commas. NO markdown code blocks. NO comments.
- Output must be STRICTLY valid JSON that can be parsed by json.loads()."""
            try:
                retry_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=retry_prompt,
                    config=genai.types.GenerateContentConfig(
                        response_mime_type='application/json',
                    )
                )
                retry_text = retry_response.text
                try:
                    file_contents = json.loads(retry_text)
                except json.JSONDecodeError:
                    repaired_retry = repair_json(retry_text)
                    file_contents = json.loads(repaired_retry)
                logger.info("Retry succeeded for boilerplate generation.")
            except Exception as retry_err:
                logger.error(f"JSON parse failed after all attempts including retry: {retry_err}")
                return jsonify({
                    "success": False,
                    "error": "AI generated invalid JSON",
                    "details": str(retry_err)
                }), 500

        # Validate each file content for security
        for fkey, content in file_contents.items():
            if isinstance(content, str) and len(content) > 0:
                is_safe, msg = validate_latex_security(content)
                if not is_safe:
                    logger.warning(f"Security check failed for {fkey}: {msg}")
                    file_contents[fkey] = f"% Content removed for security: {msg}"

        logger.info(f"Generated boilerplate for {len(file_contents)} files")
        return jsonify({
            "success": True,
            "fileContents": file_contents
        })

    except Exception as e:
        logger.error(f"Boilerplate Generation Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@latex_bp.route('/generate-latex', methods=['POST'])
def generate_latex():
    try:
        data = request.get_json()
        if not data: return jsonify({"success": False, "error": "No JSON body provided"}), 400

        user_idea = data.get('userIdea')
        title = data.get('title')
        template_type = data.get('templateType', 'article') 
        author_details = data.get('authorDetails', {})

        if not user_idea or not title:
            return jsonify({"success": False, "error": "Missing userIdea or title"}), 400

        # --- MODE 1: BLANK DOCUMENT (Legacy) ---
        if template_type == "Blank Document":
            author_name = author_details.get('name', 'Author')
            prompt = f"""You are a LaTeX document generator. 
CRITICAL: Output ONLY raw LaTeX. Start with \\documentclass.
CRITICAL SYNTAX RULES:
1. NO MARKDOWN: Never use **bold** or *italic*. Use \\textbf{{bold}} and \\textit{{italic}}.
2. ESCAPE CHARACTERS: Escape & % $ # _ {{ }} ~ ^ \\ (e.g. use \\&).
Title: {title}
Author: {author_name}
Content: {user_idea}
"""
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            latex_content = clean_latex_response(response.text)
            
            is_safe, msg = validate_latex_security(latex_content)
            if not is_safe: return jsonify({"success": False, "error": msg}), 400

            return jsonify({"success": True, "latexContent": latex_content})

        # --- MODE 2: TEMPLATE SYSTEM (JSON + Assembly) ---
        else:
            required_sections = TEMPLATE_REGISTRY.get(template_type, ["Introduction", "Methodology", "Results", "Conclusion"])
            
            # --- MODIFIED SYSTEM PROMPT START ---
            prompt = f"""You are an expert LaTeX content generator.
Task: Generate content for a "{template_type}" paper titled "{title}".
Idea: "{user_idea}"

CRITICAL INSTRUCTIONS FOR LATEX SYNTAX:
1. **NO MARKDOWN**: Never use `**bold**` or `*italic*`. Use `\\textbf{{bold}}` and `\\textit{{italic}}`.
2. **ESCAPE CHARACTERS**: Escape the following in text: & % $ # _ {{ }} ~ ^ \\ (e.g., use `\\&` not `&`).
3. **MATH**: Use `$` for inline math. Do not escape chars inside math mode.
4. **CONTENT ONLY**: The JSON values should only contain the body text for that section.
5. **NO COMMENTS**: NO LATEX COMMENTS (%) TO AVOID ANY SUBSEQUENT CODE ON THE SAME LINE GETTING COMMENTED OUT

CRITICAL OUTPUT FORMAT:
Output ONLY valid JSON. No markdown code blocks.
Structure:
{{
    "abstract": "Abstract text here...",
    "keywords": "key1, key2...",
    "sections": {{
        "{required_sections[0]}": "Content...",
        ... (generate all required sections: {', '.join(required_sections)})
    }}
}}
"""
            response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
            raw_text = response.text
            
            # Attempt 1: Clean and Parse
            cleaned_json = clean_json_response(raw_text)
            
            try:
                content_data = json.loads(cleaned_json)
            except json.JSONDecodeError as e1:
                logger.warning(f"Initial JSON parse failed: {e1}. Attempting repair...")
                
                # Attempt 2: Repair and Parse
                repaired_json = repair_json(cleaned_json)
                try:
                    content_data = json.loads(repaired_json)
                except json.JSONDecodeError as e2:
                    logger.error(f"CRITICAL JSON ERROR after repair. \nOriginal Error: {e1}\nRepair Error: {e2}")
                    return jsonify({
                        "success": False, 
                        "error": "AI generated invalid JSON structure that could not be repaired.",
                        "details": str(e2)
                    }), 500

            # Prepare data for renderer
            authors_list = [{
                'name': author_details.get('name', 'Author Name'),
                'organization': author_details.get('affiliation', 'Organization'),
                'email': author_details.get('email', ''),
                'is_corresponding': True 
            }]
            
            journal_meta = {
                'year': '2026', 'volume': '1', 'issue': '1', 
                'journal_name': template_type.replace('_', ' ').title(),
                'date': 'January 2026'
            }

            # Find and Call Renderer
            renderer_name = RENDERER_MAP.get(template_type)
            if not renderer_name or not hasattr(rs, renderer_name):
                return jsonify({"success": False, "error": f"Renderer not found for {template_type}"}), 500
            
            renderer_func = getattr(rs, renderer_name)
            
            try:
                # Dispatch based on known signatures
                if template_type == 'ai4x':
                    conf_info = {'conference_name': 'AI Conference', 'year': '2026'}
                    final_latex = renderer_func(title, authors_list, content_data.get('abstract',''), content_data.get('sections',{}), conf_info)
                elif template_type in ['ajp', 'aip']:
                    final_latex = renderer_func(title, authors_list, content_data.get('abstract',''), content_data.get('sections',{}))
                elif template_type in ['springer_nature','acm_manuscript', 'acs', 'frontiers', 'asme', 'ios_book_article', 'spie_journal', 'science', 'asm_journal']:
                    final_latex = renderer_func(title, authors_list, content_data.get('abstract',''), content_data.get('keywords',''), content_data.get('sections',{}))
                else:
                    # Default signature (IEEE, MDPI, etc.)
                    final_latex = renderer_func(title, authors_list, content_data.get('abstract',''), content_data.get('keywords',''), content_data.get('sections',{}), journal_meta)

                is_safe, msg = validate_latex_security(final_latex)
                if not is_safe: return jsonify({"success": False, "error": msg}), 400

                return jsonify({
                    "success": True,
                    "latexContent": final_latex,
                    "projectJson": content_data 
                })

            except Exception as te:
                logger.error(f"Renderer Error: {te}")
                return jsonify({"success": False, "error": f"Template Rendering Failed: {str(te)}"}), 500

    except Exception as e:
        logger.error(f"Generation Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# latex.py

@latex_bp.route('/edit-latex', methods=['POST'])
def edit_latex():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')
        current_latex = data.get('latexContent')
        context = data.get('context')  # Optional: { title, abstractText, outline }
        file_map = data.get('fileMap')  # Optional: { "sections/intro.tex": "content...", ... }

        if not user_prompt or not current_latex:
            return jsonify({"success": False, "error": "Missing inputs"}), 400

        # Build context section for the prompt
        context_block = ""
        if context:
            if context.get('title'):
                context_block += "\nPaper Title: " + context['title']
            if context.get('abstractText'):
                context_block += "\nAbstract: " + context['abstractText']
            if context.get('outline'):
                outline_str = " → ".join(context['outline'])
                context_block += "\nDocument Sections: " + outline_str

        # Build the project files section for the prompt
        project_files_block = ""
        if file_map and isinstance(file_map, dict) and len(file_map) > 0:
            project_files_block = "\n\nPROJECT FILES:\nThe project has multiple files. Below is each file with its path and current content.\n"
            for file_path, content in file_map.items():
                project_files_block += f"\n--- FILE: {file_path} ---\n{content}\n--- END FILE: {file_path} ---\n"

        # System Prompt
        system_prompt = """You are an expert LaTeX Editor.
        Task: Modify the LaTeX document based on the user's request.

        CRITICAL SYNTAX RULES:
        1. **NO MARKDOWN**: 
           - ❌ NEVER output `**text**` or `*text*`. 
           - ✅ ALWAYS output `\\\\textbf{text}` or `\\\\textit{text}`.
           - ❌ NEVER output `### Heading`.
           - ✅ ALWAYS output `\\\\section{Heading}`.
        2. **ESCAPE TEXT CHARACTERS**: 
           - Escape & % $ # _ { } ~ ^ \\\\ in normal text (e.g. "Profit \\\\&  Loss").
        3. **PRESERVE STRUCTURE**: Do not remove \\\\begin{document} unless asked.
        4. **PRESERVE STYLING**: Do NOT remove or modify any existing styling commands with respect to the document structure(sections bold, ruled titles, etc.) that occur before \\\\begin{document}.
        5. **NO COMMENTS**: NO LATEX COMMENTS (%) TO AVOID ANY SUBSEQUENT CODE ON THE SAME LINE GETTING COMMENTED OUT
        """

        # Add file-map-aware instructions
        if file_map and len(file_map) > 0:
            system_prompt += """
        6. **MULTI-FILE PROJECT**: This is a multi-file LaTeX project. The main document uses \\\\input{} to include content from separate files. 
           - The PROJECT FILES section shows ALL project files with their paths and current content.
           - When the user asks to edit content, identify WHICH FILE contains that content and modify it there.
           - Your response MUST include a `file_updates` object mapping each modified file path to its COMPLETE new content.
           - Only include files that you actually changed in `file_updates`. Do NOT include unchanged files.
           - The `full_latex` field should contain the updated main document (only if the main document itself changed, otherwise return it unchanged).
           - File paths in `file_updates` must exactly match the paths shown in PROJECT FILES.
        """
        else:
            system_prompt += """
        6. **PRESERVE FILE MARKERS (HIGHEST PRIORITY)**: The document contains markers like `%% BEGIN_INPUT{filename.tex} %%` and `%% END_INPUT{filename.tex} %%`. These wrap content from external files loaded via \\input{}.
           - You MUST preserve ALL markers exactly as they appear.
           - You may ONLY edit the LaTeX content BETWEEN matching BEGIN/END markers.
           - NEVER remove markers. NEVER replace a marked section with inline content. NEVER delete BEGIN or END lines.
        """
        
        system_prompt += """
        CRITICAL OUTPUT FORMAT:
        Return a VALID JSON object with:
        1. "full_latex": The full, compilable main document.
        2. "changed_snippet": A short excerpt of just the modified part (for preview).
        3. "message": A brief description of what was changed.
        4. "file_updates": An object mapping file paths to their complete new content (ONLY for files that were modified). If no project files were changed (e.g. single-file project), this should be an empty object {}.
        
        Output raw JSON only. Escape backslashes in the JSON string (e.g. \\\\\\\\documentclass).
        """

        # Inject context block if available
        if context_block:
            system_prompt = system_prompt.replace(
                "Task: Modify the LaTeX document based on the user's request.",
                "Task: Modify the LaTeX document based on the user's request.\n\n        DOCUMENT CONTEXT:" + context_block
            )

        full_prompt = f"""{system_prompt}\n\nUSER: "{user_prompt}"\n\nMAIN DOCUMENT:\n{current_latex}{project_files_block}"""

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=full_prompt
        )

        # Parse JSON
        cleaned_text = clean_json_response(response.text)
        try:
            result_json = json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Try repair
            repaired = repair_json(cleaned_text)
            try:
                result_json = json.loads(repaired)
            except json.JSONDecodeError:
                logger.error("JSON Decode failed, falling back to raw text")
                result_json = {
                    'full_latex': cleaned_text,
                    'changed_snippet': '',
                    'message': 'Changes applied.',
                    'file_updates': {}
                }

        full_doc = result_json.get('full_latex', '')
        snippet = result_json.get('changed_snippet', '')
        message = result_json.get('message', 'Changes applied.')
        file_updates = result_json.get('file_updates', {})

        # --- FALLBACK: Auto-calculate Diff if Snippet is empty ---
        if not snippet or len(snippet) < 10:
            # Compare lines to find the difference
            diff = difflib.unified_diff(
                current_latex.splitlines(), 
                full_doc.splitlines(), 
                n=0, # No context lines
                lineterm=''
            )
            # Extract just the added lines (starting with +)
            changes = [line[1:] for line in diff if line.startswith('+') and not line.startswith('+++')]
            if changes:
                snippet = "\n".join(changes[:10]) # First 10 changed lines
                if len(changes) > 10: snippet += "\n..."
            elif file_updates:
                # Changes were in project files, not main doc
                changed_files = list(file_updates.keys())
                snippet = f"Modified {len(changed_files)} file(s): {', '.join(changed_files)}"
            else:
                snippet = "Modifications applied throughout the document."

        if "\\begin{document}" not in full_doc:
             return jsonify({"success": False, "error": "AI malformed the structure."}), 500

        return jsonify({
            "success": True,
            "latexContent": full_doc,
            "changedSnippet": snippet,
            "message": message,
            "fileUpdates": file_updates
        })

    except Exception as e:
        logger.error(f"Edit Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500