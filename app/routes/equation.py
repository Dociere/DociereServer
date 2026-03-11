from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import os, re, logging
from google import genai

import requests

logger = logging.getLogger(__name__)
equation_router = APIRouter()

async def call_llm(prompt, ai_config):
    """Dispatcher for Gemini and Ollama"""
    logger.info(f"🚀 call_llm (equation) invoked with provider: {ai_config.get('provider') if ai_config else 'None'}")
    
    if not ai_config:
        logger.warning("⚠️ No ai_config provided for equation, falling back to default Gemini")
        # Fallback to default Gemini if no config provided
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing for default Gemini fallback.")
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return response.text

    provider = ai_config.get("provider", "gemini")
    model = ai_config.get("model", "gemini-2.5-flash")

    if provider == "gemini":
        api_key = ai_config.get("apiKey") or os.getenv("GEMINI_API_KEY")
        logger.info(f"💎 Using Gemini (equation) with model: {model}")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing for Gemini provider.")
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        return response.text
    elif provider == "ollama":
        url = ai_config.get("url", "http://localhost:11434/api/generate")
        logger.info(f"🦙 Using Ollama (equation) at {url} with model: {model}")
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info("✅ Ollama (equation) response received")
        return response.json().get("response", "")
    else:
        logger.error(f"❌ Unknown AI provider (equation): {provider}")
        raise ValueError(f"Unknown AI provider: {provider}")

@equation_router.post('/generate-equation')
async def generate_equation(request: Request):
    try:
        data = await request.json()
        
        if not data:
            return JSONResponse(
                content={"success": False, "error": "No JSON body provided"},
                status_code=400,
            )

        user_prompt = data.get('prompt')
        ai_config = data.get('aiConfig')

        # Validation
        if not user_prompt:
            return JSONResponse(
                content={"success": False, "error": "Missing required field: prompt is required"},
                status_code=400,
            )

        # Construct System Prompt - Explicitly asking for detailed results
        prompt = f"""You are a LaTeX math equation generator. Your task is to convert natural language descriptions into raw, high-quality LaTeX math code.
        
        CRITICAL INSTRUCTIONS:
        1. Output ONLY the raw LaTeX code for the equation.
        2. Do NOT wrap your response in ```latex, ```tex, or ``` markdown blocks.
        3. Do NOT include delimiters like $$, \\[, \\begin{{equation}}, or \\end{{equation}} unless the specific equation structure (like 'align') strictly requires it. Provide only the inner math content.
        4. Do NOT add any explanations, commentary, or text before or after the code.
        5. Use standard, professional LaTeX formatting (e.g., \\frac for fractions, \\cdot for multiplication if needed, \\mathbf for vectors).
        6. If the user asks for a specific known equation (e.g., "Quadratic Formula"), provide the standard canonical form.
        7. Provide a COMPREHENSIVE and DETAILED LaTeX representation. If the equation has multiple parts or steps, include them if appropriate for the request.

        User Request: "{user_prompt}"

        Example Input: "2x2 matrix determinant general equation"
        Example Output: \\det(A) = \\begin{{vmatrix}} a & b \\\\ c & d \\end{{vmatrix}} = ad - bc

        Example Input: "quadratic formula"
        Example Output: x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}

        Your Output:"""

        # Generate Content via Dispatcher
        raw_response = await call_llm(prompt, ai_config)
        latex_equation = raw_response.strip()

        # Robust trimming logic
        latex_equation = re.sub(r'^```(latex|tex)?\s*', '', latex_equation, flags=re.IGNORECASE)
        latex_equation = re.sub(r'\s*```$', '', latex_equation)
        
        # Remove any remaining backticks at start/end
        latex_equation = latex_equation.strip('`').strip()

        # Basic validation
        if not latex_equation or "sorry" in latex_equation.lower():
             raise ValueError("Generated content does not appear to be a valid equation.")

        return {
            "success": True,
            "latexEquation": latex_equation
        }

    except Exception as e:
        logger.error(f"Equation generation error: {str(e)}")
        return JSONResponse(
            content={"success": False, "error": str(e) or "Failed to generate equation"},
            status_code=500,
        )