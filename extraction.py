import os
import re
from datetime import datetime
from PyPDF2 import PdfReader
from docx import Document
import csv
import json
from openpyxl import load_workbook

def extract_text_from_pdf(filepath):
    """Extract text from PDF file"""
    try:
        text = ""
        with open(filepath, 'rb') as file:
            reader = PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        raise Exception(f"Error extracting PDF: {str(e)}")

def extract_text_from_docx(filepath):
    """Extract text from DOCX file"""
    try:
        text = ""
        doc = Document(filepath)
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # Extract text from tables if present
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
        
        return text
    except Exception as e:
        raise Exception(f"Error extracting DOCX: {str(e)}")

def extract_text_from_txt(filepath):
    """Extract text from TXT file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    except Exception as e:
        raise Exception(f"Error extracting TXT: {str(e)}")

def extract_text_from_csv(filepath):
    """Extract text from CSV file"""
    try:
        text = ""
        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                text += " ".join(row) + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error extracting CSV: {str(e)}")

def extract_text_from_xlsx(filepath):
    """Extract text from Excel file"""
    try:
        text = ""
        workbook = load_workbook(filepath)
        for sheet in workbook.sheetnames:
            ws = workbook[sheet]
            text += f"Sheet: {sheet}\n"
            for row in ws.iter_rows(values_only=True):
                text += " ".join([str(cell) if cell else "" for cell in row]) + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error extracting XLSX: {str(e)}")

def extract_text_from_file(filepath, file_type):
    """Main function to extract text from any supported file type"""
    file_ext = file_type.lower()
    
    if file_ext == 'pdf' or filepath.endswith('.pdf'):
        return extract_text_from_pdf(filepath)
    elif file_ext in ['docx', 'doc'] or filepath.endswith(('.docx', '.doc')):
        return extract_text_from_docx(filepath)
    elif file_ext == 'txt' or filepath.endswith('.txt'):
        return extract_text_from_txt(filepath)
    elif file_ext == 'csv' or filepath.endswith('.csv'):
        return extract_text_from_csv(filepath)
    elif file_ext == 'xlsx' or filepath.endswith('.xlsx'):
        return extract_text_from_xlsx(filepath)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

def extract_closing_date(text):
    """Extract closing date from text"""
    # Pattern variations for closing dates
    patterns = [
        r'(?:closing\s+date|deadline|due\s+date|submission\s+deadline)[:\s]+([^\n]+?)(?:\n|$)',
        r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            return date_str
    
    return None

def extract_scope_of_work(text):
    """Extract scope of work from text"""
    patterns = [
        r'(?:scope\s+of\s+work|scope)[:\s]+([^\n]+(?:\n(?!(?:evaluation|requirement|closing|deadline))[^\n]+)*)',
        r'(?:description|objective|project\s+description)[:\s]+([^\n]+(?:\n(?!(?:evaluation|requirement|closing))[^\n]+)*)',
        r'(?:work\s+to\s+be\s+done)[:\s]+([^\n]+(?:\n(?!(?:evaluation|requirement|closing))[^\n]+)*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            scope = match.group(1).strip()
            # Clean up excessive whitespace
            scope = ' '.join(scope.split())
            return scope[:500]  # Limit to 500 chars
    
    return None

def extract_evaluation_criteria(text):
    """Extract evaluation criteria from text"""
    criteria = []
    
    # Pattern to find evaluation criteria section
    pattern = r'(?:evaluation\s+criteria|evaluation\s+method|assessment\s+criteria)[:\s]*\n(.*?)(?=\n\n|\nrequirement|\nsubmission|$)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        criteria_text = match.group(1)
        # Extract bullet points or numbered items
        items = re.findall(r'(?:^|\n)[\s]*(?:\d+\.|[-•*])\s*(.+?)(?=\n|$)', criteria_text, re.MULTILINE)
        criteria = [item.strip() for item in items if item.strip()]
    
    return criteria[:5]  # Limit to 5 criteria

def extract_submission_details(text):
    """Extract submission details from text"""
    submission_format = None
    
    # Pattern for submission format
    patterns = [
        r'(?:submit.*?(?:format|form)|submission\s+format)[:\s]+([^\n]+)',
        r'(?:format)[:\s]+(.+?)(?:pdf|docx|word|document)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            submission_format = match.group(1).strip()
            break
    
    return submission_format

def extract_deliverables(text):
    """Extract deliverables from text"""
    deliverables = []
    
    # Pattern to find deliverables section
    pattern = r'(?:deliverable|output|deliverable\s+item)[s]?[:\s]*\n(.*?)(?=\n\n|\nrequirement|\nevaluation|$)'
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        deliverables_text = match.group(1)
        # Extract bullet points or numbered items
        items = re.findall(r'(?:^|\n)[\s]*(?:\d+\.|[-•*])\s*(.+?)(?=\n|$)', deliverables_text, re.MULTILINE)
        deliverables = [item.strip() for item in items if item.strip()]
    
    return deliverables[:10]

def extract_compulsory_documents(text):
    """Extract compulsory/required documents from text"""
    documents = []
    
    # Pattern to find required documents section
    patterns = [
        r'(?:compulsory|required|mandatory|essential)\s+(?:document|submission)[s]?[:\s]*\n(.*?)(?=\n\n|\nevaluation|\nsubmission|$)',
        r'(?:document)[s]?\s+required[:\s]*\n(.*?)(?=\n\n|\nevaluation|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            docs_text = match.group(1)
            # Extract bullet points or numbered items
            items = re.findall(r'(?:^|\n)[\s]*(?:\d+\.|[-•*])\s*(.+?)(?=\n|$)', docs_text, re.MULTILINE)
            documents = [item.strip() for item in items if item.strip()]
            if documents:
                break
    
    return documents[:10]

def extract_tender_id(text):
    """Extract tender ID/reference number from text"""
    patterns = [
        r'(?:tender\s+(?:id|number|reference)|reference\s+number|tender\s+ref)[:\s]+([A-Z0-9\-]+)',
        r'(?:RFP|RFQ|ITB)[\s-]*([A-Z0-9\-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def extract_tender_name(text):
    """Extract tender name/title from text"""
    # Usually in the first few lines
    lines = text.split('\n')[:10]
    
    patterns = [
        r'(?:tender|project)\s+(?:title|name)[:\s]+(.+?)(?:\n|$)',
        r'^(?!.*?(?:scope|requirement|closing|evaluation))(.{20,100})$',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, '\n'.join(lines), re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            if len(name) > 10:
                return name[:200]
    
    return None

def extract_organization(text):
    """Extract issuing organization from text"""
    patterns = [
        r'(?:issued\s+by|organization|ministry|department|authority)[:\s]+([^\n]+)',
        r'(?:from|issued\s+from)[:\s]+([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            org = match.group(1).strip()
            if len(org) > 2:
                return org[:200]
    
    return None

def extract_budget(text):
    """Extract budget/project value from text"""
    patterns = [
        r'(?:budget|project\s+value|estimated\s+cost|total\s+cost)[:\s]*[A-Z]?[{$£€¥]?\s*([0-9,]+\.?[0-9]*)\s*(?:million|thousand|K|M)?',
        r'([0-9,]+\.?[0-9]*)\s*(?:million|thousand|K|M)\s*(?:USD|EUR|GBP)',
    ]
    
    budget_amount = None
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount_str = match.group(1).replace(',', '')
            try:
                budget_amount = float(amount_str)
                break
            except:
                pass
    
    return budget_amount

def extract_contact_info(text):
    """Extract contact information from text"""
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    email = email_match.group(0) if email_match else None
    
    # Phone pattern
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
    phone_match = re.search(phone_pattern, text)
    phone = phone_match.group(0) if phone_match else None
    
    return email, phone

def extract_location(text):
    """Extract project location from text"""
    patterns = [
        r'(?:location|project\s+location|site|jurisdiction|region|area)[:\s]+([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            if len(location) > 2:
                return location[:200]
    
    return None

def extract_duration(text):
    """Extract project duration from text"""
    patterns = [
        r'(?:duration|timeline|period)[:\s]+([^\n]+(?:\d+\s+(?:month|year|week|day))[^\n]*)',
        r'(\d+\s+(?:month|year|week|day)s?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            duration = match.group(1).strip()
            return duration[:100]
    
    return None
