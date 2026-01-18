from flask import Blueprint, request, jsonify
import os, re, logging
from google import genai

logger = logging.getLogger(__name__)
equation_bp = Blueprint("equation", __name__)

# Initialize API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY is missing in environment variables.")

# Initialize Client
client = genai.Client(api_key=GEMINI_API_KEY)

@equation_bp.route('/generate-equation', methods=['POST'])
def generate_equation():
    if GEMINI_API_KEY:
        print(f"🔑 Using API Key: {GEMINI_API_KEY[:4]}...{GEMINI_API_KEY[-4:]}")
    else:
        print("❌ GEMINI_API_KEY is None or Empty inside route!")
        return jsonify({"success": False, "error": "Server misconfiguration: No API Key"}), 500
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No JSON body provided"}), 400

        user_prompt = data.get('prompt')

        # Validation
        if not user_prompt:
            return jsonify({
                "success": False, 
                "error": "Missing required field: prompt is required"
            }), 400

        # Construct System Prompt
        prompt = f"""You are a LaTeX math equation generator. Your task is to convert natural language descriptions into raw, high-quality LaTeX math code.

CRITICAL INSTRUCTIONS:
1. Output ONLY the raw LaTeX code for the equation.
2. Do NOT wrap your response in ```latex, ```tex, or ``` markdown blocks.
3. Do NOT include delimiters like $$, \\[, \\begin{{equation}}, or \\end{{equation}} unless the specific equation structure (like 'align') strictly requires it. Provide only the inner math content.
4. Do NOT add any explanations, commentary, or text before or after the code.
5. Use standard, professional LaTeX formatting (e.g., \\frac for fractions, \\cdot for multiplication if needed, \\mathbf for vectors).
6. If the user asks for a specific known equation (e.g., "Quadratic Formula"), provide the standard canonical form.

User Request: "{user_prompt}"

Example Input: "2x2 matrix determinant general equation"
Example Output: \\det(A) = \\begin{{vmatrix}} a & b \\\\ c & d \\end{{vmatrix}} = ad - bc

Example Input: "quadratic formula"
Example Output: x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}

Your Output:"""

        # Generate Content
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        latex_equation = response.text.strip()

        # Robust trimming logic (same as your document generator)
        # Removes ```latex, ```tex, or ``` at the start, and ``` at the end
        latex_equation = re.sub(r'^```(latex|tex)?\s*', '', latex_equation, flags=re.IGNORECASE)
        latex_equation = re.sub(r'\s*```$', '', latex_equation)
        
        # Remove any remaining backticks at start/end
        latex_equation = latex_equation.strip('`').strip()

        # Basic validation to ensure it's not empty or an error message
        if not latex_equation or "sorry" in latex_equation.lower():
             # Fallback if the model refused or returned empty
             raise ValueError("Generated content does not appear to be a valid equation.")

        return jsonify({
            "success": True,
            "latexEquation": latex_equation
        })

    except Exception as e:
        logger.error(f"Equation generation error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e) or "Failed to generate equation"
        }), 500