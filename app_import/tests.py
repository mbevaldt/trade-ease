import os
from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bill_path = BASE_DIR + '/media/invoices/' + "Commercial invoice - CI-22-376.pdf"

for x in range(10):
    print(x)

print(x+10)
