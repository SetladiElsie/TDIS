"""Show first 3000 chars + key-term lines for the most recent uploaded PDF."""
import glob, os
from extraction import extract_text_from_file

pdfs = sorted(glob.glob('uploads/*.pdf'), key=os.path.getmtime, reverse=True)
if not pdfs:
    print("No PDFs in uploads/")
else:
    pdf = pdfs[0]
    print("FILE:", os.path.basename(pdf))
    text = extract_text_from_file(pdf, 'pdf')
    print(f"CHARS: {len(text)}\n")
    print("=== FIRST 3000 ===")
    print(text[:3000])
    print("\n=== LINES WITH KEY TERMS ===")
    for line in text.splitlines():
        l = line.lower().strip()
        if l and any(k in l for k in [
            'tender','rfq','rfp','reference no','bid no','ref no',
            'closing','deadline','submission date',
            'scope','objective','background',
            'evaluation','criteria','phase',
            'issued by','from:','organisation','department','authority','institute','agency','municipality','commission',
            'submit','email to','hand deliver',
            'location','destination','delivery address','province',
            'duration','validity period','contract period','months','weeks',
            'compulsory','mandatory','required document','returnable',
            'budget','contract value','estimated cost',
        ]):
            print(' ', repr(line.strip()[:130]))
