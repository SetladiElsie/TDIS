import glob, os
from extraction import *

for pdf in sorted(glob.glob('uploads/*.pdf'), key=os.path.getmtime, reverse=True)[:4]:
    print(f"\n{'='*65}\nFILE: {os.path.basename(pdf)}\n{'='*65}")
    text = extract_text_from_file(pdf, 'pdf')
    email, phone = extract_contact_info(text)
    for k, v in [
        ('tender_id',          extract_tender_id(text)),
        ('tender_name',        extract_tender_name(text)),
        ('organization',       extract_organization(text)),
        ('closing_date',       extract_closing_date(text)),
        ('scope_of_work',      (extract_scope_of_work(text) or '')[:150]),
        ('evaluation_criteria',extract_evaluation_criteria(text)),
        ('submission',         extract_submission_details(text)),
        ('deliverables',       extract_deliverables(text)[:3]),
        ('compulsory_docs',    extract_compulsory_documents(text)[:3]),
        ('budget',             extract_budget(text)),
        ('contact_email',      email),
        ('contact_phone',      phone),
        ('location',           extract_location(text)),
        ('duration',           extract_duration(text)),
    ]:
        print(f"  {k:22s}: {v}")
