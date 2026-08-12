"""
extractors.py — Field extractor functions for tender documents.

No standard format is assumed. Every extractor tries multiple strategies
ordered from most-specific to most-general and stops at the first good hit.
"""
import re

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

_MONTHS = (r'Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?'
           r'|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?')

_BOILERPLATE = re.compile(
    r'prevention\s+and\s+combating|not\s+exceeding\s+ten'
    r'|agreed\s+by\s+the\s+parties|means\s+(?:a|an|the)\b'
    r'|business\s+day\s+means|designated\s+sector',
    re.IGNORECASE
)

_GC_JUNK = re.compile(
    r'general\s+conditions?\s+of\s+contract'
    r'|furnished\s+by\s+or\s+on\s+behalf\s+of\s+the\s+purchaser'
    r'|shall\s+not\s+disclose|PFMA|Public\s+Finance\s+Management'
    r'|provincial\s+public\s+entity'
    r'|any\s+person\s+\(natural\s+or\s+juristic\)\s+may\s+make\s+an\s+offer'
    r'|purpose\s+of\s+the\s+form',
    re.IGNORECASE
)


def _cv(v):
    """Collapse internal whitespace."""
    return ' '.join(v.split()) if v else ''


def _coerce_sections(sections):
    if isinstance(sections, dict):
        return sections
    return {'full': sections or ''}


def _clean_page_artefacts(text):
    """Strip running page headers and standalone page-number lines."""
    text = re.sub(r'Reference\s+(?:nr|no)[.:][^\n]*\d\s*\|\s*P\s*a\s*g\s*e[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\s*\d+\s*\|\s*P\s*a\s*g\s*e\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    text = re.sub(r'^\s*(?:RFQ|RFP|RFI|RFT)\s+[\w/\-. ]{3,30}\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
    return text


def _collapse_blanks(text):
    """Collapse runs of 2+ blank lines into one."""
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _section_body(text, *heading_patterns):
    """
    Find the first matching heading in text and return the content until
    the next major heading. Returns '' if not found.
    """
    combined = '|'.join(f'(?:{p})' for p in heading_patterns)
    m = re.search(combined, text, re.IGNORECASE)
    if not m:
        return ''
    after = text[m.end():]
    stop = re.search(
        r'\n[ \t]*\n[ \t]*(?:\d+[\.\d]*[ \t]+[A-Z][A-Z]{2,}|[A-Z]{4}[A-Z \t]{2,})[ \t]*\n',
        after)
    if not stop:
        stop = re.search(
            r'\n[ \t]*(?:\d+[\.\d]*[ \t]+[A-Z][A-Z]{2,}|[A-Z]{4}[A-Z \t]{2,})[ \t]*\n',
            after)
    body = after[:stop.start()] if stop else after[:10000]
    return _clean_page_artefacts(body).strip()


def _sec(*names, sections):
    return '\n'.join(sections[n] for n in names if sections.get(n))


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tender ID / Reference Number
# ─────────────────────────────────────────────────────────────────────────────

def extract_tender_id(text):
    """
    Patterns observed across all documents:
    - "RFQ REFERENCE NUMBER RFQ 12-07-2026"
    - "RFI NUMBER : RAF/2026/00048"           (multi-line label)
    - "Reference for Quotation No: NRWDI/ICT/2026-12"
    - "Reference nr: SCM8/2026/27"
    - "REFERENCE NUMBER ATNS/RFQ/02/2026/19/"
    - "TENDER NO: SCM8/2026/27"
    - "BID NUMBER: RFQ NO .037/26"
    - "REFERENCE NO: SCMU 05 - 2026 2027"
    - "RFP NUMBER: RFP 26 -27-10 ..."
    - "SAMSA/RFI/004/2026/27"  standalone on cover
    - "BID NUMBER: BS/2026/RFB 568"
    """
    # Normalise common PDF space artefacts before matching
    t = text
    t = re.sub(r'(\d{2,3})\s+(\d{1,2})(?=[/\-])', r'\1\2', t)   # "202 6/" → "2026/", "00 4/" → "004/"
    t = re.sub(r'(\d)\s+-\s*(\d)', r'\1-\2', t)                   # "26 -27" → "26-27"
    t = re.sub(r'(RFQ|RFP|RFI|RFT|ITB)\s+(\d{1,3})\s+-\s*(\d{2}-\d{4})',
               r'\1 \2-\3', t, flags=re.IGNORECASE)

    patterns = [
        # Explicit prefixed labels — most reliable
        r'rfq\s+reference\s+number\s+((?:RFQ|RFP|RFI|RFT|ITB)[\s\-]\S[\S ]{1,35})',
        r'(?:rfi|rfq|rfp|rft|itb)\s+number\s*[:\s]+([\w/\-. ]{3,40})',
        r'reference\s+(?:nr|no|number)\s*[.:\s]+([A-Z0-9][A-Z0-9/\-. ]{2,40})',
        r'tender\s+no\.?\s*[.:\s]+([A-Z0-9][\w/\-. ]{2,35})',
        r'bid\s+(?:number|no)\s*[.:\s]+([A-Z0-9][\w/\-. ]{2,35})',
        r'(?:rfq|rfp|rfi|rft|itb)\s+no\.?\s*[.:\s]*([\w/\-. ]{3,30})',
        r'(?:request\s+for\s+(?:quotation|proposal|tender|information|bid)\s+no\.?'
        r'|ref\.?\s*no\.?)\s*[.:\s]+([A-Z0-9][\w/\-. ]{2,35})',
        # Standalone slash-separated ID on cover: "SAMSA/RFI/004/2026/27"
        r'(?:^|\n)\s*([A-Z]{2,10}/[A-Z]{2,6}/[\w/\-]{4,30})',
        # Bare RFQ/RFP token on cover line
        r'(?:^|\n)\s*((?:RFQ|RFP|RFI|RFT|ITB)[\s\-]\d[\w/\-. ]{2,25})(?:[\s\n]|$)',
    ]

    for p in patterns:
        m = re.search(p, t, re.IGNORECASE | re.MULTILINE)
        if not m:
            continue
        v = _cv(m.group(1)).strip()
        # Post-processing cleanup
        # Stop at CLOSING DATE or similar noise that indicates end of ID field
        v = re.sub(r'\s+CLOSING\s+DATE\b.*$', '', v, flags=re.IGNORECASE).strip()
        v = re.sub(r'\s+CLOSING\s+TIME\b.*$', '', v, flags=re.IGNORECASE).strip()
        v = re.sub(r'(\d{3})\s+(\d{1})\b', r'\1\2', v)           # "202 6" → "2026"
        v = re.sub(r'/\s+[A-Z].*$', '', v).strip()                # trailing "/ WORD"
        v = v.rstrip('/ ')
        v = re.sub(r'\s+[A-Z]{3,}(?:_[A-Z]+)+$', '', v).strip()  # "FACILITIES_ELEC"
        v = re.sub(r'\s+\d+\s*\|.*$', '', v).strip()              # "1 | P a g e"
        v = re.sub(r'(?<=\d{2})\s+\d{1}$', '', v).strip()         # trailing page digit
        v = re.sub(r'(\d{4})\s+(\d{2,4})$', r'\1/\2', v).strip()  # "2026 27" → "2026/27"
        v = re.sub(r'\b(RFQ|RFP|RFI|RFT|ITB)\s+NO\.?\s*', r'\1 ', v, flags=re.IGNORECASE)
        # Strip trailing description words
        v = re.sub(
            r'\s+(?:SUPPLY|DELIVERY|CERTIFICATE|ELECTRICAL|MECHANICAL'
            r'|AND\s+DELIVERY|FOR\s+FAWB|FOR\s+THE)\b.*$',
            '', v, flags=re.IGNORECASE).strip()
        if re.search(r'\d', v) and 3 <= len(v) <= 50:
            return v
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 2. Tender Name / Description
# ─────────────────────────────────────────────────────────────────────────────

def extract_tender_name(text):
    """
    Patterns observed:
    - "DESCRIPTION : REQUEST FOR INFORMATION: CLOUD-HOSTED..."
    - "DESCRIPTION APPOINTMENT OF A SERVICE PROVIDER..."
    - "PROJECT NAME/ DESCRIPTION OF GOODS, WORK OR SERVICES <value on next lines>"
    - "TENDER: RENEWAL, REGISTRATION AND SUPPLY OF..."
    - Title lines near top of document
    """
    lines = text.splitlines()

    # ── 1. Explicit DESCRIPTION label ───────────────────────────────────────
    desc_pat = re.compile(
        r'^(?:DESCRIPTION\s*[:\s]|PROJECT\s+NAME[^\n]*DESCRIPTION[^\n]*$)',
        re.IGNORECASE)
    for i, line in enumerate(lines[:60]):
        if desc_pat.match(line.strip()):
            # Value may be on same line or next non-blank lines
            inline = re.sub(r'^(?:DESCRIPTION|PROJECT\s+NAME[^\n]*)\s*[:\s]*', '', line, flags=re.IGNORECASE).strip()
            if len(inline) >= 20:
                # Collect continuation lines
                result = inline
                for j in range(i + 1, min(i + 5, len(lines))):
                    cont = lines[j].strip()
                    if not cont or re.match(r'^[A-Z\s]{4,}[:\s]', cont):
                        break
                    result += ' ' + cont
                return _cv(result)[:300]
            else:
                # Value on next lines
                result_lines = []
                for j in range(i + 1, min(i + 6, len(lines))):
                    cont = lines[j].strip()
                    if not cont:
                        if result_lines:
                            break
                        continue
                    if re.match(r'^(?:ISSUE\s+DATE|CLOSING|BRIEFING|BID\s+NUMBER|PUBLISH)', cont, re.IGNORECASE):
                        break
                    result_lines.append(cont)
                if result_lines:
                    return _cv(' '.join(result_lines))[:300]

    # ── 2. "TENDER: <title>" ─────────────────────────────────────────────────
    m = re.search(r'^TENDER\s*:\s*(.+)', text, re.IGNORECASE | re.MULTILINE)
    if m:
        # May span multiple lines
        start = m.start(1)
        snippet = text[start:start + 300]
        title_lines = []
        for l in snippet.splitlines():
            s = l.strip()
            if not s or re.match(r'^(?:SCM|BID|CONTACT|CLOSING|REFERENCE)', s, re.IGNORECASE):
                break
            title_lines.append(s)
        if title_lines:
            return _cv(' '.join(title_lines))[:300]

    # ── 3. Keyword lines near top ────────────────────────────────────────────
    kw = re.compile(
        r'^(?:supply\s+(?:and\s+)?(?:delivery|installation)|provision\s+of'
        r'|appointment\s+of|procurement\s+of|request\s+for\s+(?:information|pricing)'
        r'|renewal[,\s])',
        re.IGNORECASE)
    skip = re.compile(
        r'page\s+\d+|p\s+a\s+g\s+e|\brev\b|request\s+for\s+(quotation|proposal)'
        r'|rfq\b|rfp\b|from:|dear\s|^\s*\d+\s*$',
        re.IGNORECASE)
    for line in lines[:50]:
        s = line.strip()
        if re.search(r'[-_]{5,}', s):
            continue
        if kw.match(s) and 15 <= len(s) <= 300:
            return _cv(s)[:300]
        if 25 <= len(s) <= 250 and not skip.search(s):
            caps = sum(1 for w in s.split() if w and w[0].isupper())
            if caps >= 4:
                return _cv(s)[:300]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Closing Date
# ─────────────────────────────────────────────────────────────────────────────

def extract_closing_date(text):
    """
    Patterns observed:
    - "RFQ CLOSING DETAILS Date: 06 August 2026"
    - "RFQ Closing Date: 03 August 2026"
    - "CLOSING DATE : 26 August 2026"
    - "CLOSING DATE AND TIME: 07 AUGUST 2026 AT 11H00"
    - "PUBLISHED DATE: 31 July 2026  CLOSING DATE: 04 September 2026"
    - "CLOSE Date: Thursday 03 September 2026"
    - "BID NUMBER: ... CLOSING DATE: 04 September 2026 CLOSING TIME: 12:00"
    - "Closing Date 24 August 2026"
    - ISO: "CLOSING DATE : 2026/08/28"
    """
    _D = rf'\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}'
    _ISO = r'\d{4}[/\-]\d{1,2}[/\-]\d{1,2}'
    _NUM = r'\d{1,2}[/\-]\d{1,2}[/\-]\d{4}'

    patterns = [
        # Most specific — doc-type labelled closing dates (highest priority)
        rf'(?:rfq|rfp|rfi|rft|bid|tender)\s+closing\s+date\s+and\s+time\s*[:\s]+({_D})',
        rf'(?:rfq|rfp|rfi|rft|bid|tender)\s+closing\s+date\s+and\s+time\s*[:\s]+({_ISO})',
        rf'(?:rfq|rfp|rfi|rft|bid|tender)\s*closing\s+date\s*[:\s]+({_D})',
        rf'(?:rfq|rfp|rfi|rft|bid|tender)\s*closing\s+date\s*[:\s]+({_ISO})',
        # "RFQ CLOSING DETAILS Date: 06 August 2026"
        rf'closing\s+details\s+date[:\s]+({_D})',
        rf'closing\s+details\s+date[:\s]+({_ISO})',
        # "CLOSING DATE AND TIME: 07 AUGUST 2026 AT 11H00"
        rf'closing\s+date\s+and\s+time\s*[:\s]+({_D})',
        rf'closing\s+date\s+and\s+time\s*[:\s]+(\d{{1,2}}\s+\w+\s+\d{{4}})',
        # "CLOSE Date: Thursday 03 September 2026"
        rf'close\s+date\s*[:\s]+(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w*\s+)?({_D})',
        # "PUBLISHED DATE: ... CLOSING DATE: ..." — capture the CLOSING part only
        rf'CLOSING\s+DATE\s*[:\s]*({_D})',
        rf'CLOSING\s+DATE\s*[:\s]*({_ISO})',
        rf'CLOSING\s+DATE\s*[:\s]*({_NUM})',
        # "Due Date / Deadline"
        rf'(?:due\s+date|deadline)\s*[:\s]+({_D})',
        # Contextual fallback — bare date near closing keyword
        rf'(?:close|closing|submission|deadline)[^\n]{{0,60}}\b({_D})\b',
    ]

    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = _cv(m.group(1))[:60]
            # Strip appended time info
            v = re.sub(r'\s+(?:at|AT)\s+\d[\d:hH]+.*$', '', v).strip()
            v = re.sub(r'\s+\d{1,2}[hH]\d{0,2}.*$', '', v).strip()
            v = re.sub(r'(\b\d{4}\b)\s+\D.*$', r'\1', v).strip()
            if v and re.search(r'\d{4}', v):
                return v
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Briefing Session
# ─────────────────────────────────────────────────────────────────────────────

def extract_briefing_session(text):
    """
    Extract compulsory/non-compulsory briefing session details.

    Patterns:
    - "BRIEFING SESSION DETAILS  Compulsory ... N/A  Non-compulsory ... N/A"
    - "COMPULSORY BRIEFING SESSION /SITE VISIT  Venue: ...  Date: 30 July 2026  Time: 10h00"
    - "COMPULSORY BRIEFING SESSION  N/A"  /  "COMPULSORY BRIEFING SESSION N/A"
    - Two sites: ATNS has two COMPULSORY BRIEFING SESSION blocks
    """
    lines = text.splitlines()

    # Find first briefing session mention in first 100 lines
    # Join adjacent short lines first to handle "COMPULSORY BRIEFING\nSESSION /SITE VISIT"
    joined_lines = []
    i = 0
    while i < min(len(lines), 100):
        s = lines[i].strip()
        # If line ends with BRIEFING, peek at next line for SESSION
        if re.search(r'\bBRIEFING\s*$', s, re.IGNORECASE) and i + 1 < len(lines):
            s = s + ' ' + lines[i + 1].strip()
            i += 2
        else:
            i += 1
        joined_lines.append(s)

    briefing_idx = None
    for i, line in enumerate(joined_lines):
        if re.search(r'briefing\s+session', line, re.IGNORECASE):
            briefing_idx = i
            break

    if briefing_idx is None:
        return None

    # Collect the block until a stopping keyword (from original lines)
    # Map back to original line index (approximate: briefing_idx maps to ~briefing_idx)
    orig_start = min(briefing_idx, len(lines) - 1)
    block_lines = []
    for line in lines[orig_start:orig_start + 40]:
        s = line.strip()
        if re.match(r'^(?:CLOSING\s+DATE|CLOSING\s+TIME|BID\s+SUBMISSION|VALIDITY|TABLE\s+OF)', s, re.IGNORECASE):
            break
        block_lines.append(s)

    block = '\n'.join(block_lines)
    compulsory = bool(re.search(r'compulsory', block, re.IGNORECASE))

    # N/A — no briefing
    if re.search(r'N/A', block) and not re.search(r'(?:Date|Venue)\s*:', block, re.IGNORECASE):
        if compulsory:
            return 'No compulsory briefing session'
        return 'No briefing session required'

    # Parse venue/date/time blocks (may be multiple sites)
    sessions = []
    current = {}
    for s in block_lines:
        if not s:
            continue
        vm = re.match(r'(?:venue\s+for\s+the\s+site\s+visit|venue)\s*:\s*(.+)', s, re.IGNORECASE)
        dm = re.match(r'Date\s*:\s*(.+)', s, re.IGNORECASE)
        tm = re.match(r'Time\s*:\s*(.+)', s, re.IGNORECASE)
        if vm:
            if current.get('venue') or current.get('date'):
                sessions.append(current)
                current = {}
            current['venue'] = vm.group(1).strip()
        elif dm:
            current['date'] = dm.group(1).strip()
        elif tm:
            current['time'] = tm.group(1).strip()
        elif current.get('venue') and not current.get('date') and len(s) < 60:
            current['venue'] += ', ' + s  # address continuation
    if current.get('venue') or current.get('date'):
        sessions.append(current)

    if not sessions:
        if compulsory:
            return 'Compulsory briefing session (see document for details)'
        return None

    prefix = 'Compulsory' if compulsory else 'Briefing'
    parts = []
    for sess in sessions:
        seg = []
        if sess.get('venue'):
            seg.append(f"Venue: {sess['venue']}")
        if sess.get('date'):
            seg.append(f"Date: {sess['date']}")
        if sess.get('time'):
            seg.append(f"Time: {sess['time']}")
        if seg:
            parts.append(' | '.join(seg))

    if not parts:
        return None
    if len(parts) == 1:
        return f"{prefix} | {parts[0]}"
    return f"{prefix} | " + ' || '.join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Scope of Work
# ─────────────────────────────────────────────────────────────────────────────

def _clean_scope_body(body):
    body = _clean_page_artefacts(body)
    lines = body.splitlines()
    cleaned, prev_blank = [], False
    for line in lines:
        is_blank = not line.strip()
        if is_blank and prev_blank:
            continue
        cleaned.append(line.rstrip())
        prev_blank = is_blank
    return '\n'.join(cleaned).strip()


def extract_scope_of_work(sections):
    """
    Patterns observed across all documents:
    - "2. SCOPE OF WORK" heading then body
    - "TERMS OF REFERENCE/ SCOPE OF WORKS"
    - "SECTION A: INTRODUCTION AND SCOPE OF WORK" then "3. Scope of work"
    - "1 TERMS OF REFERENCE/SPECIFICATIONS" (037-26)
    - "6. SCOPE OF WORK" (RFI doc)
    - "5. Specification (please attach the specification here" (C-BRTA)
    - "SCOPE OF SUPPLY AND SPECIFIC INSTRUCTIONS" (RFP cartridges)
    - Background/purpose section (SAMSA, Cabling)
    """
    sections = _coerce_sections(sections)
    full = sections.get('full', '')

    def _is_junk(text):
        return bool(_GC_JUNK.search(text))

    def _is_toc(after):
        sample = [l.strip() for l in after[:600].splitlines() if l.strip()][:12]
        if not sample:
            return False
        toc = sum(1 for l in sample if (
            re.search(r'\d+\s*[-–]\s*\d+\s*$|\b\d{1,3}\s*$', l) or
            re.search(r'Compulsory\s+Returnable|CAMBD\s+\d|Yes\s+No\s*$', l, re.IGNORECASE)
        ))
        return toc / len(sample) >= 0.4

    # ── Heading patterns to search for in full text ──────────────────────────
    _SCOPE_HEADINGS = re.compile(
        r'(?:^|\n)[ \t]*(?:\d+[\.\d]*[ \t]+)?'
        r'(?:SCOPE\s+OF\s+WORK(?:S|/SUPPLY)?'
        r'|TERMS\s+OF\s+REFERENCE(?:\s*/\s*SCOPE\s+OF\s+WORKS?|/SPECIFICATIONS?)?'
        r'|SPECIFICATION(?:S)?\s*(?:\([^\n]{0,60})?'
        r'|SCOPE\s+OF\s+SUPPLY'
        r'|INTRODUCTION\s+AND\s+SCOPE)'
        r'[^\n]*\n',
        re.IGNORECASE)

    _NEXT_SECTION = re.compile(
        r'\n[ \t]*\n[ \t]*(?:\d+[\.\d]*[ \t]+[A-Z][A-Z]{2,}|[A-Z]{4}[A-Z \t]{2,})[ \t]*\n'
        r'|\n[ \t]*(?:\d+[\.\d]*[ \t]+[A-Z][A-Z]{2,}|[A-Z]{5}[A-Z \t]{2,})[ \t]*\n'
    )

    pos = 0
    while True:
        m = _SCOPE_HEADINGS.search(full, pos)
        if not m:
            break

        after = full[m.end():]

        # Reject form-section markers
        first = re.search(r'\S', after)
        if first:
            snippet = after[first.start():first.start() + 80]
            if re.match(r'(?:PART\s+[A-Z]|BID\s+NUMBER|INVITATION\s+TO\s+BID|YOU\s+ARE\s+HEREBY)', snippet, re.IGNORECASE):
                pos = m.end()
                continue

        # Reject ToC
        if _is_toc(after):
            pos = m.end()
            continue

        stop = _NEXT_SECTION.search(after)
        body = after[:stop.start()] if stop else after[:15000]
        body = _clean_scope_body(body)

        if not _is_junk(body) and len(body) >= 50:
            return body

        pos = m.end()

    # ── Fallback: terms of reference section ────────────────────────────────
    tor_body = _section_body(full,
        r'(?:\d+[\.\d]*[ \t]+)?TERMS\s+OF\s+REFERENCE(?:\s*/\s*SCOPE\s+OF\s+WORKS?|/SPECIFICATIONS?)?',
        r'(?:\d+[\.\d]*[ \t]+)?TERMS\s+OF\s+REFERENCE(?:\s*[:\n]|$)'
    )
    if tor_body and not _is_junk(tor_body) and len(tor_body.strip()) >= 50:
        return _clean_scope_body(tor_body)

    # ── Fallback: background / purpose section ───────────────────────────────
    for key in ('background', 'purpose'):
        body = sections.get(key, '')
        if body and not _is_junk(body) and len(body.strip()) >= 50:
            return _clean_scope_body(body)

    # ── Last resort: extract from first meaningful paragraph in full text ────
    # For short documents (RFIs, RFPs) where the scope is described in the intro
    full_clean = _clean_page_artefacts(full)
    # Find first paragraph of 3+ sentences that describes what's needed
    paras = re.split(r'\n{2,}', full_clean)
    for para in paras[1:15]:   # skip cover page header
        p = para.strip()
        if len(p) < 80 or _is_junk(p):
            continue
        # Must look like a description (contains verbs and enough words)
        if re.search(r'\b(?:seeks?\s+to|wishes?\s+to|requires?\s+to|appoint|supply|deliver|host|provide|install)\b', p, re.IGNORECASE):
            return _clean_scope_body(p)

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 6. Mandatory / Evaluation Criteria
# ─────────────────────────────────────────────────────────────────────────────

def extract_evaluation_criteria(sections):
    sections = _coerce_sections(sections)
    full = sections.get('full', '')

    # Find the evaluation section in full text
    body = _section_body(full,
        r'(?:\d+[\.\d]*\s+)?(?:EVALUATION\s+CRITERIA|BID\s+EVALUATION|STAGE\s+\d|EVALUATION\s+PROCESS)',
        r'(?:\d+[\.\d]*\s+)?MANDATORY\s+REQUIREMENTS?')

    if not body:
        body = sections.get('evaluation', '')

    if not body:
        return []

    items = re.findall(
        r'(?:^|\n)\s*(?:[ivxIVX]{1,5}[.)]\s+|[a-zA-Z][.)]\s+|\d+[.)]\s+|[-•*]\s+)(.{10,250})',
        body, re.MULTILINE)

    junk = re.compile(
        r'preference\s+point|b-?bbee\s+certificate|80/20|90/10'
        r'|closing\s+date|email\s+address|business\s+day',
        re.IGNORECASE)

    result = [_cv(i) for i in items if len(_cv(i)) > 10 and not junk.search(i)]
    seen, unique = set(), []
    for r in result:
        if r.lower() not in seen:
            seen.add(r.lower())
            unique.append(r)
    return unique[:15]


def extract_mandatory_criteria(sections):
    """
    Extract mandatory / compulsory gatekeeping requirements.
    Patterns:
    - "Phase 1: Mandatory Requirements (At Closing Stage)"
    - "Stage 2: Mandatory Requirements" with table
    - "1. Mandatory Requirement (At RFQ Closing Date) i. ..."
    - "Mandatory Requirements Description ..."
    - "5.1.1. Step 1: Mandatory compliance"
    """
    sections = _coerce_sections(sections)
    full = sections.get('full', '')

    body = _section_body(full,
        r'(?:Phase\s+1|Stage\s+[12])\s*:\s*Mandatory\s+Requirements?',
        r'(?:\d+[\.\d]*\s+)?Mandatory\s+Requirement(?:s)?\s*(?:\([^)]{0,40}\))?',
        r'Step\s+\d+\s*:\s*Mandatory\s+(?:compliance|requirements?)')

    if not body:
        body = sections.get('compulsory', '')

    if not body:
        # Search full text
        m = re.search(r'mandatory\s+requirement|compulsory\s+(?:returnable|document|criteria)', full, re.IGNORECASE)
        if m:
            start = full.find('\n', m.end())
            body = full[start:start + 3000] if start != -1 else ''

    if not body:
        return []

    items = re.findall(
        r'(?:^|\n)\s*(?:[ivxIVX]{1,5}[.)]\s+|[a-zA-Z][.)]\s+|\d+[.)]\s+|[-•*?]\s*)(.{10,300})',
        body, re.MULTILINE)

    junk = re.compile(
        r'preference\s+point|b-?bbee|80/20|90/10|business\s+day'
        r'|vat\s+inclusive|means\s+(?:a|an|the)\b',
        re.IGNORECASE)

    result = [_cv(i) for i in items if len(_cv(i)) > 10 and not junk.search(i)]
    seen, unique = set(), []
    for r in result:
        if r.lower() not in seen:
            seen.add(r.lower())
            unique.append(r)
    return unique[:15]


# ─────────────────────────────────────────────────────────────────────────────
# 7. Organisation / Issuing Entity
# ─────────────────────────────────────────────────────────────────────────────

def extract_organization(text):
    """
    Patterns observed:
    - "From: The National Radioactive Waste Disposal Institute"
    - "AIR TRAFFIC AND NAVIGATION SERVICES SOC LTD" (cover heading)
    - "Cape Agulhas Municipality" (in TOR section)
    - "ECRDA" header / "Banking Sector Education and Training Authority (BANKSETA)"
    - "CROSS-BORDER ROAD TRANSPORT AGENCY"
    - "South African Post Office Limited"
    - "THE SOUTH AFRICAN MARITIME SAFETY AUTHORITY (SAMSA)" in title line
    - "ROAD ACCIDENT FUND (RAF)"
    """
    lines = text.splitlines()

    # ── 1. Explicit "From:" label ────────────────────────────────────────────
    m = re.search(r'^From\s*:\s*(.{5,150})', text, re.IGNORECASE | re.MULTILINE)
    if m:
        v = _cv(m.group(1)).strip().rstrip('.')
        if 5 <= len(v) <= 200 and not _GC_JUNK.search(v):
            return v

    # ── 2. "Requirements of THE <Org>" ──────────────────────────────────────
    m = re.search(r'requirements\s+of\s+the\s+([A-Z][A-Za-z\s\-&]{5,80}?)(?:\s*\n|\s{3,})', text, re.IGNORECASE)
    if m:
        v = _cv(m.group(1)).strip().rstrip('.,')
        if 5 <= len(v) <= 150 and not _GC_JUNK.search(v):
            return v

    # ── 3. Org name in parentheses acronym form: "THE SOUTH AFRICAN MARITIME SAFETY AUTHORITY (SAMSA)"
    m = re.search(r'(?:THE\s+)?([A-Z][A-Z\s\-&]{5,80}?)\s*\(([A-Z]{2,8})\)', text)
    if m:
        full_name = _cv(m.group(1)).strip()
        acronym = m.group(2)
        # Must look like an org name (has typical org words or is near top)
        if (re.search(r'\b(?:authority|agency|fund|institute|board|municipality|department|seta|council|company|corporation|limited)\b', full_name, re.IGNORECASE)
                and len(full_name) >= 10):
            return f"{full_name} ({acronym})"

    # ── 4. "invited to submit proposal to the <Org>" ────────────────────────
    m = re.search(r'(?:invited\s+to\s+(?:submit|bid)\s+(?:proposal|quotation)\s+to\s+the\s+)([A-Z][A-Za-z\s\-&]{5,80})', text, re.IGNORECASE)
    if m:
        v = _cv(m.group(1)).strip()
        # Stop at prepositions that indicate the org name has ended
        v = re.sub(r'\s+(?:for\s+the|to\s+supply|limited\s+for\b|soc\s+ltd\s+for\b).*$', '', v, flags=re.IGNORECASE).strip()
        v = v.rstrip('.,')
        if 5 <= len(v) <= 150 and not _GC_JUNK.search(v):
            return v

    # ── 5. Cover-page org name — prominent lines near top ────────────────────
    skip = re.compile(
        r'^(?:page\s+\d+|p\s+a\s+g\s+e|request\s+for|rfq|rfp|rfi|rft'
        r'|invitation\s+to\s+bid|republic\s+of\s+south\s+africa'
        r'|confidential|fraud\s+hotline|\d+\s*\||\d+\s*$'
        r'|appointment\s+of|supply\s+and|provision\s+of)',
        re.IGNORECASE)
    org_kw = re.compile(
        r'\b(?:agency|authority|municipality|institute|university|college'
        r'|department|ministry|fund|seta|council|board|commission'
        r'|corporation|limited|soc\s+ltd|soc\.?\s*ltd\.?|pty\s+ltd|npc)\b',
        re.IGNORECASE)
    for line in lines[:25]:
        s = line.strip()
        if len(s) < 8 or skip.search(s):
            continue
        if org_kw.search(s) and len(s) <= 150:
            return _cv(s)

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 8. Contact Information
# ─────────────────────────────────────────────────────────────────────────────

def extract_contact_info(text):
    """
    Returns (contacts_list, primary_email, primary_phone).
    contacts_list: [{name, role, email, phone}, ...]

    Patterns observed:
    - "CONTACT PERSON Thobela Mqikela  CONTACT PERSON Siyabonga Mfeka" (side-by-side)
    - "Contact Person: Mr Kevin Fourie  Contact Person: Ms. G Koopman"
    - "ENQUIRIES:\n  PROCUREMENT SPECIALIST Martin Lekhuleni\n  Tel: 012-845-2667"
    - "Bright Blessie : BrightB@atns.co.za"
    - "RESPONSES TO BE SUBMITTED TO:\n Zanele Sibiya\n 012 366 2600\n zasibiya@samsa.org.za"
    - "Administrative Enquiries should be directed to Mr A Langa - Telephone: 043 703 6300"
    - "Contact person : <blank form field>" (ignore)
    - "Enquiries regarding this ... submitted via e-mail to: bacsecretariat@raf.co.za"
    """
    contacts = []
    lines = text.splitlines()
    n = len(lines)

    _FORM_LABEL = re.compile(
        r'^(?:contact\s+(?:person|name|number|details)|designation|telephone(?:\s+number)?'
        r'|facsimile(?:\s+number)?|e-?mail(?:\s+address)?|cellphone(?:\s+number)?'
        r'|mobile(?:\s+number)?|fax(?:\s+number)?|phone\s+no\.?'
        r'|name|title|position|role|dept|department)\s*[:\s]*$',
        re.IGNORECASE)

    def _is_real_name(s):
        if not s or len(s) < 3:
            return False
        if _FORM_LABEL.match(s):
            return False
        if re.match(r'^\d+[\.\d]*\s+', s):        # section number
            return False
        if re.match(r'^[A-Z\s]{10,}$', s):         # all caps label
            return False
        if re.search(r'_{4,}', s):                  # underscores (blank form line)
            return False
        if len(s) > 80:                             # too long to be a name
            return False
        if re.search(
            r'(?:ANNEXURE|SECTION|SCHEDULE|APPENDIX|TABLE|DEPARTMENT|SPECIFICATION'
            r'|SBD\s+\d|CAMBD\s+\d|documents\s+by|submitted\s+via|should\s+be'
            r'|regarding\s+this|PROCUREMENT\s+PROCEDURE|INFORMATION\s+MAY\s+BE)',
            s, re.IGNORECASE):
            return False
        return True

    def _find_phone(text_snippet):
        pm = re.search(r'(?:tel(?:ephone)?|cell|phone|mobile)?\s*[.:\s]*((?:\+27|0)[\d\s\-]{8,12})', text_snippet, re.IGNORECASE)
        return _cv(pm.group(1)) if pm else None

    def _find_email(text_snippet):
        em = re.search(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', text_snippet)
        return em.group(0) if em else None

    # ── P1: Side-by-side "CONTACT PERSON Name1  CONTACT PERSON Name2" ───────
    cp_dual = re.compile(r'CONTACT\s+PERSON\s+(.+?)\s{2,}CONTACT\s+PERSON\s+(.+)', re.IGNORECASE)
    for i, line in enumerate(lines):
        m = cp_dual.match(line.strip())
        if not m:
            continue
        names = [m.group(1).strip(), m.group(2).strip()]
        details = [{'name': name, 'role': 'Contact Person', 'email': None, 'phone': None}
                   for name in names if _is_real_name(name)]
        ci = 0
        for j in range(i + 1, min(i + 12, n)):
            dl = lines[j].strip()
            if not dl:
                continue
            if re.match(r'^(?:PART\s+[A-Z]|\d+\.\s+[A-Z]{3}|BID\s+NUMBER)', dl):
                break
            ph = _find_phone(dl)
            em = _find_email(dl)
            if (ph or em) and ci < len(details):
                if ph and not details[ci]['phone']:
                    details[ci]['phone'] = ph
                if em and not details[ci]['email']:
                    details[ci]['email'] = em
                ci += 1
        contacts.extend(details)

    # ── P2: "Contact Person: Name  Contact Person: Name" (colon form) ────────
    cp_colon_dual = re.compile(
        r'Contact\s+Person\s*:\s*([A-Z][a-zA-Z.\s]{2,40}?)\s{2,}Contact\s+Person\s*:\s*([A-Z][a-zA-Z.\s]{2,40})',
        re.IGNORECASE)
    for line in lines:
        m = cp_colon_dual.match(line.strip())
        if not m:
            continue
        for name in [m.group(1).strip(), m.group(2).strip()]:
            if _is_real_name(name):
                contacts.append({'name': name, 'role': 'Contact Person', 'email': None, 'phone': None})

    # ── P3: Single "CONTACT PERSON\nName" ────────────────────────────────────
    cp_single = re.compile(r'^CONTACT\s+PERSON\s*$', re.IGNORECASE)
    for i, line in enumerate(lines):
        if not cp_single.match(line.strip()):
            continue
        for j in range(i + 1, min(i + 3, n)):
            name = lines[j].strip()
            if not name or not _is_real_name(name):
                continue
            c = {'name': name, 'role': 'Contact Person', 'email': None, 'phone': None}
            for k in range(j + 1, min(j + 5, n)):
                dl = lines[k].strip()
                if not c['email']:
                    c['email'] = _find_email(dl)
                if not c['phone']:
                    c['phone'] = _find_phone(dl)
            contacts.append(c)
            break

    # ── P4: "Name : email" inline (ATNS style) ───────────────────────────────
    name_email = re.compile(
        r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,})\s*:\s*([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})')
    for m in name_email.finditer(text):
        name = m.group(1).strip()
        email = m.group(2)
        if re.search(r'quotation|email|address|procurement|submit|document', name, re.IGNORECASE):
            continue
        if not any(x['email'] == email for x in contacts):
            contacts.append({'name': name, 'role': 'Contact Person', 'email': email, 'phone': None})

    # ── P5: Enquiry blocks ────────────────────────────────────────────────────
    enq_pat = re.compile(
        r'(?:ENQUIRIES?\s*[:\n]|BIDDING\s+PROCEDURE\s+ENQUIRIES?[^\n]*\n'
        r'|TECHNICAL\s+(?:ENQUIRIES?|INFORMATION)[^\n]*\n)',
        re.IGNORECASE)
    for m in enq_pat.finditer(text):
        block = text[m.end():m.end() + 300]
        block_lines = [l.strip() for l in block.splitlines() if l.strip()][:6]
        c = {'name': None, 'role': 'Enquiries', 'email': None, 'phone': None}
        for bl in block_lines:
            em = _find_email(bl)
            ph = _find_phone(bl)
            if em:
                c['email'] = em
            if ph and not c['phone']:
                c['phone'] = ph
            # Only use as name if it looks like a proper person name (2-4 title-case words)
            if (not c['name'] and not em and not ph and _is_real_name(bl)
                    and re.match(r'^(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+$', bl)):
                c['name'] = bl
        if (c['email'] or c['phone']) and not any(x['email'] == c['email'] and c['email'] for x in contacts):
            contacts.append(c)

    # ── P6: Inline "directed to NAME - Tel: PHONE" ───────────────────────────
    inline_pat = re.compile(
        r'(?:enquiries?\s+(?:should\s+be\s+)?directed\s+(?:to\s+)?(?:Mr\.?|Ms\.?|Mrs\.?)?\s*)'
        r'([A-Z][a-zA-Z\s.]{2,40})',
        re.IGNORECASE)
    for m in inline_pat.finditer(text):
        name = m.group(1).strip().rstrip('-–, ')
        if not _is_real_name(name):
            continue
        snippet = text[m.start():m.start() + 250]
        c = {
            'name': name,
            'role': 'Enquiries',
            'email': _find_email(snippet),
            'phone': _find_phone(snippet)
        }
        if not any(x['name'] == name for x in contacts):
            contacts.append(c)

    # ── P7: "RESPONSES TO BE SUBMITTED TO:" block ────────────────────────────
    submit_pat = re.compile(r'responses?\s+(?:must\s+be\s+)?(?:to\s+be\s+)?submitted\s+to\s*:\s*\n', re.IGNORECASE)
    for m in submit_pat.finditer(text):
        block_lines = [l.strip() for l in text[m.end():m.end() + 200].splitlines() if l.strip()][:5]
        c = {'name': None, 'role': 'Submission Contact', 'email': None, 'phone': None}
        for bl in block_lines:
            em = _find_email(bl)
            ph = _find_phone(bl)
            if em:
                c['email'] = em
            if ph and not c['phone']:
                c['phone'] = ph
            if not c['name'] and not em and not ph and _is_real_name(bl):
                c['name'] = bl
        if (c['name'] or c['email']) and not any(x['email'] == c['email'] and c['email'] for x in contacts):
            contacts.append(c)

    # ── Deduplicate ──────────────────────────────────────────────────────────
    seen_keys, unique = set(), []
    for c in contacts:
        key = (c.get('email') or c.get('name') or '').lower()
        if key and key not in seen_keys:
            seen_keys.add(key)
            unique.append(c)
    contacts = unique

    # ── Primary email / phone ────────────────────────────────────────────────
    priority_kw = ('procurement', 'tender', 'tenders', 'bid', 'bids', 'supply', 'admin', 'info', 'secretariat')
    all_emails = re.findall(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', text)
    primary_email = next(
        (e for e in all_emails if any(k in e.lower() for k in priority_kw)),
        all_emails[0] if all_emails else None)
    pm = re.search(
        r'(?:\+27|0)[\s\-]?(?:\d[\s\-]?){8,9}\d'
        r'|(?:\+\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
        text)
    primary_phone = _cv(pm.group(0)) if pm else None

    return contacts, primary_email, primary_phone


# ─────────────────────────────────────────────────────────────────────────────
# 9. Submission Details
# ─────────────────────────────────────────────────────────────────────────────

def extract_submission_details(sections):
    """
    Patterns observed:
    - "RFQ must be submitted to Email: Quotation1@cbrta.co.za"
    - "RESPONSES MUST BE EMAILED TO: bacsecretariat@raf.co.za  ATTENTION: Demand Management"
    - "PROPOSAL TO BE HAND DELIVERED  SAPO Supply Chain Management  Cnr James Drive..."
    - "BID SUBMISSION - ONLINE  All bid submissions must be made via the e-Submission (e-Tender)"
    - "completed bid document must be submitted via email only to tenders@ecrda.co.za"
    - "Tender Documents must be deposited in the Tender Box, at Municipal Offices, 1 Dirkie Uys..."
    - "Email the quotation to: procurement@nrwdi.org.za"
    - "Submissions must be inserted into the SUBMISSION BOX available at..."
    - "RESPONSES TO BE SUBMITTED TO:\nZanele Sibiya\n012 366 2600\nzasibiya@samsa.org.za"
    """
    sections = _coerce_sections(sections)
    full = sections.get('full', '')

    junk = re.compile(r'preference\s+point|b-?bbee|earn\s+point|in\s+order\s+to', re.IGNORECASE)

    def _multiline_block(source, trigger_re):
        m = re.search(trigger_re, source, re.IGNORECASE)
        if not m:
            return None
        after = source[m.end():]
        parts = []
        for line in after.splitlines():
            s = line.strip()
            if not s:
                if parts:
                    break
                continue
            if junk.search(s):
                break
            parts.append(s)
            if len(parts) >= 6:
                break
        if parts:
            r = ', '.join(parts)
            return re.sub(r',\s*,', ',', r).strip(', ')[:400]
        return None

    # ── 1. e-Submission / e-Tender system ───────────────────────────────────
    m = re.search(r'(?:bid\s+submissions?\s+must\s+be\s+made\s+via|all\s+bid\s+submissions?\s+must\s+be\s+(?:made|sent)\s+(?:via|through))\s+(?:the\s+)?([^\n]{5,200})', full, re.IGNORECASE)
    if m:
        v = _cv(m.group(1))
        if not junk.search(v):
            return v[:300]

    # ── 2. "RESPONSES MUST BE EMAILED TO:" ──────────────────────────────────
    m = re.search(r'responses?\s+must\s+be\s+emailed?\s+to\s*[:\s]+([^\n]{5,200})', full, re.IGNORECASE)
    if m:
        v = _cv(m.group(1))
        # Collect ATTENTION line
        tail = full[m.end():]
        att = re.search(r'ATTENTION\s*:\s*([^\n]{3,80})', tail[:200], re.IGNORECASE)
        if att:
            v += ' | Attention: ' + _cv(att.group(1))
        return v[:300]

    # ── 3. "RESPONSES TO BE SUBMITTED TO:" multi-line block ─────────────────
    r = _multiline_block(full, r'responses?\s+(?:must\s+be\s+)?(?:to\s+be\s+)?submitted\s+to\s*:')
    if r:
        return r

    # ── 4. "PROPOSAL TO BE HAND DELIVERED" block ────────────────────────────
    r = _multiline_block(full, r'proposal\s+to\s+be\s+hand\s+delivered\s*[:\n]')
    if r:
        return r

    # ── 5. "Tender documents must be deposited in the Tender Box at ..." ────
    m = re.search(r'tender\s+documents?\s+must\s+be\s+deposited[^\n]{5,200}', full, re.IGNORECASE)
    if m:
        return _cv(m.group(0))[:300]

    # ── 6. Inline email submission patterns ─────────────────────────────────
    inline = [
        r'rfq\s+must\s+be\s+submitted\s+to\s+email\s*[:\s]+([^\n]{5,200})',
        r'(?:bid|quotation|document)\s+must\s+be\s+submitted\s+via\s+email\s+(?:only\s+)?to\s+([^\n]{5,200})',
        r'submitted?\s+via\s+email\s+(?:only\s+)?to\s*[:\s]*([^\n]{5,200})',
        r'(?:email\s+the\s+quotation\s+to|quotes?\s+must\s+be\s+emailed?\s+to'
        r'|quotation\s+(?:must\s+be\s+)?submitted?\s+to)\s*[:\s]+([^\n]{5,200})',
        r'submissions?\s+(?:must\s+be\s+)?inserted\s+into\s+the\s+submission\s+box[^\n]{5,200}',
        r'[Ee]-?mail\s+to\s*[:\s]+([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})',
        r'directed\s+to\s+([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})',
    ]
    for p in inline:
        m = re.search(p, full, re.IGNORECASE)
        if m:
            v = _cv(m.group(1) if m.lastindex else m.group(0))[:300]
            if len(v) > 5 and not junk.search(v):
                return v

    return None


# ─────────────────────────────────────────────────────────────────────────────
# 10. Address / Delivery Location
# ─────────────────────────────────────────────────────────────────────────────

def extract_address(text):
    junk = re.compile(
        r'postal\s+address|p\.?\s*o\.?\s*box|telephone|cellphone|facsimile'
        r'|e-?mail\s+address|supplier\s+information|name\s+of\s+bidder',
        re.IGNORECASE)

    block_triggers = re.compile(
        r'(?:destination|delivery\s+address|delivery\s+details?|site\s+address|physical\s+address)\s*[:\n]',
        re.IGNORECASE)

    m = block_triggers.search(text)
    if m:
        after = text[m.end():]
        address_lines = []
        for line in after.splitlines():
            stripped = line.strip()
            if not stripped:
                if address_lines:
                    break
                continue
            if re.match(r'^[A-Z][A-Za-z ]{2,30}:\s*\S', stripped):
                break
            if junk.search(stripped):
                break
            if len(stripped) >= 3:
                address_lines.append(stripped)
            if len(address_lines) >= 6:
                break
        if address_lines:
            result = ', '.join(address_lines)
            result = re.sub(r',\s*,', ',', result).strip(', ')
            if len(result) >= 5 and not junk.search(result):
                return result[:300]

    single = [
        r'delivery\s+(?:details?|location)\s*[:\s]+([^\n]{5,150})',
        r'site\s+(?:address|location)\s*[:\s]+([^\n]{5,100})',
        r'physical\s+address\s*[:\s]+([^\n]{5,150})',
        r'\b([A-Z][a-zA-Z ]{2,}(?:,\s*)?(?:KwaZulu|Northern\s+Cape|Western\s+Cape'
        r'|Eastern\s+Cape|Gauteng|Limpopo|Mpumalanga|Free\s+State|North\s+West)[^\n]{0,80})\b',
    ]
    for p in single:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = _cv(m.group(1))
            if len(v) >= 5 and not junk.search(v):
                return v[:200]
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 11. Duration / Validity
# ─────────────────────────────────────────────────────────────────────────────

def extract_duration(sections):
    sections = _coerce_sections(sections)
    full = sections.get('full', '')

    junk = re.compile(
        r'prevention\s+and\s+combating|shall\s+not\s+relieve'
        r'|not\s+exceeding\s+ten\s+years|period\s+not\s+exceeding\s+10\s+years',
        re.IGNORECASE)

    patterns = [
        r'(?:quotation|bid)\s+validity\s+period\s*[:\s]+([^\n]{3,80})',
        r'validity\s+period\s+of\s+bids?\s*[:\s]+([^\n]{3,80})',
        r'(?:contract\s+period|period\s+of\s+(?:contract|performance|validity|service)'
        r'|project\s+(?:duration|timeline)|duration\s+of\s+(?:contract|service))\s*[:\s]+([^\n]{3,80})',
        r'for\s+a\s+period\s+of\s+((?:thirty|thirty-six|twenty-four|twelve|six|three|\d+)'
        r'(?:\s*\(\d+\))?\s+months?(?:[^\n]{0,40})?)',
        r'\b(\d+\s+(?:working\s+)?(?:months?|years?|weeks?|days?)'
        r'(?:\s+(?:from|after|of)\s+[^\n]{0,30})?)\b',
    ]
    for p in patterns:
        m = re.search(p, full, re.IGNORECASE)
        if m:
            v = _cv(m.group(1))[:120]
            if not junk.search(v) and len(v.split()) <= 25:
                return v
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 12. Budget
# ─────────────────────────────────────────────────────────────────────────────

def extract_budget(text):
    currency = 'ZAR'
    amount = None
    m = re.search(
        r'(?:estimated\s+budget|budget\s+amount|contract\s+value|total\s+value)\s*[:\s]+'
        r'([A-Za-z]{0,3}\s*\d[\d,\.]{1,15})',
        text, re.IGNORECASE)
    if m:
        raw = _cv(m.group(1))
        cc = re.match(r'([A-Za-z]{3})', raw)
        if cc:
            currency = cc.group(1).upper()
            raw = raw[cc.end():].strip()
        amount = raw.replace(',', '').strip()
    return {'amount': amount, 'currency': currency}


# ─────────────────────────────────────────────────────────────────────────────
# 13. Compulsory documents / Deliverables / Pricing (unchanged helpers)
# ─────────────────────────────────────────────────────────────────────────────

def _split_inline_items(value):
    if not value:
        return []
    parts = re.split(r'\s*(?:,|;|/|\band\b)\s*', value, flags=re.IGNORECASE)
    return [p.strip(' ,;') for p in parts if p.strip(' ,;') and p.strip().lower() != 'and']


def extract_compulsory_documents(sections):
    sections = _coerce_sections(sections)
    full = sections.get('full', '')
    body = sections.get('compulsory', '')

    if not body:
        m = re.search(r'(?:mandatory\s+requirement|compulsory\s+(?:returnable|document))', full, re.IGNORECASE)
        if m:
            start = full.find('\n', m.end())
            body = full[start:start + 3000] if start != -1 else ''

    if not body:
        return []

    items = re.findall(
        r'(?:^|\n)\s*(?:[ivxIVX]{1,5}[.)]\s+|[a-zA-Z][.)]\s+|\d+[.)]\s+|[-•*?]\s*)(.{10,200})',
        body, re.MULTILINE)
    junk = re.compile(r'must\s+be\s+firm|vat\s+inclusive|business\s+day|closing\s+date\b', re.IGNORECASE)
    docs = [_cv(i) for i in items if len(_cv(i)) > 10 and not junk.search(i)]
    return docs[:10]


def extract_deliverables(sections):
    sections = _coerce_sections(sections)
    body = _sec('specifications', 'deliverables', 'pricing', sections=sections)
    full = sections.get('full', '')

    items = re.findall(
        r'(?:^|\n)\s*(?:•\s*|-\s*)([A-Z][^\n]{10,120})',
        body or full, re.MULTILINE)
    result = [_cv(i) for i in items
              if re.search(r'supply|deliver|install|replace|upgrade|provide|repair', i, re.IGNORECASE)
              and len(_cv(i)) > 10]
    return result[:8]


def extract_pricing_schedule(sections):
    sections = _coerce_sections(sections)
    body = _sec('pricing', 'specifications', sections=sections)
    if not body:
        return []
    numbered = re.findall(r'(?:^|\n)\s*(\d+)\s+([A-Z][^\n]{8,120})', body, re.MULTILINE)
    items = []
    for num, desc in numbered:
        v = _cv(f"{num}. {desc}")
        if len(v) > 12 and not re.search(r'bidding\s+procedure|enquir|clarification', v, re.IGNORECASE):
            items.append(v)
    seen, unique = set(), []
    for i in items:
        if i.lower() not in seen:
            seen.add(i.lower())
            unique.append(i)
    return unique[:20]
