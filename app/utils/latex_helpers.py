import re

def build_prompt(title, template_type, user_idea, author_details):
    author_name = author_details.get('name', 'Author')
    author_email = f"- Email: {author_details.get('email','')}" if author_details.get('email') else ""
    author_affiliation = f"- Affiliation: {author_details.get('affiliation','')}" if author_details.get('affiliation') else ""

    prompt = f"""You are a LaTeX document generator. Your task is to create a complete, valid LaTeX document.

CRITICAL INSTRUCTIONS:
1. Output ONLY raw LaTeX code
2. Start directly with \\documentclass and end with \\end{{document}}

Document Requirements:
- Title: {title}
- Template Type: {template_type}
- Author: {author_name}
{author_email}
{author_affiliation}

Content Brief:
{user_idea}"""

    return prompt

def clean_latex(text):
    # Remove ```latex, ```tex, ``` at start and ``` at end
    latex_content = re.sub(r'^```(latex|tex)?\s*', '', text, flags=re.IGNORECASE)
    latex_content = re.sub(r'\s*```$', '', latex_content)
    return latex_content.strip('`').strip()
