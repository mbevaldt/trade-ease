import os
import re
import glob
import fitz # pymupdf 
import pdfplumber
from pypdf import PdfReader
from .models import Invoice, ProForma, BillLading

print(pdfplumber.__version__)

def remove_invoices():
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
      files = glob.glob(BASE_DIR + '/media/invoices/*.pdf')
      for f in files:
            os.remove(f)

def process_invoice_old(invoice):
      
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      invoice_path = BASE_DIR + '/media/invoices/' + invoice

      pdf = fitz.open(invoice_path) 
      text = pdf[0].get_text(sort=True)
      dict_invoice = {}

      invoice_number = re.findall('Invoice\sNumber\\n(\w\w-\d\d-\d{4})', text)
      invoice_date = re.findall('(\d\d[.\/]\d\d[.\/]\d{4})', text)
      container_num = re.findall('(\w{4}\d{7})\\nContainer', text)
      port_dest = re.findall('Port\s\/\sDestination\\n(.*)\\n', text)

      invoice_text = f'Invoice Number: {invoice_number[0]}\n'
      invoice_text += f'invoice_date: {invoice_date[0]}\n'
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

def get_invoice_data(invoice):
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      invoice_path = BASE_DIR + '/media/invoices/' + invoice

      pdf = fitz.open(invoice_path) 
      text = pdf[0].get_text(sort=True)
      global dict_invoice 
      dict_invoice = {}

      invoice_number = re.findall('Invoice\sNumber\\n(\w\w-\d\d-\d{4})', text)
      invoice_date = re.findall('(\d\d[.\/]\d\d[.\/]\d{4})', text)
      container_num = re.findall('(\w{4}\d{7})\\nContainer', text)
      port_dest = re.findall('Port\s\/\sDestination\\n(.*)\\n', text)
      qtd_invoice = re.findall('Grand\sTotal\\n([\d,\.]+)\\n', text)
      tot_invoice = re.findall('Grand\sTotal\\n[\d,\.]+\\n([\d,\.]+)\\n', text)

      # split date, reverse and join '-' to get the format needed
      invoice_date = '-'.join(invoice_date[0].split('.')[::-1])

      dict_invoice['invoice_number'] = invoice_number[0]
      dict_invoice['invoice_date'] = invoice_date
      dict_invoice['container_num'] = container_num[0]
      dict_invoice['port_dest'] = port_dest[0]
      dict_invoice['qtd_invoice'] = qtd_invoice[0]
      dict_invoice['tot_invoice'] = tot_invoice[0]

      # use lookbehind and lookahead to remove last space
      description = re.findall('(\d{3}\/\d{2}R.*?)\\n', text)
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)

      quantity = re.findall('\d{3}\/\d{2}R.*?\\n\s*(\d+)\s*\\n', text)
      unit_value = re.findall('\d{3}\/\d{2}R.*?\\n\s*\d+\\n{0,3}\s*(\d+\.?\d{2})', text)

      # check if elements in a lis are equal
      # if([L[0]]*len(L) == L): True
      
      qtd, vlr = (0, 0)
      for q, u in zip(quantity, unit_value):
            qtd += int(q)
            vlr += int(q) * float(u)

      dict_invoice['qtd_tot_calc'] = f"{qtd:,.0f}"
      dict_invoice['vlr_tot_calc'] = f"{round(vlr, 2):,.2f}"
      dict_invoice['color_qtd'] = '#90EE90' if qtd_invoice[0] == f"{qtd:,.0f}" else 'red'
      dict_invoice['color_vlr'] = '#90EE90' if tot_invoice[0] == f"{vlr:,.2f}" else 'red'
      
      num_item = range(len(description))
      itens = list(zip(num_item, description, quantity, unit_value))
      dict_invoice['itens'] = itens
      
      return dict_invoice

def get_invoice_data_pypdf(invoice):
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      invoice_path = BASE_DIR + '/media/invoices/' + invoice

      reader = PdfReader(invoice_path)
      page = reader.pages[0]
      text = page.extract_text()

      global dict_invoice 
      dict_invoice = {}

      invoice_number = re.findall('(CI-\d\d-\d{4})', text)
      invoice_date = re.findall('(\d\d[.\/]\d\d[.\/]\d{4})', text)
      container_num = re.findall('(\w{4}\d{7})\sContainer', text)
      port_dest = re.findall('Discharge\s-\s(.*?)\sBrazil', text)
      qtd_invoice = re.findall('Grand\sTotal\s([\d,\.]+)', text)
      tot_invoice = re.findall('Grand\sTotal\s[\d,\.]+\s([\d,\.]+)', text)

      # split date, reverse and join '-' to get the format needed
      invoice_date = '-'.join(invoice_date[0].split('.')[::-1])

      dict_invoice['invoice_number'] = invoice_number[0]
      dict_invoice['invoice_date'] = invoice_date
      dict_invoice['container_num'] = container_num[0]
      dict_invoice['port_dest'] = port_dest[0]
      dict_invoice['qtd_invoice'] = qtd_invoice[0]
      dict_invoice['tot_invoice'] = tot_invoice[0]

      # use lookbehind and lookahead to remove last space
      description = re.findall('(\d{3}\/\d\dR.*?)\s+\d+,?\d+\s\d+\.\d{2}', text)
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)

      quantity = re.findall('\d{3}\/\d\dR.*?\s+(\d+,?\d+)\s\d+\.\d{2}', text)
      unit_value = re.findall('\d{3}\/\d\dR.*?\s+\d+,?\d+\s(\d+\.\d{2})', text)

      # check if elements in a lis are equal
      # if([L[0]]*len(L) == L): True
      
      qtd, vlr = (0, 0)
      for q, u in zip(quantity, unit_value):
            qtd += int(q)
            vlr += int(q) * float(u)

      dict_invoice['qtd_tot_calc'] = f"{qtd:,.0f}"
      dict_invoice['vlr_tot_calc'] = f"{round(vlr, 2):,.2f}"
      dict_invoice['color_qtd'] = '#90EE90' if qtd_invoice[0] == f"{qtd:,.0f}" else 'red'
      dict_invoice['color_vlr'] = '#90EE90' if tot_invoice[0] == f"{vlr:,.2f}" else 'red'
      
      num_item = range(len(description))
      itens = list(zip(num_item, description, quantity, unit_value))
      dict_invoice['itens'] = itens
      
      return dict_invoice

def add_invoice_data_bd(self):
      
      # se invoice_number já estiver no BD, não importa!
      invoice_number_items = Invoice.objects.filter(
                        invoice_number=dict_invoice['invoice_number'])
      
      if not invoice_number_items:
            for item_ in dict_invoice['itens']:

                  invoice = Invoice(invoice_number=dict_invoice['invoice_number'],
                                    invoice_date=dict_invoice['invoice_date'],
                                    container_num=dict_invoice['container_num'],
                                    port_dest=dict_invoice['port_dest'],
                                    num_item = item_[0],
                                    description=item_[1],
                                    quantity=item_[2],
                                    unit_value=float(item_[3]),
                                    )
                  invoice.save()

            return dict_invoice # "Dados salvos com sucesso!" 
      else:
            return f"ERRO: Invoice {dict_invoice['invoice_number']} já estava salva!" 

def get_proforma_data(proforma):
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      proforma_path = BASE_DIR + '/media/invoices/' + proforma

      with pdfplumber.open(proforma_path) as pdf: 
            text = pdf.pages[0].extract_text()

      global dict_proforma 
      dict_proforma = {}

      port_dest = re.findall('DISCHARGE\sPORT\s:\s(.*?),\sBRAZIL', text)
      pi_ref = re.findall('PI REF\s#\s(.*?)\\n', text)
      other_ref = re.findall('OTHER\sREFERENCE\s:\s(\d+)\\n', text)
      proforma_date = re.findall('DATE:(\d\d\.\d\d\.\d{4})', text)

      # split date, reverse and join '-' to get the format needed
      proforma_date = '-'.join(proforma_date[0].split('.')[::-1])

      dict_proforma['port_dest'] = port_dest[0]
      dict_proforma['pi_ref'] = pi_ref[0]
      dict_proforma['other_ref'] = other_ref[0]
      dict_proforma['proforma_date'] = proforma_date

      # use lookbehind and lookahead to remove last space
      description = re.findall('(\d{3}\/\d{2}R.*?\d{2}\s?[TH])', text)
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)
      
      brand = re.findall('(FERENTINO)\s\d{3}\/\d{2}R', text)
      quantity = re.findall('\d{3}\/\d{2}R.*?\d{2}\s?[TH]\s(\d+)\sPCS', text)
      ncm = re.findall('\d{3}\/\d{2}R.*?\d{2}\s?[TH]\s\d+\sPCS\s(\d{4}\.\d{2}\.\d{2})', text)
      weight = re.findall('\d{4}\.\d{2}\.\d{2}\s(\d+,\d+)', text)
      unit_value = re.findall('\d{4}\.\d{2}\.\d{2}\s\d+,\d+\s\d+,\d+\s(\d+,\d+)', text)
      
      weight = tuple(v.replace(',', '.') for v in weight)
      unit_value = tuple(v.replace(',', '.') for v in unit_value)

      qtd, vlr = (0, 0)
      for q, u in zip(quantity, unit_value):
            qtd += int(q)
            vlr += int(q) * float(u)
      dict_proforma['qtd_tot'] = f"{qtd:,.0f}"
      dict_proforma['vlr_tot'] = f"{round(vlr, 2):,.2f}"

      num_item = range(len(description))
      itens = list(zip(num_item, brand, description, quantity, 
                       ncm, weight, unit_value))
      dict_proforma['itens'] = itens

      return dict_proforma

def add_proforma_data_bd(self):
      
      # se pi_ref já estiver no BD, não importa!
      pi_ref_items = ProForma.objects.filter(
                        pi_ref=dict_proforma['pi_ref'])
      
      if not pi_ref_items:
            for item_ in dict_proforma['itens']:

                  proforma = ProForma(pi_ref=dict_proforma['pi_ref'], 
                                    other_ref=dict_proforma['other_ref'],
                                    proforma_date=dict_proforma['proforma_date'],
                                    port_dest=dict_proforma['port_dest'],
                                    num_item = item_[0],
                                    brand=item_[1],
                                    description=item_[2],
                                    quantity=float(item_[3]),
                                    ncm=item_[4],
                                    weight=float(item_[5]),
                                    unit_value=float(item_[6]),
                                    )
                  proforma.save()

            return "Dados salvos com sucesso!" 
      else:
            return f"Pro Forma {dict_proforma['pi_ref']} já estava salva!" 

def get_packing_list_data(packing_list):
      
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      packing_path = BASE_DIR + '/media/invoices/' + packing_list

      global dict_packing
      dict_packing = {}

      with pdfplumber.open(packing_path) as pdf: 
            text = pdf.pages[0].extract_text()
      
      invoice_number = re.findall('INVOICE.*?(\w\w-\d\d-\d{4})', text)   
      container_num = re.findall('Container\s[Nn]umber\s(.*?)\\n', text)  

      description = re.findall('(\d{3}\/\d{2}R.*?)\s\d{4}\.\d{4}', text)
      # use lookbehind and lookahead to remove last space
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)
      pl_unit_weight = re.findall('\d{3}\/\d{2}R.*?\s\d{4}\.\d{4}\s\d+\s(\d+\.\d+)\s', text)

      itens = list(zip(description, pl_unit_weight))

      dict_packing['invoice_number'] = invoice_number[0]
      dict_packing['container_num'] = container_num[0]
      dict_packing['itens'] = itens

      # verifica se já há invoice no BD
      invoice_items = Invoice.objects.filter(
                        invoice_number=dict_packing['invoice_number'])
      
      if not invoice_items:
            dict_packing['msg'] = f"ERRO: Invoice {dict_packing['invoice_number']} ainda não importada!"
      
      return dict_packing
      
def add_packing_data(self):

      lst_msg = []
      invoice_num = dict_packing['invoice_number']
      container_num = dict_packing['container_num']

      for item in dict_packing['itens']:
            pneu = item[0]
            weight = float(item[1])
            
            try:
                  Invoice.objects.filter(
                        invoice_number = invoice_num,
                        description = pneu).update(
                              pl_unit_weight=weight,
                              container_num=container_num)
            except:
                  lst_msg.append(f"""Pneu {pneu} não encontrado na Invoice 
                                  {invoice_num}. 
                                  Peso não foi atualizado!\n""")
      if len(lst_msg) == 0:
            return "Peso dos pneus atualizados com sucesso!"
      else:
            return lst_msg

def get_bill_data(bill): # Bill of Lading 1
     
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      bill_path = BASE_DIR + '/media/invoices/' + bill

      global dict_bill
      dict_bill = {}

      with pdfplumber.open(bill_path) as pdf: 
            text1 = pdf.pages[0].extract_text()
            text2 = pdf.pages[1].extract_text() # ATTACHED SHEET 
     
      bill_number = re.findall('Lading\sNumber\\n?\s?(.*?)[\\n\s]', text1)
      port = re.findall('delivery:\n(.*?),\sBRAZIL', text1)
      freight = re.findall('FREIGHT\sUSD\s(\d+,?\d+)\n', text1)

      freight = 0 if len(freight)==0 else freight[0] 

      dict_bill['bill_number'] = bill_number[0]
      dict_bill['port'] = port[0]
      dict_bill['freight'] = freight

      invoices = re.findall('CI-\d\d-\d{4}', text1)
      invoices = '>'.join(invoices)
      dict_bill['invoices'] = invoices
 
      qty = re.findall('pieces\s(\d+,?\d+)', text2)
      container = re.findall('pieces\s\d+,?\d+\s(.*?)\s', text2)
      net_weight = re.findall('pieces\s\d+,?\d+\s.*?\s(\d+,?\d+\.\d\d)', text2)
      gross_weight = re.findall('pieces\s\d+,?\d+\s.*?\s\d+,?\d+\.\d\d\s(\d+,?\d+\.\d\d)', text2)

      qty = tuple(v.replace(',', '') for v in qty)
      net_weight = tuple(v.replace(',', '') for v in net_weight)
      gross_weight = tuple(v.replace(',', '') for v in gross_weight)

      itens = list(zip(qty, container, net_weight, gross_weight))
      dict_bill['itens'] = itens
      
      return dict_bill
      
def add_bill_lading(self):
      
      # se bill_number já estiver no BD, não importa!
      bill_number_items = BillLading.objects.filter(
                              bill_number=dict_bill['bill_number'])
      
      if not bill_number_items:
            for item_ in dict_bill['itens']:

                  bill = BillLading(bill_number=dict_bill['bill_number'], 
                                    port=dict_bill['port'],
                                    freight=dict_bill['freight'],
                                    invoices=dict_bill['invoices'],
                                    quantity = int(item_[0]),
                                    container=item_[1],
                                    net_weight=float(item_[2]),
                                    gross_weight=float(item_[3]),
                                    )
                  bill.save()

            return "Dados salvos com sucesso!" 
      else:
            return f"Bill of Lading {dict_bill['bill_number']} já estava salva!"       


