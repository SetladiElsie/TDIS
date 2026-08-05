"""
extraction.py — Section-aware tender document extraction engine.

Pipeline
--------
read file → normalise text → split into sections → extract each field
from the most relevant section → return clean dict.
"""

import re
import csv
from PyPDF2 import PdfReader
from docx import Document
from openpyxl import load_workbook

from extractors import (
    extract_tender_id,
    extract_tender_name,
    extract_closing_date,
    extract_scope_of_work,
    extract_mandatory_criteria,
    extract_pricing_schedule,
    extract_submission_details,
    extract_compulsory_documents,
    extract_deliverables,
    extract_contact_info,
    extract_address,
    extract_duration,
    extract_organization,
    extract_budget,
    extract_evaluation_criteria,
    extract_briefing_session,
)


# ── file readers ───────────────────────────────────────────────────────────────

def extract_text_from_pdf(filepath):
    try:
        pages = []
        with open(filepath, 'rb') as f:
            for page in PdfReader(f).pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return '\n'.join(pages)
    except Exception as e:
        raise Exception(f"PDF read error: {e}")


def extract_text_from_docx(filepath):
    try:
        doc = Document(filepath)
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            for row in table.rows:
                parts.append(' | '.join(c.text.strip() for c in row.cells))
        return '\n'.join(parts)
    except Exception as e:
        raise Exception(f"DOCX read error: {e}")


def extract_text_from_txt(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as e:
        raise Exception(f"TXT read error: {e}")


def extract_text_from_csv(filepath):
    try:
        rows = []
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for row in csv.reader(f):
                rows.append(' '.join(row))
        return '\n'.join(rows)
    except Exception as e:
        raise Exception(f"CSV read error: {e}")


def extract_text_from_xlsx(filepath):
    try:
        parts = []
        wb = load_workbook(filepath, data_only=True)
        for name in wb.sheetnames:
            parts.append(f"Sheet: {name}")
            for row in wb[name].iter_rows(values_only=True):
                parts.append(' '.join(str(c) if c is not None else '' for c in row))
        return '\n'.join(parts)
    except Exception as e:
        raise Exception(f"XLSX read error: {e}")


def extract_text_from_file(filepath, file_type):
    ext = file_type.lower()
    lo  = filepath.lower()
    if ext == 'pdf'  or lo.endswith('.pdf'):              return extract_text_from_pdf(filepath)
    if ext in ('docx','doc') or lo.endswith(('.docx','.doc')): return extract_text_from_docx(filepath)
    if ext == 'txt'  or lo.endswith('.txt'):              return extract_text_from_txt(filepath)
    if ext == 'csv'  or lo.endswith('.csv'):              return extract_text_from_csv(filepath)
    if ext == 'xlsx' or lo.endswith('.xlsx'):             return extract_text_from_xlsx(filepath)
    raise ValueError(f"Unsupported file type: {file_type}")


# ── normalise ──────────────────────────────────────────────────────────────────

def _normalise(raw: str) -> str:
    """Clean raw PDF text while preserving line structure."""
    text = raw.replace('\u2013', '-').replace('\u2014', '-').replace('\u2012', '-')
    # Rejoin words broken by trailing hyphen across lines (PDF artefact)
    text = re.sub(r'-\s*\n\s*', '', text)
    # Collapse whitespace within lines, keep newlines
    text = re.sub(r'[^\S\n]+', ' ', text)
    # Remove ToC dot leaders ONLY (4+ dots, optionally followed by spaces and a page number)
    # Do NOT strip single dots (decimals) or slashes (reference numbers like 2026/27)
    text = re.sub(r'\.{4,}\s*\d*', '', text)
    # Remove running page headers like "Reference No: SCMU 05 - 2026/27   3 | P a g e"
    text = re.sub(r'Reference\s+No[.:][^\n]*\d\s*\|\s*P\s*a\s*g\s*e[^\n]*', '',
                  text, flags=re.IGNORECASE)
    # Remove standalone page lines like "3 | P a g e"
    text = re.sub(r'^\s*\d+\s*\|\s*P\s*a\s*g\s*e\s*$', '',
                  text, flags=re.MULTILINE | re.IGNORECASE)
    return text


# ── section splitter ───────────────────────────────────────────────────────────

_SECTION_HEADINGS = [
    ('reference',      r'^\s*(?:reference\s+no|ref\s*no|bid\s+no|rfq\s+no|rfp\s+no)[.:\s]'),
    ('invitation',     r'^\s*(?:invitation\s+to\s+bid|request\s+for\s+(?:quotation|proposal|tender))'),
    ('purpose',        r'^\s*(?:\d+[\.\s]+)?purpose\b'),
    ('background',     r'^\s*(?:\d+[\.\s]+)?background\b'),
    ('scope',          r'^\s*(?:\d+[\.\s]+)?scope\s+of\s+work\b'),
    ('objective',      r'^\s*(?:\d+[\.\s]+)?objective[s]?\b'),
    ('specifications', r'^\s*(?:\d+[\.\s]+)?(?:specification[s]?(?:\s*/\s*terms\s+of\s+reference|\s*\(please[^)]*\))?|terms\s+of\s+reference)\b'),
    ('evaluation',     r'^\s*(?:\d+[\.\s]+)?evaluation'),
    ('compulsory',     r'^\s*(?:\d+[\.\s]+)?(?:compulsory|mandatory)\s+(?:documents?|requirements?|returnables?|sites?|briefings?)'),
    ('submission',     r'^\s*(?:\d+[\.\s]+)?(?:submission|how\s+to\s+(?:bid|submit)|bidding\s+procedure)'),
    ('contact',        r'^\s*(?:\d+[\.\s]+)?contact\b'),
    ('deliverables',   r'^\s*(?:\d+[\.\s]+)?deliverables?\b'),
    ('duration',       r'^\s*(?:\d+[\.\s]+)?(?:duration|contract\s+period|validity)'),
    ('pricing',        r'^\s*(?:\d+[\.\s]+)?pricing'),
    ('general',        r'^\s*(?:\d+[\.\s]+)?general\s+conditions?'),
]

_HEADING_RE = re.compile(
    '|'.join(f'(?P<sec_{k}>{v})' for k, v in _SECTION_HEADINGS),
    re.IGNORECASE | re.MULTILINE
)


def _split_sections(text: str) -> dict:
    sections = {'full': text, 'header': ''}
    lines = text.splitlines()
    current_name  = 'header'
    current_lines = []

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            sections[current_name] = '\n'.join(current_lines).strip()
            current_name = 'other'
            for k, _ in _SECTION_HEADINGS:
                if m.group(f'sec_{k}'):
                    current_name = k
                    break
            current_lines = [line]
        else:
            current_lines.append(line)

    existing = sections.get(current_name, '')
    sections[current_name] = (existing + '\n' + '\n'.join(current_lines)).strip()
    return sections


# ── main entry point ───────────────────────────────────────────────────────────

def process_document(filepath: str, file_type: str) -> dict:
    """
    Full pipeline: read → normalise → split sections → extract all fields.
    Returns a dict with all field values (None / [] when not found).
    """
    raw      = extract_text_from_file(filepath, file_type)
    text     = _normalise(raw)
    sections = _split_sections(text)

    contacts, email, phone = extract_contact_info(text)
    budget = extract_budget(text)

    return {
        'tender_id':            extract_tender_id(text),
        'tender_name':          extract_tender_name(text),
        'organization':         extract_organization(text),
        'closing_date':         extract_closing_date(text),
        'scope_of_work':        extract_scope_of_work(sections),
        'mandatory_criteria':   extract_mandatory_criteria(sections),
        'evaluation_criteria':  extract_evaluation_criteria(sections),
        'pricing_schedule':     extract_pricing_schedule(sections),
        'submission_format':    extract_submission_details(sections),
        'deliverables':         extract_deliverables(sections),
        'compulsory_documents': extract_compulsory_documents(sections),
        'contact_email':        email,
        'contact_phone':        phone,
        'contact_persons':      contacts,
        'address':              extract_address(text),
        'briefing_session':     extract_briefing_session(text),
        'estimated_duration':   extract_duration(sections),
        'budget_amount':        budget.get('amount'),
        'budget_currency':      budget.get('currency'),
        'document_type':        'RFQ/RFP',
    }
