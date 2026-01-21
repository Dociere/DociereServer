def generate_ai4x_latex(title, authors, abstract, sections, conference_info):
    # 1. PRE-PROCESS AUTHORS & AFFILIATIONS
    # We need to map unique organization strings to short IDs (aff1, aff2, etc.)
    aff_map = {}
    aff_counter = 1
    
    # Generate unique IDs for every organization
    for author in authors:
        org = author['organization']
        if org not in aff_map:
            aff_map[org] = f"aff{aff_counter}"
            aff_counter += 1

    # Build the \icmlauthor list
    author_list_latex = "\\begin{icmlauthorlist}\n"
    for author in authors:
        # Get the ID for this author's organization
        aff_id = aff_map[author['organization']]
        
        # Check optional fields
        orcid = author.get('orcid', '')
        # If 'is_presenting' is True, add 'presenting' tag
        presenting_tag = "presenting" if author.get('is_presenting') else ""
        
        author_list_latex += f"\\icmlauthor{{{author['name']}}}{{{aff_id}}}{{{orcid}}}{{{presenting_tag}}}\n"
    author_list_latex += "\\end{icmlauthorlist}\n"

    # Build the \icmlaffiliation list
    affiliation_latex = ""
    for org, aff_id in aff_map.items():
        # Assuming format "University, City, Country"
        affiliation_latex += f"\\icmlaffiliation{{{aff_id}}}{{{org}}}\n"

    # Build corresponding authors
    corr_author_latex = ""
    for author in authors:
        if author.get('is_corresponding'):
             corr_author_latex += f"\\icmlcorrespondingauthor{{{author['name']}}}{{{author['email']}}}\n"

    # 2. START LATEX GENERATION
    latex = r"""
\documentclass{ai4x}
\usepackage{tabulary}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{booktabs}
"""
    # Inject Conference Info
    latex += f"\\IACconference{{{conference_info.get('conference_name', 'AI4X -- Accelerate')}}}\n"
    latex += f"\\IACpaperyear{{{conference_info.get('year', '2026')}}}\n"
    latex += f"\\IAClocation{{{conference_info.get('location', 'Singapore')}}}\n"
    latex += f"\\IACdate{{{conference_info.get('dates', '16--19 June 2026')}}}\n"

    latex += f"\\title{{{title}}}\n"

    latex += r"""
\hypersetup{
    pdfkeywords={AI, machine learning, science, conference template}
}

\begin{document}
\twocolumn[
\maketitle
\icmlsetsymbol{equal}{*}
"""
    # Inject Pre-processed Author Blocks
    latex += author_list_latex
    latex += "\n"
    latex += affiliation_latex
    latex += "\n"
    latex += corr_author_latex

    latex += r"""
\printAffiliations
\vskip 2.5ex
]
\thispagestyle{fancy}
"""
    
    # 3. SECTIONS LOOP
    # Handle Abstract separately as it is not always a standard \section in all templates, 
    # but in AI4X it usually flows as the first section or is integrated. 
    # Based on your template, Abstract isn't explicitly wrapped in \begin{abstract}, 
    # so we can treat it as the first section or part of Introduction if strictly following the provided snippet.
    # However, standard practice suggests:
    
    # Loop through the dynamic sections dictionary
    for section_name, content in sections.items():
        # Acknowledgments usually uses \section* (no number)
        if section_name.lower() == 'acknowledgments':
             latex += f"\\section*{{{section_name}}}\n{content}\n\n"
        # Appendices environment
        elif section_name.lower() == 'appendices':
             latex += f"\\begin{{appendices}}\n{content}\n\\end{{appendices}}\n\n"
        else:
             latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # Bibliography support
    latex += "\\bibliography{biblio}\n"
    latex += "\\end{document}\n"

    return latex
def generate_springer_latex(title, authors, abstract, keywords, sections):
    # 1. PRE-PROCESS AFFILIATIONS
    # Springer requires mapping organizations to IDs (1, 2, 3...)
    org_map = {}
    org_counter = 1
    
    # Identify unique organizations and assign IDs
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1

    # 2. START LATEX GENERATION
    latex = r"""
\documentclass[pdflatex,sn-mathphys-num]{sn-jnl}
\usepackage{graphicx}
\usepackage{multirow}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{amsthm}
\usepackage{mathrsfs}
\usepackage[title]{appendix}
\usepackage{xcolor}
\usepackage{textcomp}
\usepackage{manyfoot}
\usepackage{booktabs}
\usepackage{algorithm}
\usepackage{algorithmicx}
\usepackage{algpseudocode}
\usepackage{listings}

\theoremstyle{thmstyleone}
\newtheorem{theorem}{Theorem}
\newtheorem{proposition}[theorem]{Proposition}
\theoremstyle{thmstyletwo}
\newtheorem{example}{Example}
\newtheorem{remark}{Remark}
\theoremstyle{thmstylethree}
\newtheorem{definition}{Definition}
\raggedbottom

\begin{document}
"""
    # Title
    latex += f"\\title[{title[:50]}...]{{{title}}}\n"

    # 3. GENERATE AUTHORS
    # Springer syntax: \author*[1]{\fnm{First} \sur{Last}}\email{...}
    for author in authors:
        # Get Affiliation ID
        aff_id = org_map[author['organization']]
        
        # Handle Corresponding Author (*)
        star = "*" if author.get('is_corresponding', False) else ""
        
        # Split name into First (fnm) and Surname (sur)
        # Assuming format "Firstname Lastname"
        name_parts = author['name'].strip().rsplit(' ', 1)
        if len(name_parts) > 1:
            fnm, sur = name_parts[0], name_parts[1]
        else:
            fnm, sur = "", name_parts[0]

        latex += f"\\author{star}[{aff_id}]{{\\fnm{{{fnm}}} \\sur{{{sur}}}}}\n"
        if author.get('email'):
            latex += f"\\email{{{author['email']}}}\n"
        
        # Handle Equal Contribution
        if author.get('equal_contribution'):
             latex += "\\equalcont{These authors contributed equally to this work.}\n"

    # 4. GENERATE AFFILIATIONS
    # Springer syntax: \affil*[1]{\orgname{Organization}, \orgaddress{...}}
    for org, aff_id in org_map.items():
        # Note: We treat the whole org string as \orgname for simplicity
        latex += f"\\affil[{aff_id}]{{\\orgname{{{org}}}}}\n"

    # 5. ABSTRACT & KEYWORDS
    latex += f"\\abstract{{{abstract}}}\n"
    latex += f"\\keywords{{{keywords}}}\n"
    latex += "\\maketitle\n\n"

    # 6. SECTIONS LOOP
    for section_name, content in sections.items():
        # Handle specific Springer Backmatter sections
        if section_name.lower() in ['acknowledgments', 'acknowledgements']:
            latex += f"\\bmhead{{{section_name}}}\n{content}\n\n"
        elif section_name.lower() == 'supplementary information':
            latex += f"\\backmatter\n\\bmhead{{{section_name}}}\n{content}\n\n"
        elif section_name.lower() == 'appendices':
             latex += f"\\begin{{appendices}}\n{content}\n\\end{{appendices}}\n\n"
        elif section_name.lower() == 'declarations':
             # Declarations usually require specific list formatting, but here we render content provided
             latex += f"\\section*{{{section_name}}}\n{content}\n\n"
        else:
             latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # Bibliography
    latex += "\\bibliography{sn-bibliography}\n"
    latex += "\\end{document}\n"

    return latex
def generate_transmag_latex(title, authors, abstract, keywords, sections):
    # 1. PRE-PROCESS AFFILIATIONS
    # Map unique organizations to ID numbers for the \IEEEauthorrefmark system
    org_map = {}
    org_counter = 1
    
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1

    # 2. CONSTRUCT AUTHOR STRINGS
    # This template lists all names in one block, then all affiliations in subsequent blocks
    name_list = []
    for author in authors:
        aff_id = org_map[author['organization']]
        # Format: Name\IEEEauthorrefmark{1}
        name_entry = f"{author['name']}\\IEEEauthorrefmark{{{aff_id}}}"
        
        # Add membership if present (e.g., Fellow, IEEE)
        if author.get('membership'):
             name_entry += f",~\\IEEEmembership{{{author['membership']}}}"
        
        name_list.append(name_entry)
    
    # Join names with commas
    names_latex = ",\n".join(name_list)

    # Construct Affiliation Blocks
    affil_latex = ""
    for org, aff_id in org_map.items():
        affil_latex += f"\\IEEEauthorblockA{{\\IEEEauthorrefmark{{{aff_id}}}{org}}}\n"

    # Construct Thanks block (usually for corresponding author info)
    thanks_text = ""
    for author in authors:
        if author.get('is_corresponding'):
            thanks_text = f"\\thanks{{Corresponding author: {author['name']} (email: {author['email']}).}}"
            break

    # 3. START LATEX GENERATION
    latex = r"""
\documentclass[journal,transmag]{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{xcolor}
\hyphenation{op-tical net-works semi-conduc-tor}

\begin{document}
"""
    latex += f"\\title{{{title}}}\n"

    # 4. INJECT AUTHORS
    # The transmag format puts everything inside one \author{} command
    latex += "\\author{\\IEEEauthorblockN{\n"
    latex += names_latex
    latex += "\n}\n"
    latex += affil_latex
    latex += thanks_text
    latex += "}\n"

    # 5. INJECT ABSTRACT & KEYWORDS (Must be before maketitle)
    latex += "\\IEEEtitleabstractindextext{%\n"
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n"
    latex += f"\\begin{{IEEEkeywords}}\n{keywords}\n\\end{{IEEEkeywords}}}}\n"

    # 6. MAKE TITLE & HEADERS
    latex += "\\maketitle\n"
    latex += "\\IEEEdisplaynontitleabstractindextext\n"
    latex += "\\IEEEpeerreviewmaketitle\n\n"

    # 7. SECTIONS LOOP
    for section_name, content in sections.items():
        if section_name.lower() == 'acknowledgment':
            # Acknowledgments use \section*
            latex += f"\\section*{{{section_name}}}\n{content}\n\n"
        elif section_name.lower() == 'appendices':
            # Start appendices environment
            latex += f"\\appendices\n{content}\n\n"
        elif section_name.lower() == 'biographies':
            # Biographies are handled via specific environment, usually at the end
            # We assume 'content' here is a list of bio dictionaries or pre-formatted text
            # For this renderer, we will generate them dynamically from the author list if content is empty,
            # or paste content if it is raw latex.
            pass # We will handle bios explicitly below
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. GENERATE BIOGRAPHIES
    # If the user data includes bio text for authors
    for author in authors:
        bio_text = author.get('bio_text', 'Biography text here.')
        name = author['name']
        # Use 'IEEEbiography' if photo exists (assumed handled externally) or 'IEEEbiographynophoto'
        latex += f"\\begin{{IEEEbiographynophoto}}{{{name}}}\n{bio_text}\n\\end{{IEEEbiographynophoto}}\n\n"

    # Bibliography
    latex += "\\bibliographystyle{IEEEtran}\n"
    latex += "\\bibliography{references}\n"
    
    latex += "\\end{document}\n"

    return latex
def generate_tmi_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. PREPARE HEADER & PACKAGES
    latex = r"""
\documentclass[journal,twoside,web]{ieeecolor}
\usepackage{tmi}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em
    T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}
"""
    
    # 2. RUNNING HEADERS (Markboth)
    # Extract first author surname for "Author et al."
    if authors:
        first_author_surname = authors[0]['name'].split()[-1]
    else:
        first_author_surname = "Author"
        
    vol = journal_meta.get('volume', 'XX')
    no = journal_meta.get('number', 'XX')
    year = journal_meta.get('year', '2026')
    
    latex += f"\\markboth{{\\journalname, VOL. {vol}, NO. {no}, {year}}}\n"
    latex += f"{{{first_author_surname} \\MakeLowercase{{\\textit{{et al.}}}}: {title}}}\n"

    latex += "\\begin{document}\n"
    latex += f"\\title{{{title}}}\n"

    # 3. GENERATE AUTHORS & THANKS
    # TMI puts all authors in one \author command.
    # Affiliations are added as \thanks{} footnotes.
    
    author_strings = []
    thanks_strings = []

    # A. Create the First Footnote (Submission Date / Grants)
    # This is usually required by IEEE TMI as the first \thanks
    submission_date = journal_meta.get('submission_date', 'Month XX, 2026')
    grants = journal_meta.get('grants', 'No grants specified.')
    thanks_strings.append(f"\\thanks{{This work was submitted for review on {submission_date}. This work was supported by {grants}}}")

    # B. Process Authors and their specific affiliations
    for index, author in enumerate(authors):
        # Name + Membership
        name_str = author['name']
        if author.get('membership'):
            name_str += f", \\IEEEmembership{{{author['membership']}}}"
        author_strings.append(name_str)

        # Affiliation \thanks
        # "F. A. Author is with the [Organization] (e-mail: ...)."
        affil_text = f"\\thanks{{{author['name']} is with {author['organization']} (e-mail: {author['email']}).}}"
        thanks_strings.append(affil_text)

    # Join authors with commas and "and"
    if len(author_strings) > 1:
        authors_latex = ", ".join(author_strings[:-1]) + ", and " + author_strings[-1]
    else:
        authors_latex = author_strings[0]

    # Combine into the \author command
    # Note: thanks_strings are appended immediately after the names inside \author
    latex += f"\\author{{{authors_latex}\n"
    latex += "\n".join(thanks_strings)
    latex += "}\n\n"

    latex += "\\maketitle\n\n"

    # 4. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"
    latex += f"\\begin{{IEEEkeywords}}\n{keywords}\n\\end{{IEEEkeywords}}\n\n"

    # 5. SECTIONS LOOP
    for section_name, content in sections.items():
        # Handle Introduction specifically to add \IEEEPARstart
        if section_name.lower() == 'introduction':
            # We need to wrap the first letter of the content in \IEEEPARstart
            # Simple heuristic: split first word
            words = content.split(' ', 1)
            if len(words) > 0 and len(words[0]) > 1:
                first_letter = words[0][0]
                rest_of_word = words[0][1:]
                rest_of_text = " " + words[1] if len(words) > 1 else ""
                content = f"\\IEEEPARstart{{{first_letter}}}{{{rest_of_word}}}{rest_of_text}"
            
            latex += f"\\section{{{section_name}}}\n\\label{{sec:introduction}}\n{content}\n\n"
        
        elif section_name.lower() == 'appendix':
            latex += f"\\appendices\n\\section*{{Appendix}}\n{content}\n\n"
            
        elif section_name.lower() in ['acknowledgment', 'acknowledgments']:
            latex += f"\\section*{{Acknowledgment}}\n{content}\n\n"
            
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. REFERENCES
    latex += "\\bibliographystyle{IEEEtran}\n"
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_ieee_journal_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. SETUP HEADERS & PACKAGES
    latex = r"""
\documentclass[lettersize,journal]{IEEEtran}
\usepackage{amsmath,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{array}
\usepackage[caption=false,font=normalsize,labelfont=sf,textfont=sf]{subfig}
\usepackage{textcomp}
\usepackage{stfloats}
\usepackage{url}
\usepackage{verbatim}
\usepackage{graphicx}
\usepackage{cite}
\hyphenation{op-tical net-works semi-conduc-tor IEEE-Xplore}

\begin{document}
"""
    
    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # IEEE Journals typically list authors in a continuous block, with \thanks{} for affiliations
    author_list = []
    thanks_list = []
    
    for author in authors:
        # Construct Name + Membership
        name_str = author['name']
        if author.get('membership'):
            name_str += f",~\\IEEEmembership{{{author['membership']}}}"
        author_list.append(name_str)
        
        # Construct Affiliation Note
        # "M. Shell is with the Department of..., (e-mail: ...)"
        initials = "".join([n[0] for n in author['name'].split()])
        thanks_str = f"\\thanks{{{author['name']} is with {author['organization']} (e-mail: {author['email']}).}}"
        thanks_list.append(thanks_str)

    # Join authors with commas
    latex += "\\author{" + ", ".join(author_list) + "\n"
    # Append the thanks footnotes
    latex += "\n".join(thanks_list)
    latex += "}\n"

    # 4. RUNNING HEADERS (Markboth)
    vol = journal_meta.get('volume', '14')
    no = journal_meta.get('number', '8')
    date = journal_meta.get('date', 'August 2021')
    journal_name = journal_meta.get('journal_name', 'Journal of LaTeX Class Files')
    
    # First author surname for header
    first_author_surname = authors[0]['name'].split()[-1] if authors else "Author"

    latex += f"\\markboth{{{journal_name},~Vol.~{vol}, No.~{no}, {date}}}%\n"
    latex += f"{{{first_author_surname} \\MakeLowercase{{\\textit{{et al.}}}}: {title}}}\n"

    # 5. PUB ID
    # Must be placed before maketitle
    latex += "\\IEEEpubid{0000--0000/00\\$00.00~\\copyright~2021 IEEE}\n"
    
    latex += "\\maketitle\n"

    # 6. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"
    latex += f"\\begin{{IEEEkeywords}}\n{keywords}\n\\end{{IEEEkeywords}}\n\n"

    # 7. SECTIONS LOOP
    for section_name, content in sections.items():
        
        # Handle Introduction specifically for Drop Cap
        if section_name.lower() == 'introduction':
            # Logic to split the first word for \IEEEPARstart{F}{irst}
            words = content.split(' ', 1)
            if len(words) > 0 and len(words[0]) > 1:
                first_char = words[0][0]
                rest_word = words[0][1:]
                rest_text = " " + words[1] if len(words) > 1 else ""
                formatted_content = f"\\IEEEPARstart{{{first_char}}}{{{rest_word}}}{rest_text}"
            else:
                formatted_content = content
            
            # Add \IEEEpubidadjcol to clear the pubid in the second column
            formatted_content += "\n\\IEEEpubidadjcol\n"
            
            latex += f"\\section{{{section_name}}}\n{formatted_content}\n\n"
        
        elif section_name.lower() == 'appendices':
            latex += f"\\appendices\n{content}\n\n"
            
        elif section_name.lower() in ['acknowledgments', 'acknowledgment']:
            latex += f"\\section*{{Acknowledgments}}\n{content}\n\n"
            
        elif section_name.lower() == 'biographies':
            # Skip here, handled specifically at the end
            pass
            
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. REFERENCES
    latex += "\\bibliographystyle{IEEEtran}\n"
    latex += "\\bibliography{references}\n"

    # 9. BIOGRAPHIES
    # These usually come after references
    if 'Biographies' in sections:
        # If raw content was passed in sections
        latex += sections['Biographies']
    else:
        # Generate from author data if not explicitly provided in sections
        latex += "\\newpage\n\n"
        for author in authors:
            bio = author.get('bio_text', 'Biography text here.')
            name = author['name']
            # Check if photo exists (placeholder logic)
            if author.get('photo_path'):
                latex += f"\\begin{{IEEEbiography}}[{author['photo_path']}]{{{name}}}\n{bio}\n\\end{{IEEEbiography}}\n\n"
            else:
                latex += f"\\begin{{IEEEbiographynophoto}}{{{name}}}\n{bio}\n\\end{{IEEEbiographynophoto}}\n\n"

    latex += "\\vfill\n"
    latex += "\\end{document}\n"

    return latex
def generate_ieee_journal_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. SETUP HEADERS & PACKAGES
    latex = r"""
\documentclass[lettersize,journal]{IEEEtran}
\usepackage{amsmath,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{array}
\usepackage[caption=false,font=normalsize,labelfont=sf,textfont=sf]{subfig}
\usepackage{textcomp}
\usepackage{stfloats}
\usepackage{url}
\usepackage{verbatim}
\usepackage{graphicx}
\usepackage{cite}
\hyphenation{op-tical net-works semi-conduc-tor IEEE-Xplore}

\begin{document}
"""
    
    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # IEEE Journals typically list authors in a continuous block, with \thanks{} for affiliations
    author_list = []
    thanks_list = []
    
    for author in authors:
        # Construct Name + Membership
        name_str = author['name']
        if author.get('membership'):
            name_str += f",~\\IEEEmembership{{{author['membership']}}}"
        author_list.append(name_str)
        
        # Construct Affiliation Note
        # "M. Shell is with the Department of..., (e-mail: ...)"
        initials = "".join([n[0] for n in author['name'].split()])
        thanks_str = f"\\thanks{{{author['name']} is with {author['organization']} (e-mail: {author['email']}).}}"
        thanks_list.append(thanks_str)

    # Join authors with commas
    latex += "\\author{" + ", ".join(author_list) + "\n"
    # Append the thanks footnotes
    latex += "\n".join(thanks_list)
    latex += "}\n"

    # 4. RUNNING HEADERS (Markboth)
    vol = journal_meta.get('volume', '14')
    no = journal_meta.get('number', '8')
    date = journal_meta.get('date', 'August 2021')
    journal_name = journal_meta.get('journal_name', 'Journal of LaTeX Class Files')
    
    # First author surname for header
    first_author_surname = authors[0]['name'].split()[-1] if authors else "Author"

    latex += f"\\markboth{{{journal_name},~Vol.~{vol}, No.~{no}, {date}}}%\n"
    latex += f"{{{first_author_surname} \\MakeLowercase{{\\textit{{et al.}}}}: {title}}}\n"

    # 5. PUB ID
    # Must be placed before maketitle
    latex += "\\IEEEpubid{0000--0000/00\\$00.00~\\copyright~2021 IEEE}\n"
    
    latex += "\\maketitle\n"

    # 6. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"
    latex += f"\\begin{{IEEEkeywords}}\n{keywords}\n\\end{{IEEEkeywords}}\n\n"

    # 7. SECTIONS LOOP
    for section_name, content in sections.items():
        
        # Handle Introduction specifically for Drop Cap
        if section_name.lower() == 'introduction':
            # Logic to split the first word for \IEEEPARstart{F}{irst}
            words = content.split(' ', 1)
            if len(words) > 0 and len(words[0]) > 1:
                first_char = words[0][0]
                rest_word = words[0][1:]
                rest_text = " " + words[1] if len(words) > 1 else ""
                formatted_content = f"\\IEEEPARstart{{{first_char}}}{{{rest_word}}}{rest_text}"
            else:
                formatted_content = content
            
            # Add \IEEEpubidadjcol to clear the pubid in the second column
            formatted_content += "\n\\IEEEpubidadjcol\n"
            
            latex += f"\\section{{{section_name}}}\n{formatted_content}\n\n"
        
        elif section_name.lower() == 'appendices':
            latex += f"\\appendices\n{content}\n\n"
            
        elif section_name.lower() in ['acknowledgments', 'acknowledgment']:
            latex += f"\\section*{{Acknowledgments}}\n{content}\n\n"
            
        elif section_name.lower() == 'biographies':
            # Skip here, handled specifically at the end
            pass
            
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. REFERENCES
    latex += "\\bibliographystyle{IEEEtran}\n"
    latex += "\\bibliography{references}\n"

    # 9. BIOGRAPHIES
    # These usually come after references
    if 'Biographies' in sections:
        # If raw content was passed in sections
        latex += sections['Biographies']
    else:
        # Generate from author data if not explicitly provided in sections
        latex += "\\newpage\n\n"
        for author in authors:
            bio = author.get('bio_text', 'Biography text here.')
            name = author['name']
            # Check if photo exists (placeholder logic)
            if author.get('photo_path'):
                latex += f"\\begin{{IEEEbiography}}[{author['photo_path']}]{{{name}}}\n{bio}\n\\end{{IEEEbiography}}\n\n"
            else:
                latex += f"\\begin{{IEEEbiographynophoto}}{{{name}}}\n{bio}\n\\end{{IEEEbiographynophoto}}\n\n"

    latex += "\\vfill\n"
    latex += "\\end{document}\n"

    return latex
def generate_tns_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. SETUP HEADERS & PACKAGES
    latex = r"""
\documentclass{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp,nicefrac}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em
T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}
"""

    # 2. RUNNING HEADERS (Markboth)
    # TNS Format: IEEE TRANSACTIONS ON NUCLEAR SCIENCE, VOL. XX, NO. XX, MONTH YEAR
    vol = journal_meta.get('volume', 'XX')
    no = journal_meta.get('number', 'XX')
    month_year = journal_meta.get('month_year', 'January 2025')
    journal_name = journal_meta.get('journal_name', 'IEEE TRANSACTIONS ON NUCLEAR SCIENCE')
    
    # First author surname for header "Author et al."
    if authors:
        first_author_surname = authors[0]['name'].split()[-1]
    else:
        first_author_surname = "Author"

    latex += f"\\markboth{{{journal_name}, VOL. {vol}, NO. {no}, {month_year}}}\n"
    latex += f"{{{first_author_surname} \\MakeLowercase{{\\textit{{et al.}}}}: {title}}}\n"

    latex += "\\begin{document}\n"
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # TNS puts all authors in one block.
    # The first \thanks contains submission date and support/funding.
    # Subsequent \thanks contain affiliation and email.

    author_names = []
    thanks_entries = []

    # A. First Footnote (Submission Date + Funding)
    sub_date = journal_meta.get('submission_date', 'Month XX, 2025')
    funding = journal_meta.get('funding', 'No funding source specified.')
    thanks_entries.append(f"\\thanks{{This work was submitted for review on {sub_date}. {funding}}}")

    # B. Process Authors
    for author in authors:
        # Name + Membership
        name_str = author['name']
        if author.get('membership'):
            name_str += f", \\IEEEmembership{{{author['membership']}}}"
        author_names.append(name_str)

        # Affiliation \thanks
        # "F. A. Author is with [Organization] (e-mail: ...)."
        affil_text = f"\\thanks{{{author['name']} is with {author['organization']} (e-mail: {author['email']}).}}"
        thanks_entries.append(affil_text)

    # Combine names
    if len(author_names) > 1:
        # Join with commas, and add 'and' before the last one
        names_latex = ", ".join(author_names[:-1]) + ", and " + author_names[-1]
    elif author_names:
        names_latex = author_names[0]
    else:
        names_latex = ""

    # Generate the \author block
    latex += f"\\author{{{names_latex}\n"
    latex += "\n".join(thanks_entries)
    latex += "}\n\n"

    latex += "\\maketitle\n\n"

    # 4. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"
    latex += f"\\begin{{IEEEkeywords}}\n{keywords}\n\\end{{IEEEkeywords}}\n\n"

    # 5. SECTIONS LOOP
    for section_name, content in sections.items():
        # Handle Introduction specifically for Drop Cap (\IEEEPARstart)
        if section_name.lower() == 'introduction':
            # Logic to split the first word for Drop Cap
            words = content.split(' ', 1)
            if len(words) > 0 and len(words[0]) > 0:
                first_letter = words[0][0]
                rest_of_word = words[0][1:]
                rest_of_text = " " + words[1] if len(words) > 1 else ""
                content = f"\\IEEEPARstart{{{first_letter}}}{{{rest_of_word}}}{rest_of_text}"
            
            latex += f"\\section{{{section_name}}}\n\\label{{sec:introduction}}\n{content}\n\n"
        
        elif section_name.lower() in ['appendix', 'appendices']:
            # TNS uses \appendices then \section*{Appendix} (no numbering)
            latex += f"\\appendices\n\\section*{{Appendix}}\n{content}\n\n"
            
        elif section_name.lower() in ['acknowledgment', 'acknowledgments']:
            latex += f"\\section*{{Acknowledgment}}\n{content}\n\n"
            
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. REFERENCES
    latex += "\\bibliographystyle{IEEEtran}\n"
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_ieee_journal_letters_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. PREAMBLE & PACKAGES
    latex = r"""
\documentclass[lettersize,journal]{IEEEtran}
\usepackage{amsmath,amsfonts}
\usepackage{algorithmic}
\usepackage{algorithm}
\usepackage{array}
\usepackage[caption=false,font=normalsize,labelfont=sf,textfont=sf]{subfig}
\usepackage{textcomp}
\usepackage{stfloats}
\usepackage{url}
\usepackage{verbatim}
\usepackage{graphicx}
\usepackage{cite}
\usepackage{bm}
\hyphenation{op-tical net-works semi-conduc-tor IEEE-Xplore}

\begin{document}
"""
    
    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # This template puts all authors in one block and uses \thanks for affiliations/dates.
    
    author_names_formatted = []
    thanks_notes = []

    # A. First Thanks Note (Dates)
    received_date = journal_meta.get('received_date', 'November 4, 2023')
    revised_date = journal_meta.get('revised_date', 'February 28, 2024')
    thanks_notes.append(f"\\thanks{{Manuscript received {received_date}; revised {revised_date}.}}")

    # B. Process Authors
    for author in authors:
        # Build Name + Membership (e.g., "John Doe, \IEEEmembership{Member, IEEE}")
        name_str = author['name']
        if author.get('membership'):
            name_str += f", \\IEEEmembership{{{author['membership']}}}"
        author_names_formatted.append(name_str)

        # Build Affiliation Thanks
        # Note: In real scenarios, you might group authors by affiliation to reduce redundancy.
        # Here we generate a simple thanks string per author or group.
        affil = f"\\thanks{{{author['name']} is with {author['organization']} (e-mail: {author['email']}).}}"
        thanks_notes.append(affil)

    # Join authors with commas and "and" for the last one
    if len(author_names_formatted) > 1:
        authors_string = ", ".join(author_names_formatted[:-1]) + ", and " + author_names_formatted[-1]
    else:
        authors_string = author_names_formatted[0] if author_names_formatted else ""

    latex += f"\\author{{{authors_string}\n"
    latex += "\n".join(thanks_notes)
    latex += "\n}\n"

    # 4. RUNNING HEADERS (Markboth)
    j_name = journal_meta.get('journal_name', 'IEEE Journal of \\LaTeX\\ Class')
    vol = journal_meta.get('volume', '12')
    no = journal_meta.get('issue', '6')
    date = journal_meta.get('date', 'February 2024')
    
    # First author surname for "Et al."
    first_author_surname = authors[0]['name'].split()[-1] if authors else "Author"

    latex += f"\\markboth{{{j_name},~Vol.~{vol}, No.~{no},~{date}}}%\n"
    latex += f"{{{first_author_surname} \\MakeLowercase{{\\textit{{et al.}}}}: {title}}}\n"

    # 5. PUBLICATION ID
    year = journal_meta.get('year', '2024')
    latex += f"\\IEEEpubid{{0000--0000~\\copyright~{year} IEEE}}\n"

    latex += "\\maketitle\n"

    # 6. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"
    latex += f"\\begin{{IEEEkeywords}}\n{keywords}\n\\end{{IEEEkeywords}}\n\n"

    # 7. SECTIONS LOOP
    for section_name, content in sections.items():
        
        # Special Handling for Introduction (Drop Cap)
        if section_name.lower() == 'introduction':
            # Logic to split the first word: "This" -> "T" and "his"
            # Simple heuristic: Split by first space
            words = content.strip().split(' ', 1)
            if words and len(words[0]) > 0:
                first_word = words[0]
                first_char = first_word[0]
                rest_word = first_word[1:]
                rest_sentence = " " + words[1] if len(words) > 1 else ""
                
                content = f"\\IEEEPARstart{{{first_char}}}{{{rest_word}}}{rest_sentence}"
            
            # IEEEpubidadjcol must be called in the second column of the first page
            # usually appearing in the intro or early sections.
            content += "\n\\IEEEpubidadjcol\n"
            
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

        # Special Handling for Appendix
        elif section_name.lower().startswith('appendix'):
            # Detect if single or multiple appendices needed
            # For this template, \appendices is common for multiple, \appendix for single.
            latex += f"\\appendices\n\\section{{{section_name}}}\n{content}\n\n"

        # Special Handling for Acknowledgments
        elif section_name.lower().startswith('acknowledg'):
            latex += f"\\section*{{Acknowledgments}}\n{content}\n\n"

        # Standard Sections
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. BIBLIOGRAPHY
    latex += "\\bibliographystyle{IEEEtran}\n"
    latex += "\\bibliography{references}\n" # Assumes a references.bib file exists

    # 9. END DOCUMENT
    latex += "\\vfill\n"
    latex += "\\end{document}\n"

    return latex
def generate_mdpi_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. SETUP CLASS & PREAMBLE
    # Default to 'journal' if not specified. MDPI has many specific journal names.
    journal_name = journal_meta.get('journal_id', 'journal') 
    latex = f"\\documentclass[{journal_name},article,submit,pdftex,moreauthors]{{Definitions/mdpi}}\n"
    
    latex += r"""
\firstpage{1} 
\makeatletter 
\setcounter{page}{\@firstpage} 
\makeatother
"""
    # Inject Metadata
    pub_vol = journal_meta.get('volume', '1')
    issue_num = journal_meta.get('issue', '1')
    pub_year = journal_meta.get('year', '2026')
    latex += f"\\pubvolume{{{pub_vol}}}\n\\issuenum{{{issue_num}}}\n\\pubyear{{{pub_year}}}\n\\copyrightyear{{{pub_year}}}\n"
    
    # 2. TITLE
    latex += f"\\Title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # Logic: Map unique organizations to IDs (1, 2, 3).
    # Format: \Author{Name $^{1}$, Name $^{2}$}
    # Format: \address{$^{1}$ \quad Org 1}
    
    org_map = {}
    org_counter = 1
    author_latex_list = []
    
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1
        
        aff_id = org_map[org]
        
        # Check for Corresponding Author (*)
        star = "*" if author.get('is_corresponding') else ""
        
        # Build entry: "Firstname Lastname $^{1,*}$"
        # Note: ORCID logic omitted for brevity, but fits here usually as \orcidA{}
        entry = f"{author['name']} $^{{{aff_id}}}{star}$"
        author_latex_list.append(entry)

    # Join authors
    latex += "\\Author{" + ", ".join(author_latex_list) + "}\n"
    
    # Author Names for Metadata
    plain_names = ", ".join([a['name'] for a in authors])
    latex += f"\\AuthorNames{{{plain_names}}}\n"

    # Build Address Block
    address_lines = []
    for org, aff_id in org_map.items():
        address_lines.append(f"$^{{{aff_id}}}$ \\quad {org}")
    
    latex += "\\address{%\n" + "\\\\ \n".join(address_lines) + "}\n"

    # Correspondence info
    # Find corresponding email
    corr_email = next((a['email'] for a in authors if a.get('is_corresponding')), "email@example.com")
    latex += f"\\corres{{Correspondence: {corr_email}}}\n"

    # 4. ABSTRACT & KEYWORDS
    latex += f"\\abstract{{{abstract}}}\n"
    latex += f"\\keyword{{{keywords}}}\n"

    latex += "\\begin{document}\n"

    # 5. SECTIONS LOOP
    # MDPI uses specific commands for backmatter sections instead of \section
    mdpi_special_sections = {
        'author contributions': '\\authorcontributions',
        'funding': '\\funding',
        'institutional review board statement': '\\institutionalreview',
        'informed consent statement': '\\informedconsent',
        'data availability statement': '\\dataavailability',
        'acknowledgments': '\\acknowledgments',
        'conflicts of interest': '\\conflictsofinterest'
    }

    for section_name, content in sections.items():
        key = section_name.lower().strip()
        
        if key in mdpi_special_sections:
            # Use specific MDPI command: \funding{Content...}
            command = mdpi_special_sections[key]
            latex += f"{command}{{{content}}}\n\n"
        
        elif key == 'abbreviations':
            # Abbreviations usually require specific tabular formatting
            # For simplicity, we wrap content in the macro
            latex += f"\\abbreviations{{Abbreviations}}{{\n{content}\n}}\n\n"
            
        elif key == 'appendix':
             latex += f"\\appendixtitles{{yes}}\n\\appendixstart\n\\appendix\n\\section{{}}\n{content}\n\n"
             
        else:
            # Standard Section
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. REFERENCES
    # MDPI usually requires external .bib or specific format. 
    # We will assume standard bibtex here.
    latex += "\\reftitle{References}\n"
    latex += "\\externalbibliography{yes}\n"
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_acm_latex(title, authors, abstract, keywords, sections):
    latex = r"""
\documentclass[manuscript,screen,review]{acmart}
\AtBeginDocument{%
  \providecommand\BibTeX{{%
    Bib\TeX}}}

% Rights and Conference Configuration (Placeholders)
\setcopyright{acmlicensed}
\copyrightyear{2024}
\acmYear{2024}
\acmDOI{XXXXXXX.XXXXXXX}
\acmConference[Conference '24]{ACM Conference}{June 03--05, 2024}{City, Country}
\acmISBN{978-1-4503-XXXX-X/18/06}

\begin{document}

"""
    latex += f"\\title{{{title}}}\n\n"

    # Generate ACM specific Author/Affiliation blocks
    # ACM requires separate commands for email and affiliation details
    for author in authors:
        latex += f"\\author{{{author['name']}}}\n"
        latex += f"\\email{{{author['email']}}}\n"
        # Assuming 'organization' contains the institution name. 
        # Ideally, structured data would provide city/country, but we default here.
        latex += "\\affiliation{%\n"
        latex += f"  \\institution{{{author['organization']}}}\n"
        latex += f"  \\country{{Country}}\n" 
        latex += "}\n\n"

    # Short authors for header
    if len(authors) > 0:
        first_author = authors[0]['name'].split()[-1] # Surname
        latex += f"\\renewcommand{{\\shortauthors}}{{{first_author} et al.}}\n"

    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"

    # CCS Concepts Placeholder (Required for ACM)
    latex += r"""
\begin{CCSXML}
<ccs2012>
 <concept>
  <concept_id>00000000.00000000.00000000</concept_id>
  <concept_desc>Computer systems organization~Architectures</concept_desc>
  <concept_significance>500</concept_significance>
 </concept>
</ccs2012>
\end{CCSXML}

\ccsdesc[500]{Computer systems organization~Architectures}
"""
    
    latex += f"\\keywords{{{keywords}}}\n\n"
    
    latex += "\\maketitle\n\n"

    # Render Sections
    for section_name, content in sections.items():
        # Special handling for Acknowledgments in ACM (uses 'acks' environment)
        if section_name.lower() in ['acknowledgments', 'acknowledgements']:
            latex += f"\\begin{{acks}}\n{content}\n\\end{{acks}}\n\n"
        
        # Special handling for Appendices
        elif section_name.lower() in ['appendix', 'appendices']:
            latex += f"\\appendix\n{content}\n\n"
            
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # Bibliographystyle is typically defined at the end for ACM
    latex += "\\bibliographystyle{ACM-Reference-Format}\n"
    latex += "\\bibliography{references}\n"
    
    latex += "\\end{document}\n"
    
    return latex
def generate_cell_press_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. PREAMBLE
    latex = r"""
\documentclass[12pt,letterpaper]{article}
\usepackage[a4paper, total={7in, 10in}]{geometry}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{graphicx}
\usepackage{helvet}
\usepackage{authblk}
\usepackage{hyperref}
\usepackage{amsmath} 
\usepackage{amssymb} 
\usepackage{orcidlink} 
\usepackage[super,comma,sort&compress]{natbib}
\bibliographystyle{numbered}
\usepackage[right]{lineno} \linenumbers

\makeatletter
\renewcommand{\maketitle}{\bgroup\setlength{\parindent}{0pt}
\begin{flushleft}
  \textbf{\@title}
  
  \@author
\end{flushleft}\egroup}
\makeatother
"""

    # 2. TITLE
    latex += f"\\title{{{title}}}\n"
    latex += "\\date{}\n"

    # 3. AUTHORS & AFFILIATIONS
    # Cell Press uses authblk: \author[1,2]{Name} and \affil[1]{Org}
    # It also uses * for correspondence.
    
    org_map = {}
    org_counter = 1
    
    # Identify unique organizations
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1

    # Generate Authors
    # Logic: [1,2, *]
    for author in authors:
        affils = [str(org_map[author['organization']])]
        
        # Add ORCID if present (using orcidlink package from template)
        if author.get('orcid'):
            affils.append(f"\\orcidlink{{{author['orcid']}}}")
            
        # Add Correspondence marker
        if author.get('is_corresponding'):
            affils.append("*")
        
        affil_str = ",".join(affils)
        latex += f"\\author[{affil_str}]{{{author['name']}}}\n"

    # Generate Affiliations
    for org, oid in org_map.items():
        latex += f"\\affil[{oid}]{{{org}}}\n"

    # Generate Correspondence Footnote
    # Find the corresponding author email
    corr_email = next((a['email'] for a in authors if a.get('is_corresponding')), "email@example.com")
    latex += f"\\affil[*]{{Correspondence: {corr_email}}}\n"

    latex += "\\begin{document}\n"
    latex += "\\maketitle\n\n"

    # 4. SUMMARY (Abstract) & KEYWORDS
    # Cell Press calls the Abstract "SUMMARY"
    latex += f"\\section*{{SUMMARY}}\n{abstract}\n\n"
    latex += f"\\section*{{KEYWORDS}}\n{keywords}\n\n"

    # 5. SECTIONS
    # Cell Press style: \section*{NAME} (All Caps, Unnumbered)
    
    for section_name, content in sections.items():
        header = section_name.upper()
        
        # Special handling for Resource Availability to ensure subsections are formatted correctly
        # if the content isn't pre-formatted latex.
        if header == "RESOURCE AVAILABILITY":
             latex += f"\\section*{{{header}}}\n"
             latex += "\\subsection*{Lead contact}\nRequests for further information should be directed to the lead contact.\n"
             latex += "\\subsection*{Materials availability}\nMaterials are available upon request.\n"
             latex += f"\\subsection*{{Data and code availability}}\n{content}\n\n"
        
        # Standard Handling
        else:
            latex += f"\\section*{{{header}}}\n{content}\n\n"

    # 6. REFERENCES
    latex += "\\bibliography{references}\n"
    
    latex += "\\end{document}\n"

    return latex
def generate_acs_latex(title, authors, abstract, keywords, sections):
    # 1. PREAMBLE
    latex = r"""
\documentclass[letterpaper]{article}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\geometry{margin=1in}
\usepackage{setspace}
\usepackage{graphicx}
\usepackage{float}
\usepackage{authblk}
\usepackage{chemformula}
\usepackage[version=4]{mhchem}
\usepackage[style=chem-acs]{biblatex}
\addbibresource{references.bib}

% ACS generally turns off section numbering
\setcounter{secnumdepth}{-1}

% Float setup for Schemes/Charts typical in Chemistry
\newfloat{scheme}{htbp}{los}
\floatname{scheme}{Scheme}
\newfloat{chart}{htbp}{loh}
\floatname{chart}{Chart}

\begin{document}
"""

    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # ACS template uses 'authblk': \author[1]{Name} and \affil[1]{Org}
    
    org_map = {}
    org_counter = 1
    
    # Identify unique organizations
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1

    # Generate Author entries
    corr_email = None
    for author in authors:
        affil_id = org_map[author['organization']]
        
        # Check for corresponding author
        if author.get('is_corresponding'):
            corr_email = author['email']
            # Using authblk syntax, we can't easily put the email in the author command 
            # without it looking messy, so ACS puts it in \date or a footnote.
        
        latex += f"\\author[{affil_id}]{{{author['name']}}}\n"

    # Generate Affiliation entries
    for org, affil_id in org_map.items():
        latex += f"\\affil[{affil_id}]{{{org}}}\n"

    # 4. CORRESPONDING INFO (in \date)
    if corr_email:
        latex += f"\\date{{*Email: {corr_email}}}\n"
    else:
        latex += "\\date{}\n"

    latex += "\\maketitle\n\n"

    # 5. ABSTRACT
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"

    # 6. KEYWORDS & ABBREVIATIONS (Manual formatting as per template)
    if keywords:
        latex += f"\\section*{{Keywords}}\n{keywords}\n\n"
    
    # Optional Abbreviations section if provided in data, else skip or assume empty
    # latex += "\\section*{Abbreviations}\n...\n\n"

    # 7. SECTIONS LOOP
    for section_name, content in sections.items():
        # Handle specific ACS sections that usually appear at the end
        if section_name.lower() in ['acknowledgements', 'acknowledgments']:
            latex += f"\\section*{{Acknowledgements}}\n{content}\n\n"
        elif section_name.lower() == 'supporting information':
            latex += f"\\section*{{Supporting information}}\n{content}\n\n"
        else:
            # Standard sections (Introduction, Results, etc.)
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. BIBLIOGRAPHY
    latex += "\\printbibliography\n"

    # 9. TOC GRAPHIC (Optional but common in ACS)
    # Adding a placeholder for the graphical abstract if needed
    latex += r"""
\newpage
\rule{0.05in}{1.75in}%
\begin{minipage}[b][1.75in]{3.25in}
  \sffamily
  \frenchspacing
  \centering
  (Insert Table of Contents Graphic Here)
\end{minipage}%
\rule{0.05in}{1.75in}
"""

    latex += "\\end{document}\n"

    return latex
def generate_frontiers_latex(title, authors, abstract, keywords, sections, running_title="Article Title"):
    # 1. PRE-PROCESS AUTHORS & AFFILIATIONS
    # Frontiers requires a specific format: Name$^{1,*}$
    # And a corresponding Address def: $^{1}$Laboratory...
    
    org_map = {}
    org_counter = 1
    
    # Map organizations to IDs
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1

    # Build Author String (\Authors)
    author_list_strs = []
    corr_author_name = ""
    corr_author_email = ""
    first_author_surname = authors[0]['name'].split()[-1] if authors else "Author"
    
    for author in authors:
        # Get ID
        aff_id = org_map[author['organization']]
        
        # Build superscript string e.g. "1,*"
        superscripts = [str(aff_id)]
        if author.get('is_corresponding'):
            superscripts.append("*")
            corr_author_name = author['name']
            corr_author_email = author['email']
        
        # Escape special chars if necessary, mostly assumed clean here
        auth_str = f"{author['name']}\\,$^{{{','.join(superscripts)}}}"
        author_list_strs.append(auth_str)

    # Join authors: "A, B and C"
    if len(author_list_strs) > 1:
        authors_def = ", ".join(author_list_strs[:-1]) + " and " + author_list_strs[-1]
    else:
        authors_def = author_list_strs[0] if author_list_strs else ""

    # Build Address String (\Address)
    address_def = ""
    for org, aff_id in org_map.items():
        address_def += f"$^{{{aff_id}}}${org} \\\\\n"

    # 2. START LATEX GENERATION
    latex = r"""
\documentclass[utf8]{FrontiersinHarvard}
\usepackage{url,hyperref,lineno,microtype,subcaption}
\usepackage[onehalfspacing]{setspace}
\linenumbers

\def\keyFont{\fontsize{8}{11}\helveticabold }
"""
    # 3. INJECT DEFINITIONS
    latex += f"\\def\\firstAuthorLast{{{first_author_surname} {{et~al.}}}}\n"
    latex += f"\\def\\Authors{{{authors_def}}}\n"
    latex += f"\\def\\Address{{{address_def}}}\n"
    latex += f"\\def\\corrAuthor{{{corr_author_name}}}\n"
    latex += f"\\def\\corrEmail{{{corr_author_email}}}\n"

    latex += r"""
\begin{document}
\onecolumn
\firstpage{1}
"""
    # 4. TITLE & MAKETITLE
    latex += f"\\title[{running_title}]{{{title}}}\n"
    latex += "\\author[\\firstAuthorLast ]{\\Authors}\n"
    latex += "\\address{}\n"
    latex += "\\correspondance{}\n"
    latex += "\\extraAuth{}\n"
    latex += "\\maketitle\n\n"

    # 5. ABSTRACT & KEYWORDS
    # Frontiers puts keywords INSIDE the abstract environment at the bottom
    latex += "\\begin{abstract}\n"
    latex += f"{abstract}\n\n"
    latex += "\\tiny\n"
    latex += f" \\keyFont{{ \\section{{Keywords:}} {keywords}}}\n"
    latex += "\\end{abstract}\n\n"

    # 6. SECTIONS LOOP
    # Frontiers uses \section* for back-matter (Conflict, Funding, etc.) and \section for main body.
    # We define a list of sections that should be unnumbered.
    back_matter_sections = [
        'conflict of interest statement',
        'author contributions',
        'funding',
        'acknowledgments',
        'supplemental data',
        'data availability statement'
    ]

    for section_name, content in sections.items():
        if section_name.lower() in back_matter_sections:
            latex += f"\\section*{{{section_name}}}\n{content}\n\n"
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 7. BIBLIOGRAPHY
    latex += "\\bibliographystyle{Frontiers-Harvard}\n"
    latex += "\\bibliography{references}\n"
    
    latex += "\\end{document}\n"

    return latex
def generate_elsarticle_latex(title, authors, abstract, keywords, sections, journal_meta):
    # 1. SETUP CLASS & PACKAGES
    # Using the 5p, twocolumn options from the example for the standard journal look
    latex = r"""
\documentclass[final,5p,times,twocolumn,authoryear]{elsarticle}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{lineno}

"""
    # Set Journal Name
    j_name = journal_meta.get('journal_name', 'Astronomy & Computing')
    latex += f"\\journal{{{j_name}}}\n"

    latex += r"""
\begin{document}
\begin{frontmatter}
"""

    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # Logic: Map unique organizations to labels (aff1, aff2, etc.)
    # Elsarticle uses \author[label]{Name} and \affiliation[label]{details}
    
    org_map = {}
    org_counter = 1
    
    # Identify unique organizations
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = f"aff{org_counter}"
            org_counter += 1

    # Generate Authors
    for author in authors:
        aff_label = org_map[author['organization']]
        # Use \corref{cor1} if corresponding? 
        # For simplicity, we just list authors here. 
        # If specific footnote needed: \author[aff_label]{Name\corref{cor1}}
        
        latex += f"\\author[{aff_label}]{{{author['name']}}}\n"

    # Generate Affiliations
    for org, label in org_map.items():
        # Elsarticle affiliation format is detailed. We map the generic 'organization' string to the organization field.
        # Assuming we don't have granular city/country data in the simple input object, we leave them blank or generic.
        latex += f"\\affiliation[{label}]{{organization={{{org}}}}}"
        latex += "\n"

    # 4. ABSTRACT
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"

    # 5. KEYWORDS
    # Keywords in elsarticle are separated by \sep
    # Assuming 'keywords' input is a comma-separated string, we replace commas with \sep
    if keywords:
        formatted_keywords = keywords.replace(",", " \\sep")
        latex += f"\\begin{{keyword}}\n{formatted_keywords}\n\\end{{keyword}}\n"

    latex += "\\end{frontmatter}\n\n"
    
    # Optional: Table of contents or lineno
    # latex += "\\linenumbers\n"

    # 6. SECTIONS LOOP
    for section_name, content in sections.items():
        
        # Handle Appendices
        if section_name.lower() in ['appendix', 'appendices']:
            latex += f"\\appendix\n{content}\n\n"
        
        # Handle Acknowledgements (usually unnumbered in many templates, but standard section in some)
        elif section_name.lower() in ['acknowledgments', 'acknowledgements']:
            latex += f"\\section*{{Acknowledgments}}\n{content}\n\n"
            
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 7. BIBLIOGRAPHY
    # Use the harvard style as defined in the class options
    latex += "\\bibliographystyle{elsarticle-harv}\n"
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_ajp_latex(title, authors, abstract, sections):
    # 1. PREAMBLE & PACKAGES
    latex = r"""
% !TeX encoding = UTF-8
% !TeX spellcheck = en_US
% !TeX TS-program = pdflatex
% !BIB TS-program = bibtex

\documentclass[prb,preprint,letterpaper,noeprint,longbibliography,nodoi,footinbib]{revtex4-1}
\usepackage[colorlinks, allcolors=blue]{hyperref}
\bibliographystyle{AJP}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{graphicx}

\begin{document}
"""
    
    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # REVTeX allows interleaved \author and \affiliation commands.
    # We will loop through authors and immediately place their affiliation.
    # Note: If multiple authors share an affiliation, REVTeX handles repetition gracefully,
    # but strictly grouping them is also common. Here is a simple direct mapping:
    
    for author in authors:
        latex += f"\\author{{{author['name']}}}\n"
        if author.get('email'):
            latex += f"\\email{{{author['email']}}}\n"
        
        # Add affiliation immediately after author
        latex += f"\\affiliation{{{author['organization']}}}\n"
        
        # Handle optional second address if present in data
        if author.get('second_address'):
            latex += f"\\altaffiliation{{{author['second_address']}}}\n"

    latex += f"\\date{{\\today}}\n"

    # 4. ABSTRACT (Must be before \maketitle in REVTeX)
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"

    # 5. MAKETITLE
    latex += "\\maketitle\n\n"

    # 6. SECTIONS LOOP
    for section_name, content in sections.items():
        # Handle Acknowledgments (REVTeX specific environment)
        if section_name.lower() in ['acknowledgments', 'acknowledgements', 'acknowledgement']:
            latex += f"\\begin{{acknowledgments}}\n{content}\n\\end{{acknowledgments}}\n\n"
        
        # Handle Appendix
        elif section_name.lower() in ['appendix', 'appendices']:
            # Use \appendix* if it's a single appendix block
            latex += f"\\appendix*\n\\section{{}}\n{content}\n\n"
        
        # Standard Sections
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 7. BIBLIOGRAPHY
    # AJP typically asks for BibTeX during submission, or pasted .bbl content for final.
    # We will generate the BibTeX command.
    latex += "\\bibliography{AJPTemplate}\n"

    latex += "\\end{document}\n"

    return latex
def generate_aip_latex(title, authors, abstract, keywords, sections):
    # 1. PREAMBLE & PACKAGES
    latex = r"""
\documentclass[aip,amsmath,amssymb,reprint]{revtex4-1}

\usepackage{graphicx}
\usepackage{dcolumn}
\usepackage{bm}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage{etoolbox}

%% Apr 2021: AIP requests that the corresponding 
%% email to be moved after the affiliations
\makeatletter
\def\@email#1#2{%
 \endgroup
 \patchcmd{\titleblock@produce}
  {\frontmatter@RRAPformat}
  {\frontmatter@RRAPformat{\produce@RRAP{*#1\href{mailto:#2}{#2}}}\frontmatter@RRAPformat}
  {}{}
}%
\makeatother

\begin{document}
"""

    # 2. METADATA (Title, Authors, Date)
    latex += f"\\title{{{title}}}\n"

    # REVTeX allows interleaving author/affiliation.
    # We will loop through authors and place their affiliation immediately after.
    for author in authors:
        latex += f"\\author{{{author['name']}}}\n"
        
        # Add email if present
        if author.get('email'):
            latex += f" \\email{{{author['email']}}}\n"
            
        # Add Affiliation
        # Assuming 'organization' holds the primary affiliation
        if author.get('organization'):
            latex += f" \\affiliation{{{author['organization']}}}\n"
            
        # Add Altaffiliation if present (e.g., secondary address)
        if author.get('second_address'):
            latex += f" \\altaffiliation{{{author['second_address']}}}\n"

    latex += "\\date{\\today}\n"

    # 3. ABSTRACT (Must appear before \maketitle in REVTeX)
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n"

    # 4. MAKETITLE
    latex += "\\maketitle\n\n"

    # 5. SECTIONS LOOP
    for section_name, content in sections.items():
        
        # Special Handling for "Lead Paragraph" (Quotation environment)
        # Used often in AIP journals like 'Chaos'
        if section_name.lower() == 'lead paragraph':
            latex += f"\\begin{{quotation}}\n{content}\n\\end{{quotation}}\n\n"

        # Special Handling for Acknowledgments (Specific environment)
        elif section_name.lower() in ['acknowledgments', 'acknowledgements']:
            latex += f"\\begin{{acknowledgments}}\n{content}\n\\end{{acknowledgments}}\n\n"

        # Special Handling for Data Availability (Unnumbered Section)
        elif section_name.lower() == 'data availability statement':
            latex += f"\\section*{{Data Availability Statement}}\n{content}\n\n"

        # Special Handling for Appendix
        elif section_name.lower() in ['appendix', 'appendices']:
            latex += f"\\appendix\n{content}\n\n"

        # Standard Sections
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. BIBLIOGRAPHY
    latex += "\\nocite{*}\n" # Include all refs or remove based on preference
    latex += "\\bibliography{aipsamp}\n"
    
    latex += "\\end{document}\n"

    return latex
def generate_science_latex(title, authors, abstract, keywords, sections):
    # 1. PREAMBLE
    latex = r"""
\documentclass[12pt]{article}
\usepackage{newtxtext,newtxmath}
\usepackage{graphicx}
\usepackage[letterpaper,margin=1in]{geometry}
\linespread{1.5}
\frenchspacing
\usepackage{scicite}
\usepackage{url}

% Abstract formatting
\renewenvironment{abstract}
	{\quotation}
	{\endquotation}

\date{}
\renewcommand\refname{References and Notes}

% Bold Figure/Table labels
\makeatletter
\renewcommand{\fnum@figure}{\textbf{Figure \thefigure}}
\renewcommand{\fnum@table}{\textbf{Table \thetable}}
\makeatother

\def\scititle{""" + title + r"""}
\title{\bfseries \boldmath \scititle}
"""

    # 2. AUTHORS & AFFILIATIONS
    # Science uses a manual formatting within \author{}:
    # Name$^{1,2\ast}$, Name2$^{1}$ \and \small^{1}Affil...
    
    org_map = {}
    org_counter = 1
    
    # Map organizations to IDs
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = org_counter
            org_counter += 1

    author_names = []
    
    # Build Author Names part
    for author in authors:
        aff_id = org_map[author['organization']]
        # Superscript string
        superscripts = [str(aff_id)]
        if author.get('is_corresponding'):
            superscripts.append(r"\ast")
        
        auth_str = f"{author['name']}$^{{{','.join(superscripts)}}}"
        author_names.append(auth_str)

    # Build Affiliations part
    affil_lines = []
    for org, aff_id in org_map.items():
        affil_lines.append(f"\\small$^{{{aff_id}}}${org}.")

    # Add Corresponding email if found
    corr_email = next((a['email'] for a in authors if a.get('is_corresponding')), None)
    if corr_email:
        affil_lines.append(f"\\small$^\\ast$Corresponding author. Email: {corr_email}")

    # Combine into \author block
    # Note: Science uses \and to separate the name block from the affiliation block
    latex += "\\author{\n"
    latex += ", ".join(author_names) + "\\and\n"
    latex += "\\and\n".join(affil_lines)
    latex += "\n}\n"

    latex += "\\begin{document}\n"
    latex += "\\maketitle\n"

    # 3. ABSTRACT
    # Science abstracts are bold
    latex += f"\\begin{{abstract}} \\bfseries \\boldmath\n{abstract}\n\\end{{abstract}}\n\n"

    # 4. MAIN SECTIONS
    # Science specific: Introduction has NO header.
    # Other sections use \subsection*.
    
    # We segregate Supplementary material to handle it at the end
    supp_content = None
    
    for section_name, content in sections.items():
        key = section_name.lower().strip()
        
        if key == 'introduction':
            latex += f"\\noindent\n{content}\n\n"
            
        elif key == 'acknowledgments':
            latex += f"\\section*{{Acknowledgments}}\n{content}\n\n"
            
        elif key in ['supplementary materials', 'supplementary text']:
            supp_content = content # Save for end
            
        elif key == 'materials and methods':
            # Often appearing in supplement for Science, but can be main text.
            # We will treat as main text subsection unless user specifically put it in 'supplementary' key
            latex += f"\\subsection*{{Materials and Methods}}\n{content}\n\n"
            
        else:
            latex += f"\\subsection*{{{section_name}}}\n{content}\n\n"

    # 5. REFERENCES (Main Text)
    latex += "\\bibliographystyle{sciencemag}\n"
    latex += "\\bibliography{references}\n"

    # 6. SUPPLEMENTARY MATERIALS (If applicable)
    if supp_content:
        latex += r"""
\newpage
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\theequation}{S\arabic{equation}}
\setcounter{figure}{0}
\setcounter{table}{0}
\setcounter{equation}{0}

\begin{center}
\section*{Supplementary Materials for\\ \scititle}
\end{center}
"""
        latex += f"{supp_content}\n"

    latex += "\\end{document}\n"

    return latex
def generate_rsc_latex(title, authors, abstract, sections, journal_meta):
    # 1. PREAMBLE
    latex = r"""
\documentclass[twoside,twocolumn,9pt]{article}
\usepackage{extsizes}
\usepackage[super,sort&compress,comma]{natbib} 
\usepackage[version=3]{mhchem}
\usepackage[left=1.5cm, right=1.5cm, top=1.785cm, bottom=2.0cm]{geometry}
\usepackage{balance}
\usepackage{mathptmx}
\usepackage{sectsty}
\usepackage{graphicx} 
\usepackage{lastpage}
\usepackage[format=plain,justification=justified,singlelinecheck=false,font={stretch=1.125,small,sf},labelfont=bf,labelsep=space]{caption}
\usepackage{float}
\usepackage{fancyhdr}
\usepackage{fnpos}
\usepackage[english]{babel}
\addto{\captionsenglish}{%
  \renewcommand{\refname}{Notes and references}
}
\usepackage{array}
\usepackage{droidsans}
\usepackage{charter}
\usepackage[T1]{fontenc}
\usepackage[usenames,dvipsnames]{xcolor}
\usepackage{setspace}
\usepackage[compact]{titlesec}
\usepackage{hyperref}
\usepackage{epstopdf}

\definecolor{cream}{RGB}{222,217,201}

\begin{document}

\pagestyle{fancy}
\thispagestyle{plain}
\fancypagestyle{plain}{
\renewcommand{\headrulewidth}{0pt}
}

\makeFNbottom
\makeatletter
\renewcommand\LARGE{\@setfontsize\LARGE{15pt}{17}}
\renewcommand\Large{\@setfontsize\Large{12pt}{14}}
\renewcommand\large{\@setfontsize\large{10pt}{12}}
\renewcommand\footnotesize{\@setfontsize\footnotesize{7pt}{10}}
\makeatother

\renewcommand{\thefootnote}{\fnsymbol{footnote}}
\renewcommand\footnoterule{\vspace*{1pt}% 
\color{cream}\hrule width 3.5in height 0.4pt \color{black}\vspace*{5pt}} 
\setcounter{secnumdepth}{5}

\makeatletter 
\renewcommand\@biblabel[1]{#1}            
\renewcommand\@makefntext[1]% 
{\noindent\makebox[0pt][r]{\@thefnmark\,}#1}
\makeatother 
\renewcommand{\figurename}{\small{Fig.}~}
\sectionfont{\sffamily\Large}
\subsectionfont{\normalsize}
\subsubsectionfont{\bf}
\setstretch{1.125}
\setlength{\skip\footins}{0.8cm}
\setlength{\footnotesep}{0.25cm}
\setlength{\jot}{10pt}
\titlespacing*{\section}{0pt}{4pt}{4pt}
\titlespacing*{\subsection}{0pt}{15pt}{1pt}

\fancyfoot{}
\fancyfoot[LO,RE]{\vspace{-7.1pt}\includegraphics[height=9pt]{head_foot/LF}}
\fancyfoot[CO]{\vspace{-7.1pt}\hspace{13.2cm}\includegraphics{head_foot/RF}}
\fancyfoot[CE]{\vspace{-7.2pt}\hspace{-14.2cm}\includegraphics{head_foot/RF}}
\fancyfoot[RO]{\footnotesize{\sffamily{1--\pageref{LastPage} ~\textbar  \hspace{2pt}\thepage}}}
\fancyfoot[LE]{\footnotesize{\sffamily{\thepage~\textbar\hspace{3.45cm} 1--\pageref{LastPage}}}}
\fancyhead{}
\renewcommand{\headrulewidth}{0pt} 
\renewcommand{\footrulewidth}{0pt}
\setlength{\arrayrulewidth}{1pt}
\setlength{\columnsep}{6.5mm}
\setlength\bibsep{1pt}

\makeatletter 
\newlength{\figrulesep} 
\setlength{\figrulesep}{0.5\textfloatsep} 

\newcommand{\topfigrule}{\vspace*{-1pt}% 
\noindent{\color{cream}\rule[-\figrulesep]{\columnwidth}{1.5pt}} }

\newcommand{\botfigrule}{\vspace*{-2pt}% 
\noindent{\color{cream}\rule[\figrulesep]{\columnwidth}{1.5pt}} }

\newcommand{\dblfigrule}{\vspace*{-1pt}% 
\noindent{\color{cream}\rule[-\figrulesep]{\textwidth}{1.5pt}} }

\makeatother
"""

    # 3. TITLE, AUTHORS & ABSTRACT (Inside twocolumn)
    # The RSC template manually constructs the header block using a tabular environment inside \twocolumn[...]
    
    # Process Authors for the manual block
    # Name formatting: "Full Name,$^{\ast}$\textit{$^{a}$}"
    author_latex_list = []
    org_map = {}
    org_counter = ord('a') # a, b, c...
    
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = chr(org_counter)
            org_counter += 1
        
        aff_char = org_map[org]
        star = r"$^{\ast}$" if author.get('is_corresponding') else ""
        
        # Format: Name,STAR\textit{^char}
        entry = f"{author['name']},{star}\\textit{{$^{{{aff_char}}}$}}"
        author_latex_list.append(entry)

    author_block = ", ".join(author_latex_list)

    latex += r"""
\twocolumn[
  \begin{@twocolumnfalse}
{\includegraphics[height=30pt]{head_foot/journal_name}\hfill\raisebox{0pt}[0pt][0pt]{\includegraphics[height=55pt]{head_foot/RSC_LOGO_CMYK}}\\[1ex]
\includegraphics[width=18.5cm]{head_foot/header_bar}}\par
\vspace{1em}
\sffamily
\begin{tabular}{m{4.5cm} p{13.5cm} }

\includegraphics{head_foot/DOI} & \noindent\LARGE{\textbf{""" + title + r"""$^\dag$}} \\
\vspace{0.3cm} & \vspace{0.3cm} \\

 & \noindent\large{""" + author_block + r"""} \\

\includegraphics{head_foot/dates} & \noindent\normalsize{""" + abstract + r"""} \\

\end{tabular}

 \end{@twocolumnfalse} \vspace{0.6cm}

  ]
"""

    # 4. RESET FONT & ADD FOOTNOTES
    latex += r"""
\renewcommand*\rmdefault{bch}\normalfont\upshape
\rmfamily
\section*{}
\vspace{-1cm}
"""
    # Affiliation Footnotes
    for org, char in org_map.items():
        latex += f"\\footnotetext{{\\textit{{$^{{{char}}}$~{org}}}}}" + "\n"

    # 5. SECTIONS LOOP
    # Special sections in RSC: Conclusions, Author contributions, Conflicts of interest, Data availability, Acknowledgements
    # These are typically \section*{...} (unnumbered) at the end.
    
    special_sections = [
        'conclusions', 
        'author contributions', 
        'conflicts of interest', 
        'data availability', 
        'acknowledgements',
        'acknowledgments'
    ]

    for section_name, content in sections.items():
        if section_name.lower() in special_sections:
            latex += f"\\section*{{{section_name}}}\n{content}\n\n"
        else:
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. BIBLIOGRAPHY
    latex += "\\balance\n" # Balances columns on last page
    latex += "\\bibliography{rsc}\n"
    latex += "\\bibliographystyle{rsc}\n"

    latex += "\\end{document}\n"

    return latex
def generate_asm_latex(title, authors, abstract, keywords, sections):
    # 1. PREAMBLE
    latex = r"""
\documentclass{asmarticle}
\usepackage{url}
\usepackage{graphicx}
\usepackage[sort&compress]{natbib}

\begin{document}
"""

    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # ASM puts all authors in one \author{} command, comma separated.
    # Affiliations are referenced via \afn{1}, and listed via sequential \affil{} commands.
    
    org_map = {}
    org_list = []
    author_parts = []
    corr_address = ""

    # Map organizations to indices (1, 2, 3...)
    for author in authors:
        org = author['organization']
        if org not in org_map:
            org_map[org] = len(org_list) + 1
            org_list.append(org)
        
        idx = org_map[org]
        
        # Build author string: "Name\afn{1}"
        # Check for corresponding author (*)
        if author.get('is_corresponding'):
            marker = f"{idx}*"
            # Construct correspondence string
            corr_address = f"\\corraddress{{Address correspondence to {author['name']}, {author['email']}.}}"
        else:
            marker = f"{idx}"
            
        author_parts.append(f"{author['name']}\\afn{{{marker}}}")

    # Combine authors
    latex += "\\author{" + ", ".join(author_parts) + "}\n\n"

    # List affiliations
    for org in org_list:
        latex += f"\\affil{{{org}}}\n"

    # Add correspondence info
    latex += f"{corr_address}\n"

    latex += "\\maketitle\n\n"

    # 4. ABSTRACT & IMPORTANCE
    # ASM requires the "Importance" section to be nested INSIDE the abstract environment.
    latex += "\\begin{abstract}\n"
    latex += f"{abstract}\n"
    
    # Check if 'Importance' exists in sections and move it here
    if 'Importance' in sections:
        latex += f"\\begin{{importance}}\n{sections['Importance']}\n\\end{{importance}}\n"
        del sections['Importance'] # Remove so it doesn't print again later
    
    latex += "\\end{abstract}\n\n"

    # 5. SECTIONS LOOP
    # ASM uses specific environments for backmatter to support blind reviews.
    
    special_envs = {
        'acknowledgments': 'acknowledgments',
        'funding': 'funding',
        'conflicts of interest': 'conflictsinterest',
        'author biographies': 'authorbios'
    }

    for section_name, content in sections.items():
        key = section_name.lower().strip()
        
        # Handle Special Environments
        if key in special_envs:
            env_name = special_envs[key]
            latex += f"\\begin{{{env_name}}}\n\\section{{{section_name.upper()}}}\n{content}\n\\end{{{env_name}}}\n\n"
        
        # Standard Sections (Intro, Methods, Results, Discussion)
        # ASM typically uses UPPERCASE for main section headers
        else:
            latex += f"\\section{{{section_name.upper()}}}\n{content}\n\n"

    # 6. REFERENCES
    latex += "\\bibliographystyle{asm}\n" # Assuming asm.bst exists in their package
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_asme_latex(title, authors, abstract, keywords, sections, journal_name="Heat Transfer"):
    # 1. HEADER & PREAMBLE
    latex = r"""
\documentclass[subscriptcorrection,upint,varvw,barcolor=Goldenrod3,mathalfa=cal=euler,balance,hyphenate,pdf-a]{asmejour}

\hypersetup{
    pdfauthor={ASME Author},
    pdftitle={ASME Journal Paper},
    pdfkeywords={ASME, Journal, Template}
}
"""
    # 2. JOURNAL CONFIGURATION
    latex += f"\\JourName{{{journal_name}}}\n"

    # 3. AUTHOR BLOCK
    # ASME uses \SetAuthorBlock{Name}{Affiliation}
    # It uses \CorrespondingAuthor inside the name field for the contact person.
    latex += r"""
\begin{document}
"""
    for author in authors:
        # Check for corresponding author flag
        name_str = author['name']
        if author.get('is_corresponding', False):
            name_str += r"\CorrespondingAuthor"
            # Optional: Add email to corresponding author macro if needed, e.g., \CorrespondingAuthor{email}
        
        # Build affiliation string (Organization, Address, Email)
        affiliation_str = f"{author['organization']}\\\\\n{author.get('address', '')}\\\\\nemail: {author.get('email', '')}"
        
        latex += f"\\SetAuthorBlock{{{name_str}}}{{{affiliation_str}}}\n"

    # 4. TITLE AND KEYWORDS
    latex += f"\\title{{{title}}}\n"
    
    # Keywords must appear BEFORE the abstract end in this template
    if keywords:
        latex += f"\\keywords{{{keywords}}}\n"

    # 5. ABSTRACT
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"

    # 6. DATE & MAKETITLE
    latex += r"\date{\today}" + "\n"
    latex += r"\maketitle" + "\n"

    # 7. SECTIONS LOOP
    for section_name, content in sections.items():
        # Handle Special ASME Sections
        if section_name.lower() == 'nomenclature':
            # Assumes content is formatted as \entry{symbol}{def} lines
            latex += f"\\begin{{nomenclature}}\n{content}\n\\end{{nomenclature}}\n\n"
        
        elif section_name.lower() in ['acknowledgment', 'funding data']:
            # ASME uses \section* for these specific back-matter sections
            latex += f"\\section*{{{section_name}}}\n{content}\n\n"
            
        elif section_name.lower() in ['appendix', 'appendices']:
            latex += f"\\appendix\n{content}\n\n"
            
        else:
            # Standard numbered sections
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. BIBLIOGRAPHY
    latex += r"""
\bibliographystyle{asmejour}
\bibliography{references}
\end{document}
"""
    return latex
def generate_ams_tran_latex(title, authors, abstract, sections, journal_meta):
    # 1. PREAMBLE & THEOREM DEFINITIONS
    latex = r"""
\documentclass{tran-l}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage[cmtip,all]{xy}

% Theorem Definitions required by AMS template
\newtheorem{theorem}{Theorem}[section]
\newtheorem{lemma}[theorem]{Lemma}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}
\newtheorem{xca}[theorem]{Exercise}

\theoremstyle{remark}
\newtheorem{remark}[theorem]{Remark}

\numberwithin{equation}{section}

\begin{document}
"""

    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS
    # AMS requires looping through authors and creating a distinct block for each
    for author in authors:
        latex += f"\\author{{{author['name']}}}\n"
        
        # Address is usually the organization/institution
        if author.get('organization'):
            latex += f"\\address{{{author['organization']}}}\n"
        
        # Current address (optional)
        if author.get('current_address'):
            latex += f"\\curraddr{{{author['current_address']}}}\n"
            
        if author.get('email'):
            latex += f"\\email{{{author['email']}}}\n"
            
        if author.get('thanks'):
            latex += f"\\thanks{{{author['thanks']}}}\n"
        
        latex += "\n"

    # 4. SUBJECT CLASSIFICATION & DATES
    # Required by AMS. Defaults provided if missing from journal_meta.
    subj_class = journal_meta.get('subj_class', 'Primary 54C40, 14E20; Secondary 46E25, 20C20')
    latex += f"\\subjclass[2010]{{{subj_class}}}\n"
    
    latex += "\\date{\\today}\n"
    
    if journal_meta.get('dedicatory'):
        latex += f"\\dedicatory{{{journal_meta['dedicatory']}}}\n"

    # 5. ABSTRACT
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"

    latex += "\\maketitle\n\n"

    # 6. SECTIONS LOOP
    # AMS uses standard \section commands
    for section_name, content in sections.items():
        latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 7. BIBLIOGRAPHY
    latex += "\\bibliographystyle{amsplain}\n"
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_ios_press_latex(title, authors, abstract, keywords, sections):
    # 1. PREAMBLE
    latex = r"""\documentclass{IOS-Book-Article}
\usepackage{mathptmx}
\usepackage{graphicx}

\begin{document}
\begin{frontmatter}
"""

    # 2. TITLE & RUNNING TITLE
    latex += f"\\title{{{title}}}\n"
    # Simplified running title logic (first 50 chars)
    latex += f"\\runningtitle{{{title[:50]}...}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # Logic: Map organizations to keys A, B, C...
    # Split names into First (fnms) and Surname (snm).
    
    org_map = {}
    org_keys = []
    
    # Identify unique organizations
    for author in authors:
        org = author['organization']
        if org not in org_map:
            key = chr(ord('A') + len(org_keys)) # A, B, C...
            org_map[org] = key
            org_keys.append(org)

    # Generate Author Entries
    author_latex_list = []
    for author in authors:
        key = org_map[author['organization']]
        
        # Split Name
        parts = author['name'].split()
        if len(parts) > 1:
            fnms = " ".join(parts[:-1])
            snm = parts[-1]
        else:
            fnms = ""
            snm = parts[0]
            
        entry = f"\\author[{key}]{{\\fnms{{{fnms}}} \\snm{{{snm}}}"
        
        # Corresponding Author Footnote
        if author.get('is_corresponding'):
            entry += f"\\thanks{{Corresponding Author: {author['name']}, {author['organization']}; E-mail: {author['email']}.}}"
        
        entry += "}"
        author_latex_list.append(entry)

    # Join authors with commas and "and"
    if len(author_latex_list) > 1:
        authors_str = ", ".join(author_latex_list[:-1]) + "\nand\n" + author_latex_list[-1]
    else:
        authors_str = author_latex_list[0] if author_latex_list else ""

    latex += f"{authors_str}\n\n"

    # Generate Running Author
    first_author_surname = authors[0]['name'].split()[-1] if authors else "Author"
    latex += f"\\runningauthor{{{first_author_surname} et al.}}\n"

    # Generate Addresses
    for org in org_keys:
        key = org_map[org]
        latex += f"\\address[{key}]{{{org}}}\n"

    # 4. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n"
    
    if keywords:
        # IOS Press separates keywords with \sep
        formatted_keywords = keywords.replace(",", "\\sep")
        latex += f"\\begin{{keyword}}\n{formatted_keywords}\n\\end{{keyword}}\n"

    latex += "\\end{frontmatter}\n"
    latex += "\\thispagestyle{empty}\n\\pagestyle{empty}\n"

    # 5. SECTIONS LOOP
    for section_name, content in sections.items():
        # IOS Press usually numbers sections, except Introduction sometimes in examples.
        # We will use standard numbering for all.
        latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. BIBLIOGRAPHY
    # IOS Press often uses numbered references. 
    # Assuming manual bib items or standard bibtex. Using standard bibtex setup here for flexibility.
    latex += "\\bibliographystyle{vancouver}\n" # Common choice, though manual doesn't specify strictly
    latex += "\\bibliography{references}\n"

    latex += "\\end{document}\n"

    return latex
def generate_spie_latex(title, authors, abstract, keywords, sections):
    # 1. PREAMBLE
    latex = r"""
\documentclass[12pt]{spieman}
\usepackage{amsmath,amsfonts,amssymb}
\usepackage{graphicx}
\usepackage{setspace}
\usepackage{tocloft}
\usepackage{lineno}
\linenumbers

\renewcommand{\cftdotsep}{\cftnodots}
\cftpagenumbersoff{figure}
\cftpagenumbersoff{table} 

\begin{document} 
"""

    # 2. TITLE
    latex += f"\\title{{{title}}}\n"

    # 3. AUTHORS & AFFILIATIONS
    # Logic: Map organizations to 'a', 'b', 'c'...
    # Format: \author[a]{Name} ... \affil[a]{Address}
    
    org_map = {}
    org_keys = []
    
    # Identify unique organizations
    for author in authors:
        org = author['organization']
        if org not in org_map:
            key = chr(ord('a') + len(org_keys)) # a, b, c...
            org_map[org] = key
            org_keys.append(org)

    # Generate Author Entries
    corr_author_name = ""
    corr_author_email = ""

    for author in authors:
        key = org_map[author['organization']]
        affil_marker = key
        
        # Check for Corresponding Author (*)
        if author.get('is_corresponding'):
            affil_marker += ",*"
            corr_author_name = author['name']
            corr_author_email = author['email']
        
        latex += f"\\author[{affil_marker}]{{{author['name']}}}\n"

    # Generate Affiliations
    for org in org_keys:
        key = org_map[org]
        latex += f"\\affil[{key}]{{{org}}}\n"

    latex += "\\maketitle\n\n"

    # 4. ABSTRACT & KEYWORDS
    latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\n"
    latex += f"\\keywords{{{keywords}}}\n\n"

    # 5. CORRESPONDING AUTHOR FOOTNOTE (Manual formatting required by SPIE)
    if corr_author_name:
        latex += f"{{\\noindent \\footnotesize\\textbf{{*}}{corr_author_name},  \\linkable{{{corr_author_email}}} }}\n\n"

    # 6. MAIN BODY (Double Spaced)
    latex += "\\begin{spacing}{2}\n"

    # 7. SECTIONS LOOP
    # SPIE Specifics: Disclosures, Acknowledgments, Data Availability are often unnumbered subsections (\subsection*)
    # Biographies are plain text at the end.
    
    unnumbered_subsections = [
        'disclosures',
        'acknowledgments',
        'acknowledgements',
        'code, data, and materials availability',
        'data availability'
    ]

    for section_name, content in sections.items():
        key = section_name.lower().strip()
        
        if key == 'biographies':
            # Biographies are just text at the end, often separated by vspace
            latex += f"\\vspace{{2ex}}\\noindent {content}\n\n"
            
        elif key in unnumbered_subsections:
            latex += f"\\subsection*{{{section_name}}}\n{content}\n\n"
            
        elif key in ['appendix', 'appendices']:
            latex += f"\\appendix\n\\section{{}}\n{content}\n\n"
            
        else:
            # Standard numbered section
            latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 8. BIBLIOGRAPHY
    latex += "\\bibliographystyle{spiejour}\n"
    latex += "\\bibliography{report}\n"
    
    latex += "\\listoffigures\n"
    latex += "\\listoftables\n"
    latex += "\\end{spacing}\n"
    latex += "\\end{document}\n"

    return latex

def generate_mla_latex(title, authors, abstract, sections, course_info):
    # 1. PREAMBLE
    latex = r"""
\documentclass{article}
\usepackage{mla13}
\usepackage{graphicx}
\usepackage{lipsum} 

"""
    # 2. METADATA
    # Extract first author details (MLA usually focuses on the student/single author context)
    first_author = authors[0] if authors else {'name': 'Author Name'}
    name_parts = first_author['name'].split()
    firstname = name_parts[0] if name_parts else ""
    lastname = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    latex += f"\\title{{{title}}}\n"
    latex += f"\\firstname{{{firstname}}}\n"
    latex += f"\\lastname{{{lastname}}}\n"
    
    # Course / Professor Info (defaults if missing)
    professor = course_info.get('professor', 'Professor Name')
    course_name = course_info.get('course_name', 'Class Name')
    
    latex += f"\\professor{{{professor}}}\n"
    latex += f"\\class{{{course_name}}}\n"
    
    # Define bibliography file
    latex += "\\sources{references.bib}\n"

    latex += r"""
\begin{document}
% Title Page
\maketitlepage
\newpage

% Table of Contents
\tableofcontents
\newpage
"""

    # 3. ABSTRACT
    if abstract:
        latex += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n\\newpage\n"

    # 4. MAIN CONTENT START
    latex += "\\makeheader\n" # Adds MLA header (Surname Page#)
    latex += "\\maketitle\n\n" # Adds Title block on first page of text

    # 5. SECTIONS LOOP
    for section_name, content in sections.items():
        # Skip 'Works Cited' if it's passed as a section, handled by command
        if section_name.lower() == 'works cited':
            continue
            
        latex += f"\\section{{{section_name}}}\n{content}\n\n"

    # 6. WORKS CITED
    latex += "\\newpage\n"
    latex += "\\makeworkscited\n"
    
    latex += "\\end{document}\n"

    return latex