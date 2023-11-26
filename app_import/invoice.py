import os
import re
import glob
import fitz # pymupdf 

def remove_invoices():
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
      files = glob.glob(BASE_DIR + '/media/invoices/*.pdf')
      for f in files:
            os.remove(f)

def process_invoice(invoice):
      
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      invoice_path = BASE_DIR + '/media/invoices/' + invoice

      pdf = fitz.open(invoice_path) 
      text = pdf[0].get_text(sort=True)
      dict_invoice = {}

      invoice_number = re.findall('Invoice\sNumber\\n(\w\w-\d\d-\d{4})', text)
      date_ = re.findall('(\d\d[.\/]\d\d[.\/]\d{4})', text)
      container_num = re.findall('(\w{4}\d{7})\\nContainer', text)
      port_dest = re.findall('Port\s\/\sDestination\\n(.*)\\n', text)

      invoice_text = f'Invoice Number: {invoice_number[0]}\n'
      invoice_text += f'Date: {date_[0]}\n'
      invoice_text += f'Container No: {container_num[0]}\n'
      invoice_text += f'Port/Destination: {port_dest[0]}\n'
      
      description = re.findall('(\d{3}\/\d{2}R.*?)\\n', text)
      quantity = re.findall('\d{3}\/\d{2}R.*?\\n\s*(\d+)\s*\\n', text)
      unit_value = re.findall('\d{3}\/\d{2}R.*?\\n\s*\d+\\n{0,3}\s*(\d+\.?\d{2})', text)
      
      item_text = ''
      for r, _ in enumerate(description):
            item_text += f'{description[r]}\t{quantity[r]}\t{unit_value[r]}\n'

      doc = fitz.open()
      page = doc.new_page()

      where = fitz.Point(50, 100)
      page.insert_text(where, 'INVOICE DATA', fontsize=20)

      where = fitz.Point(50, 130)
      page.insert_text(where, invoice_text, fontsize=15)

      where = fitz.Point(50, 230)
      page.insert_text(where, item_text, fontsize=10)

      #new_name = re.sub('\.pdf', ' - summary.pdf', invoice)
      new_name = f'{invoice_number[0]} Summary.pdf'
      doc.save(BASE_DIR + f'/media/invoices/{new_name}')

      return new_name


#process_invoice('Commercial_invoice_-_CI-22-376.pdf')














