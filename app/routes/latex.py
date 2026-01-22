# from flask import Blueprint, request, jsonify
# import os, re, logging
# from google import genai

# logger = logging.getLogger(__name__)
# latex_bp = Blueprint("latex", __name__)
# # app = Flask(__name__)

# # Initialize API Key
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# if not GEMINI_API_KEY:
#     logger.error("GEMINI_API_KEY is missing in environment variables.")

# # Note: In the new SDK, we typically instantiate the client where needed 
# # or create a global client instance if thread-safety permits. 
# # Initializing it here for reuse.
# client = genai.Client(api_key=GEMINI_API_KEY)

# @latex_bp.route('/generate-latex', methods=['POST'])
# def generate_latex():
#     try:
#         data = request.get_json()
        
#         if not data:
#             return jsonify({"success": False, "error": "No JSON body provided"}), 400

#         user_idea = data.get('userIdea')
#         title = data.get('title')
#         template_type = data.get('templateType', 'article')
#         author_details = data.get('authorDetails', {})

#         # Validation
#         if not user_idea or not title:
#             return jsonify({
#                 "success": False, 
#                 "error": "Missing required fields: userIdea and title are required"
#             }), 400

#         # Construct Author String safely
#         author_name = author_details.get('name', 'Author')
#         author_email = f"- Email: {author_details['email']}" if author_details.get('email') else ""
#         author_affiliation = f"- Affiliation: {author_details['affiliation']}" if author_details.get('affiliation') else ""

#         # Construct Prompt
#         prompt = f"""You are a LaTeX document generator. Your task is to create a complete, valid LaTeX document.

# CRITICAL INSTRUCTIONS:
# 1. Output ONLY raw LaTeX code - no explanations, no markdown formatting, no code blocks
# 2. Do NOT wrap your response in ```latex or ``` or any other markdown syntax
# 3. Start directly with \\documentclass and end with \\end{{document}}
# 4. The output must be immediately compilable LaTeX code
# 5. Do NOT include any text before \\documentclass or after \\end{{document}}
# 6. Do NOT add any commentary, explanations, or notes outside the LaTeX code
# 7. If the user idea is vague, make reasonable assumptions to create a coherent document
# 8. Ensure proper LaTeX syntax and structure throughout the document

# [VERY IMPORTANT]if Template Type is Blank Document, ONLY,:-
# 1. Use this exact syntax to add sections: \\section{{Section Title}}
# 2. Use this exact syntax to add subsections: \\subsection{{Subsection Title}}

# Here are the details for the document you need to generate:

# Document Requirements:
# - Title: {title}
# - Template Type: {template_type}
# - Author: {author_name}
# {author_email}
# {author_affiliation}

# Content Brief:
# {user_idea}

# Generate a professional {template_type} document with:
# - Appropriate document class (article, report, book, etc.)
# - Essential packages (geometry, inputenc, graphicx, hyperref, amsmath, etc.)
# - Proper structure (title, author, abstract if applicable, sections, subsections as needed)
# - Well-formatted content based on the user's idea
# - Professional typography and layout
# - Bibliography section if references are mentioned

# IMPORTANT: Your ENTIRE response must be valid LaTeX code. Start with \\documentclass and end with \\end{{document}}. Nothing else."""

#         # Generate Content using the new SDK
#         response = client.models.generate_content(
#             model='gemini-2.5-flash',
#             contents=prompt
#         )

#         latex_content = response.text.strip()

#         # Robust trimming logic
#         # Removes ```latex, ```tex, or ``` at the start, and ``` at the end
#         latex_content = re.sub(r'^```(latex|tex)?\s*', '', latex_content, flags=re.IGNORECASE)
#         latex_content = re.sub(r'\s*```$', '', latex_content)
        
#         # Remove any remaining backticks at start/end
#         latex_content = latex_content.strip('`').strip()

#         # Validate that we have LaTeX content
#         if "\\documentclass" not in latex_content or "\\end{document}" not in latex_content:
#             raise ValueError("Generated content does not appear to be valid LaTeX.")

#         return jsonify({
#             "success": True,
#             "latexContent": latex_content
#         })

#     except Exception as e:
#         logger.error(f"AI generation error: {str(e)}")
#         return jsonify({
#             "success": False,
#             "error": str(e) or "Failed to generate LaTeX content"
#         }), 500
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
            
            prompt = f"""You are an academic content generator.
Task: Generate content for a "{template_type}" paper titled "{title}".
Idea: "{user_idea}"

CRITICAL: Output ONLY valid JSON. No markdown.
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
            raw_json = clean_json_response(response.text)
            
            try:
                content_data = json.loads(raw_json)
            except json.JSONDecodeError:
                return jsonify({"success": False, "error": "AI generated invalid JSON"}), 500

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
                elif template_type in ['acm_manuscript', 'acs', 'frontiers', 'asme', 'ios_book_article', 'spie_journal', 'science', 'asm_journal']:
                    final_latex = renderer_func(title, authors_list, content_data.get('abstract',''), content_data.get('keywords',''), content_data.get('sections',{}))
                else:
                    # Default signature (Springer, IEEE, MDPI, etc.)
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

        if not user_prompt or not current_latex:
            return jsonify({"success": False, "error": "Missing inputs"}), 400

        # System Prompt (Requesting JSON)
        system_prompt = """You are an expert LaTeX Editor.
        Task: Modify the LaTeX document based on the user's request.

        CRITICAL OUTPUT FORMAT:
        Return a VALID JSON object with:
        1. "full_latex": The full, compilable document.
        2. "changed_snippet": A short excerpt of just the modified part.

        RULES:
        - Output raw JSON only. No markdown.
        - Escape backslashes (e.g. \\documentclass).
        """

        full_prompt = f"""{system_prompt}\n\nUSER: "{user_prompt}"\n\nDOCUMENT:\n{current_latex}"""

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=full_prompt
        )

        # Parse JSON
        cleaned_text = clean_json_response(response.text)
        try:
            result_json = json.loads(cleaned_text)
            full_doc = result_json.get('full_latex', '')
            snippet = result_json.get('changed_snippet', '')
        except json.JSONDecodeError:
            logger.error("JSON Decode failed, falling back to raw text")
            # Fallback: Assume the whole text is the latex if JSON fails
            full_doc = cleaned_text
            snippet = ""

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
            else:
                snippet = "Modifications applied throughout the document."

        if "\\begin{document}" not in full_doc:
             return jsonify({"success": False, "error": "AI malformed the structure."}), 500

        return jsonify({
            "success": True,
            "latexContent": full_doc,
            "changedSnippet": snippet,
            "message": "Success"
        })

    except Exception as e:
        logger.error(f"Edit Error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500