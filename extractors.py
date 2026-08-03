"""
extractors.py — All field extractor functions.
Imported by extraction.py; do not run directly.
"""
import re

# ── Shared helpers ─────────────────────────────────────────────────────────────

_BOILERPLATE = re.compile(
    r'prevention\s+and\s+combating|not\s+exceeding\s+ten'
    r'|period\s+not\s+exceeding\s+10|it\s+is\s+decided'
    r'|agreed\s+by\s+the\s+parties|means\s+(?:a|an|the)\b'
    r'|business\s+day\s+means|designated\s+sector'
    r'|contact\s+details\s*$|indicated\s+in\s+point',
    re.IGNORECASE
)

# Junk headings / lines that are NOT scope content
_SCOPE_JUNK = re.compile(
    r'PFMA|Public\s+Finance\s+Management|Schedule\s+3'
    r'|provincial\s+public\s+entity'
    r'|any\s+person\s+\(natural\s+or\s+juristic\)\s+may\s+make\s+an\s+offer'
    r'|in\s+terms\s+of\s+this\s+invitation\s+to\s+bid'
    r'|purpose\s+of\s+the\s+form',
    re.IGNORECASE
)


def _cv(v):
    """Collapse internal whitespace."""
    return ' '.join(v.split()) if v else ''


def _fm(patterns, text, flags=re.IGNORECASE):
    """Return first non-empty group(1) match."""
    for p in patterns:
        m = re.search(p, text, flags)
        if m:
            v = _cv(m.group(1))
            if v:
                return v
    return None


def _sec(*names, sections):
    """Concatenate named section bodies."""
    return '\n'.join(sections[n] for n in names if sections.get(n))


def _section_text(body: str, strip_heading: str = '') -> str:
    """
    Clean a section body:
    - Strip the heading line
    - Strip running page headers
    - Return all remaining text (no length cap)
    """
    if strip_heading:
        body = re.sub(
            rf'^[^\n]*{re.escape(strip_heading)}[^\n]*\n',
            '', body, flags=re.IGNORECASE)
    body = re.sub(r'Reference\s+No[.:][^\n]+', '', body, flags=re.IGNORECASE)
    body = re.sub(r'^\s*\d+\s*\|\s*P\s*a\s*g\s*e\s*$', '', body,
                  flags=re.MULTILINE | re.IGNORECASE)
    return body.strip()


# ── 1. Tender ID ───────────────────────────────────────────────────────────────

def extract_tender_id(text):
    patterns = [
        r'reference\s+no[.:\s]+([A-Z0-9][A-Z0-9/\-. ]{2,35})',
        r'(?:request\s+for\s+(?:quotation|proposal|tender)\s+no\.?'
        r'|rfq\s+no\.?|rfp\s+no\.?|bid\s+no\.?|tender\s+no\.?'
        r'|ref\.?\s*no\.?)[:\s]+([A-Z0-9][A-Z0-9/\-.]{3,30})',
        r'\b((?:RFQ|RFP|RFT|ITB)\s+\d[A-Z0-9/\-.]{3,25})',
    ]
    v = _fm(patterns, text)
    if not v:
        return None
    v = re.sub(r'\s+\d+\s*\|.*$', '', v).strip()
    v = re.sub(r'\s+[A-Z]{3,}\s*$', '', v).strip()
    if re.search(r'\d', v) and 3 <= len(v) <= 40:
        return v
    return None


# ── 2. Tender Name ─────────────────────────────────────────────────────────────

def extract_tender_name(text):
    top = '\n'.join(text.splitlines()[:50])

    v = _fm([
        r'(?:description\s+of\s+services|subject|tender\s+(?:title|name|description)'
        r'|project\s+(?:title|name))[:\s]+(.{15,250})',
        r'invitation\s+to\s+bid[:\s]+(.{10,250})',
    ], top)
    if v and 15 <= len(v) <= 250 and not _BOILERPLATE.search(v):
        return v[:250]

    kw = re.compile(
        r'^(?:supply\s+(?:and\s+)?(?:delivery|installation|provision)|provision\s+of'
        r'|appointment\s+of|procurement\s+of)\s+.{10,}',
        re.IGNORECASE)
    for line in text.splitlines()[:50]:
        s = line.strip()
        if kw.match(s) and 15 <= len(s) <= 250:
            return _cv(s)[:250]

    skip = re.compile(
        r'page\s+\d+|p\s+a\s+g\s+e|\brev\b|doc\.\s*no'
        r'|request\s+for\s+(quotation|proposal)|rfq\b|rfp\b'
        r'|from:|dear\s|please\s+provide|^\s*\d+\s*$',
        re.IGNORECASE)
    for line in text.splitlines()[:35]:
        s = line.strip()
        if re.search(r'[-_]{5,}', s):
            continue
        if 20 <= len(s) <= 200 and not skip.search(s):
            has_kw = re.search(
                r'supply|deliver|install|provision|appointment|service|procure'
                r'|tender|bid|laptop|toner|cartridge|cabling|remediation|infrastructure'
                r'|construction|maintenance|repair|upgrade|development',
                s, re.IGNORECASE)
            caps = sum(1 for w in s.split() if w and w[0].isupper())
            if has_kw or caps >= 3:
                return s[:250]
    return None


# ── 3. Closing Date ────────────────────────────────────────────────────────────

_MONTHS = (r'Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?'
           r'|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?')


def extract_closing_date(text):
    patterns = [
        rf'closing\s+date\s{{1,15}}(\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}})',
        rf'closing\s+date[:\s]+(\d{{1,2}}\s+\w+\s+\d{{4}})',
        r'(?:rfq|rfp|rft|bid|tender)\s*closing\s+date(?:\s+and\s+time)?[:\s]+([^\n]{4,40})',
        r'(?:due\s+date|deadline|submission\s+(?:date|closing))[:\s]+([^\n]{4,40})',
        r'rfp\s+closing\s+date\s+and\s+time[:\s]+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        r'closing\s+date\s+(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        rf'\b(\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}})\b',
        r'\b(\d{4}[/-]\d{2}[/-]\d{2})\b',
        r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = _cv(m.group(1))[:60]
            v = re.sub(r'\s*(?:closing\s+time|and\s+time|at\s+\d[\d:hH]+)[^\n]*$',
                       '', v, flags=re.IGNORECASE).strip()
            v = re.sub(r'(\b\d{4}\b)\s+\D.*$', r'\1', v).strip()
            if v:
                return v
    return None


# ── 4. Scope of Work ──────────────────────────────────────────────────────────

def extract_scope_of_work(sections):
    """
    Extract the full scope of work.
    Strategy:
    1. Look for a dedicated 'scope' section — take ALL its text.
    2. If none, try 'objective', then 'background'/'purpose' (skipping boilerplate).
    3. If still nothing, search the full text for a SCOPE OF WORK heading and
       capture everything up to the next major section heading.
    No hard character cap — return the complete text of the section.
    """

    # ── Step 1: dedicated scope section ──────────────────────────────────────
    scope_body = sections.get('scope', '')
    if scope_body and not _SCOPE_JUNK.search(scope_body):
        cleaned = _section_text(scope_body, strip_heading='scope of work')
        # Remove sub-heading lines that are just numbers/section markers
        lines = [l for l in cleaned.splitlines()
                 if l.strip() and not re.match(r'^\s*\d+[\.\d]*\s*$', l.strip())]
        result = _cv(' '.join(lines))
        if len(result) >= 40:
            return result

    # ── Step 2: objective section ─────────────────────────────────────────────
    obj_body = sections.get('objective', '')
    if obj_body and not _SCOPE_JUNK.search(obj_body):
        cleaned = _section_text(obj_body, strip_heading='objective')
        lines = [l for l in cleaned.splitlines()
                 if l.strip() and len(l.strip()) >= 20]
        result = _cv(' '.join(lines))
        if len(result) >= 40:
            return result

    # ── Step 3: search full text for SCOPE heading ───────────────────────────
    full = sections.get('full', '')
    scope_match = re.search(
        r'(?:^|\n)\s*(?:\d+\.?\d*\s+)?SCOPE\s+OF\s+WORK[^\n]*\n',
        full, re.IGNORECASE)
    if scope_match:
        after = full[scope_match.end():]
        # Stop at the next major numbered/all-caps section heading
        next_sec = re.search(
            r'\n\s*(?:\d+\.?\s+[A-Z]{3}|\n[A-Z]{4}[A-Z \t]{3,}\n)',
            after)
        body = after[:next_sec.start()] if next_sec else after[:8000]
        body = re.sub(r'Reference\s+No[.:][^\n]+', '', body, flags=re.IGNORECASE)
        lines = [l for l in body.splitlines()
                 if l.strip() and not re.match(r'^\s*\d+[\.\d]*\s*$', l.strip())]
        result = _cv(' '.join(lines))
        if len(result) >= 40:
            return result

    # ── Step 4: background as last resort (non-boilerplate) ──────────────────
    for sec_name in ('background', 'purpose', 'specifications'):
        body = sections.get(sec_name, '')
        if not body or _SCOPE_JUNK.search(body):
            continue
        cleaned = _section_text(body)
        lines = [l for l in cleaned.splitlines()
                 if l.strip() and len(l.strip()) >= 20]
        result = _cv(' '.join(lines))
        if len(result) >= 40:
            return result

    return None


# ── 5. Mandatory Criteria ─────────────────────────────────────────────────────

def extract_mandatory_criteria(sections):
    """
    Extract mandatory / compulsory requirements that bidders must meet.
    These are often listed as Phase 1 gatekeeping criteria or in a
    dedicated mandatory requirements section.
    """
    # Look in the compulsory section first
    body = sections.get('compulsory', '')

    # Also check evaluation section for Phase 1 / mandatory block
    eval_body = sections.get('evaluation', '')
    if eval_body:
        phase1 = re.search(
            r'(?:Phase\s+1|mandatory\s+requirement|gatekeeping)[^\n]*\n(.*?)'
            r'(?=Phase\s+[23]|\n\s*\n\s*[A-Z]{3}|\Z)',
            eval_body, re.IGNORECASE | re.DOTALL)
        if phase1:
            body = (body + '\n' + phase1.group(1)) if body else phase1.group(1)

    # Fall back to searching full text
    if not body:
        full = sections.get('full', '')
        m = re.search(
            r'(?:mandatory\s+requirement|compulsory\s+(?:returnable|document|criteria)'
            r'|gatekeeping\s+criteria|pre-?qualification\s+criteria)',
            full, re.IGNORECASE)
        if m:
            start = full.find('\n', m.end())
            body = full[start:start + 3000] if start != -1 else ''

    if not body:
        return []

    # Extract bulleted / numbered items
    items = re.findall(
        r'(?:^|\n)\s*(?:[ivxIVX]{1,5}[.)]\s+|[a-zA-Z]\.\s+|\d+\.\s+|[-•*]\s+)(.{10,250})(?=\n|$)',
        body, re.MULTILINE)

    junk = re.compile(
        r'must\s+be\s+firm|vat\s+inclusive|will\s+be\s+disqualified'
        r'|means\s+(?:a|an|the)\b|designated\s+sector|business\s+day'
        r'|closing\s+date\b|email\s+address',
        re.IGNORECASE)

    criteria = [_cv(i) for i in items if len(_cv(i)) > 10 and not junk.search(i)]

    # Deduplicate
    seen, unique = set(), []
    for c in criteria:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)
    return unique[:15]


# ── 6. Pricing Schedule ───────────────────────────────────────────────────────

def extract_pricing_schedule(sections):
    """
    Extract pricing / bill-of-quantities items.
    Returns a list of line items found in the pricing or specifications section.
    """
    body = _sec('pricing', 'specifications', sections=sections)

    if not body:
        return []

    # Remove running headers and boilerplate
    body = re.sub(r'Reference\s+No[.:][^\n]+', '', body, flags=re.IGNORECASE)
    body = re.sub(r'^\s*\d+\s*\|\s*P\s*a\s*g\s*e\s*$', '', body,
                  flags=re.MULTILINE | re.IGNORECASE)

    items = []

    # Numbered items: "1 Black Drum For Konica Minolta C300I 2 R R"
    numbered = re.findall(
        r'(?:^|\n)\s*(\d+)\s+([A-Z][^\n]{8,120})',
        body, re.MULTILINE)
    for num, desc in numbered:
        v = _cv(f"{num}. {desc}")
        if (len(v) > 12
                and not re.search(
                    r'bidding\s+procedure|enquir|clarification|introduction'
                    r'|background|specification\s*/\s*pricing\s+structure',
                    v, re.IGNORECASE)):
            items.append(v)

    # Bullet / dash items
    if not items:
        bullets = re.findall(
            r'(?:^|\n)\s*(?:•\s*|-\s*)([A-Z][^\n]{8,120})',
            body, re.MULTILINE)
        items = [_cv(i) for i in bullets
                 if len(_cv(i)) > 10
                 and re.search(r'supply|deliver|install|laptop|toner|drum|item|unit|qty|price',
                               i, re.IGNORECASE)]

    # Deduplicate
    seen, unique = set(), []
    for i in items:
        if i.lower() not in seen:
            seen.add(i.lower())
            unique.append(i)
    return unique[:20]


# ── 7. Submission Details ─────────────────────────────────────────────────────

def extract_submission_details(sections):
    body = _sec('submission', sections=sections)
    full = sections.get('full', '')

    junk = re.compile(
        r'earn\s+(?:the\s+)?(?:relevant\s+)?point|preference\s+point'
        r'|in\s+order\s+to|must\s+be\s+used',
        re.IGNORECASE)

    patterns = [
        r'(?:bid\s+response\s+documents?\s+must\s+be\s+submitted\s+(?:via\s+email\s+)?to'
        r'|submitted?\s+via\s+email\s+(?:only\s+)?to'
        r'|must\s+be\s+submitted\s+(?:via\s+)?email\s+(?:only\s+)?to)[:\s]+([^\n]{5,200})',
        r'(?:email\s+the\s+quotation\s+to|quotes?\s+must\s+be\s+emailed?\s+to'
        r'|quotation\s+(?:must\s+be\s+)?submitted?\s+to)[:\s]+([^\n]{5,200})',
        r'proposal\s+to\s+be\s+hand\s+delivered[:\s]+([^\n]{5,200})',
        r'bids?\s+(?:must\s+be\s+)?(?:submitted?|emailed?)\s+to[:\s]+'
        r'([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
        r'(?:send\s+to|email\s+to)[:\s]+([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
        r'directed\s+to\s+([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
        r'e-?mail\s+address[:\s]+([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
        r'e-?mail[:\s]+([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
    ]

    for source in (body, full):
        if not source:
            continue
        for p in patterns:
            m = re.search(p, source, re.IGNORECASE)
            if m:
                v = _cv(m.group(1))[:300]
                if len(v) > 5 and not junk.search(v):
                    return v
    return None


# ── 8. Compulsory Documents ───────────────────────────────────────────────────

def extract_compulsory_documents(sections):
    body = sections.get('compulsory', '')

    if not body:
        full = sections.get('full', '')
        m = re.search(
            r'(?:mandatory\s+requirement|compulsory\s+(?:returnable|document)'
            r'|required\s+returnable|table\s+\d+[:\s]+compulsory)',
            full, re.IGNORECASE)
        if m:
            start = full.find('\n', m.end())
            body = full[start:start + 3000] if start != -1 else ''

    if not body:
        return []

    items = re.findall(
        r'(?:^|\n)\s*(?:[ivxIVX]{1,5}[.)]\s+|[a-zA-Z]\.\s+|\d+\.\s+|[-•*]\s+)(.{10,200})(?=\n|$)',
        body, re.MULTILINE)

    junk = re.compile(
        r'must\s+be\s+firm|vat\s+inclusive|will\s+be\s+disqualified'
        r'|means\s+(?:a|an|the)\b|designated\s+sector|business\s+day'
        r'|closing\s+date\b|email\s+address',
        re.IGNORECASE)

    docs = [_cv(i) for i in items if len(_cv(i)) > 10 and not junk.search(i)]
    return docs[:10]


# ── 9. Deliverables ───────────────────────────────────────────────────────────

def extract_deliverables(sections):
    body = _sec('specifications', 'deliverables', 'pricing', sections=sections)

    items = []
    if body:
        found = re.findall(
            r'(?:^|\n)\s*\d+\.?\s+([A-Z][^\n]{10,120})',
            body, re.MULTILINE)
        items = [_cv(i) for i in found
                 if len(_cv(i)) > 10
                 and not re.search(
                     r'bidding\s+procedure|enquir|clarification|phone|email'
                     r'|specification\s*/\s*pricing|pricing\s+structure',
                     i, re.IGNORECASE)][:10]

    if not items:
        full = sections.get('full', '')
        found = re.findall(
            r'(?:^|\n)\s*(?:•\s*|-\s*)([A-Z][^\n]{10,120})',
            full, re.MULTILINE)
        items = [_cv(i) for i in found
                 if re.search(r'supply|deliver|install|replace|upgrade|provide|repair',
                              i, re.IGNORECASE)
                 and len(_cv(i)) > 10][:8]
    return items


# ── 10. Contact Info ──────────────────────────────────────────────────────────

def extract_contact_info(text):
    emails = re.findall(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', text)
    email = None
    priority = ('procurement', 'tender', 'tenders', 'bid', 'bids', 'supply', 'admin', 'info')
    for e in emails:
        if any(k in e.lower() for k in priority):
            email = e
            break
    if not email and emails:
        email = emails[0]

    pm = re.search(
        r'(?:\+27|0)[\s\-]?(?:\d[\s\-]?){8,9}\d'
        r'|(?:\+\d{1,3}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}',
        text)
    phone = _cv(pm.group(0)) if pm else None
    return email, phone


# ── 11. Location ──────────────────────────────────────────────────────────────

def extract_location(text):
    junk = re.compile(
        r'indicated\s+in|refer\s+to|as\s+per\b|see\s+point|absence\s+of'
        r'|in\s+transit|handling\s+facilities|contact\s+details',
        re.IGNORECASE)

    patterns = [
        r'destination[:\s]+([^\n]{5,200})',
        r'delivery\s+address[:\s]+([^\n]{5,200})',
        r'delivery\s+(?:details?|location)[:\s]+([^\n]{5,150})',
        r'site\s+(?:address|location)[:\s]+([^\n]{5,100})',
        r'project\s+location[:\s]+([^\n]{5,100})',
        r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+)*,\s*(?:KwaZulu|KZN|Northern\s+Cape'
        r'|Western\s+Cape|Eastern\s+Cape|Gauteng|Limpopo|Mpumalanga'
        r'|Free\s+State|North\s+West)[^\n]{0,80})\b',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            v = _cv(m.group(1))
            if len(v) > 5 and not junk.search(v):
                return v[:200]
    return None


# ── 12. Duration ──────────────────────────────────────────────────────────────

def extract_duration(sections):
    body = _sec('duration', sections=sections)
    full = sections.get('full', '')

    junk = re.compile(
        r'it\s+is\s+decided|shall\s+not\s+relieve|prevention\s+and\s+combating'
        r'|not\s+exceeding\s+ten|period\s+not\s+exceeding\s+10\s+years',
        re.IGNORECASE)

    patterns = [
        r'(?:quotation\s+validity\s+period|validity\s+period\s+of\s+bids?)[:\s]+([^\n]{3,60})',
        r'(?:contract\s+period|period\s+of\s+(?:contract|performance|validity)'
        r'|project\s+(?:duration|timeline)|duration\s+of\s+(?:contract|service))[:\s]+([^\n]{3,60})',
        r'for\s+a\s+period\s+of\s+((?:six|twelve|three|four|five|two|one|\d+)'
        r'\s+\(\d+\)\s+months?(?:\s+with[^\n]{0,60})?)',
        r'\b(\d+\s+(?:working\s+)?(?:months?|years?|weeks?|days?)'
        r'(?:\s+(?:from|after|of)\s+[^\n]{0,30})?)\b',
    ]
    for source in (body, full):
        if not source:
            continue
        for p in patterns:
            m = re.search(p, source, re.IGNORECASE)
            if m:
                v = _cv(m.group(1))[:120]
                if len(v.split()) <= 20 and not junk.search(v):
                    return v
    return None
