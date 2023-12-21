import os
import re
import glob
#import fitz # pymupdf 
import pdfplumber
from pypdf import PdfReader
from .models import Invoice, ProForma, BillLading

print(pdfplumber.__version__)

def remove_invoices():
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
      files = glob.glob(BASE_DIR + '/media/invoices/*.pdf')
      for f in files:
            os.remove(f)

def get_invoice_data(invoice):

      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      invoice = re.sub('[()]', '', invoice)
      invoice_path = BASE_DIR + '/media/invoices/' + invoice

      reader = PdfReader(invoice_path)
      page = reader.pages[0]
      text = page.extract_text()
      text = re.sub('[Ss]ample([\S\s]*)Grand\sTotal', 'Grand Total', text)

      global dict_invoice 
      dict_invoice = {}
      
      invoice_number = fill_list(re.findall('(CI-\d\d-\d{4}-?\d?\d?)', text))
      invoice_date = fill_list(re.findall('(\d\d\.\d\d\.\d{4})', text))
      container_num = fill_list(re.findall('(\w{4}\d{7})\s[Cc]ontainer', text))
      port_dest = fill_list(re.findall('[Dd]ischarge\s?-?\s?(.*?),?\sBrazil', text))
      qtd_invoice = fill_list(re.findall('Grand\sTotal\s([\d,\.]+)', text))
      tot_invoice = fill_list(re.findall('Grand\sTotal\s[\d,\.]+\s([\d,\.]+)', text))

      # split date, reverse and join '-' to get the format needed
      invoice_date = '-'.join(invoice_date[0].split('.')[::-1])

      dict_invoice['invoice_number'] = invoice_number[0]
      dict_invoice['invoice_date'] = invoice_date
      dict_invoice['container_num'] = container_num[0]
      dict_invoice['qtd_invoice'] = qtd_invoice[0]
      dict_invoice['tot_invoice'] = tot_invoice[0]

      port = port_dest[0]
      customer = 'CATARINENSE' if 'ITAPOA' in port.upper() else 'CABEDELO'
      dict_invoice['customer'] = customer
      dict_invoice['port_dest'] = port

      # use lookbehind and lookahead to remove last space
      description = fill_list(re.findall('(\d{3}\/\d\dR.*?)\s+[\d,\.]+\s+[\d,\.]+', text))
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)

      size = fill_list(re.findall('(\d{3}\/\d\dR\d{2})', text))
      quantity = fill_list(re.findall('\d{3}\/\d\dR.*?\s+([\d,\.]+)\s+[\d,\.]+', text))
      quantity = tuple(q.replace(',', '') for q in quantity)
      unit_value = fill_list(re.findall('\d{3}\/\d\dR.*?\s+[\d,\.]+\s+([\d,\.]+)', text))
      
      # check if elements in a list are equal
      # if([L[0]]*len(L) == L): True
      
      qtd, vlr = (0, 0)
      for q, u in zip(quantity, unit_value):
            qtd += int(q)
            vlr += int(q) * float(u)

      dict_invoice['qtd_tot_calc'] = f"{qtd:,.0f}"
      dict_invoice['vlr_tot_calc'] = f"{round(vlr, 2):,.2f}"
      dict_invoice['color_qtd'] = '#90EE90' if qtd_invoice[0] == f"{qtd:,.0f}" else 'red'
      dict_invoice['color_vlr'] = '#90EE90' if tot_invoice[0] == f"{vlr:,.2f}" else 'red'
      
      num_item = range(1, len(description)+1)
      itens = list(zip(num_item, description, size, quantity, unit_value))
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
                                    customer=dict_invoice['customer'],
                                    num_item = item_[0],
                                    description=item_[1],
                                    size=item_[2],
                                    quantity=item_[3],
                                    unit_value=float(item_[4]),
                                    )
                  invoice.save()

            return "Dados salvos com sucesso!" 
      else:
            return f"ERRO: Invoice {dict_invoice['invoice_number']} já estava salva!" 

def get_proforma_data(proforma):

      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      proforma = re.sub('[()]', '', proforma)
      proforma_path = BASE_DIR + '/media/invoices/' + proforma

      with pdfplumber.open(proforma_path) as pdf: 
            text = pdf.pages[0].extract_text()

      global dict_proforma 
      dict_proforma = {}
      
      port_dest = fill_list(re.findall('DISCHARGE\sPORT\s:\s(.*?),?\sBRAZIL', text))
      pi_ref = fill_list(re.findall('PI REF\s#\s(.*?)\\n', text))
      other_ref = fill_list(re.findall('OTHER\sREFERENCE\s:\s(\d+)', text))
      proforma_date = fill_list(re.findall('(\d\d\.\d\d\.\d{4})', text))
      
      # split date, reverse and join '-' to get the format needed
      proforma_date = '-'.join(proforma_date[0].split('.')[::-1])

      port = port_dest[0]
      customer = 'CATARINENSE' if 'ITAPOA' in port.upper() else 'CABEDELO'
      dict_proforma['customer'] = customer
      dict_proforma['port_dest'] = port

      dict_proforma['pi_ref'] = pi_ref[0]
      dict_proforma['other_ref'] = other_ref[0]
      dict_proforma['proforma_date'] = proforma_date

      # use lookbehind and lookahead to remove last space
      description = fill_list(re.findall('(\d{3}\/\d{2}R.*?\d{2}\s?[TH])', text))
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)
      
      size = fill_list(re.findall('(\d{3}\/\d{2}R\d{2})', text))
      brand = fill_list(re.findall('(FERENTINO)\s\d{3}\/\d{2}R', text))
      quantity = fill_list(re.findall('\d{3}\/\d{2}R.*?([\d,\.]+)\sPCS', text))
      ncm = fill_list(re.findall('\d{3}\/\d{2}R.*?[\d,\.]+\sPCS\s(\d{4}\.\d{2}\.\d{2})', text))
      weight = fill_list(re.findall('\d{4}\.\d{2}\.\d{2}\s(\d+[.,]*\d+)', text))
      unit_value = fill_list(re.findall('\d{4}\.\d{2}\.\d{2}\s[\d,\.]+[\S\s]*?[\d,\.]+\s([\d,\.]+)', text))
      
      quantity = tuple(v.replace(',', '') for v in quantity)
      weight = tuple(v.replace(',', '.') for v in weight)
      unit_value = tuple(v.replace(',', '.') for v in unit_value)

      qtd, vlr = (0, 0)
      for q, u in zip(quantity, unit_value):
            qtd += int(q)
            vlr += int(q) * float(u)
      dict_proforma['qtd_tot'] = f"{qtd:,.0f}"
      dict_proforma['vlr_tot'] = f"{round(vlr, 2):,.2f}"

      num_item = range(1, len(description)+1)
      itens = list(zip(num_item, brand, description, size, quantity, 
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
                                    customer=dict_proforma['customer'],
                                    num_item = item_[0],
                                    brand=item_[1],
                                    description=item_[2],
                                    size=item_[3],
                                    quantity=float(item_[4]),
                                    ncm=item_[5],
                                    weight=float(item_[6]),
                                    unit_value=float(item_[7]),
                                    )
                  proforma.save()

            return "Dados salvos com sucesso!" 
      else:
            return f"Pro Forma {dict_proforma['pi_ref']} já estava salva!" 

def get_packing_list_data(packing_list):
      
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      packing_list = re.sub('[()]', '', packing_list)
      packing_path = BASE_DIR + '/media/invoices/' + packing_list

      global dict_packing
      dict_packing = {}

      with pdfplumber.open(packing_path) as pdf: 
            text = pdf.pages[0].extract_text()
      text = re.sub('Sample([\S\s]*)Total', 'Total', text, flags=re.IGNORECASE)
      
      invoice_number = fill_list(re.findall('(CI-\d\d-\d{4}-?\d?\d?)', text))
      container_num = fill_list(re.findall('[Cc]ontainer\s[Nn]umber\s(.*?)\\n', text)) 
      port_dest = fill_list(re.findall('[Ss]hipped\s[Tt]o\s(.*?)\s', text))

      port = port_dest[0]
      customer = 'CATARINENSE' if 'ITAPOA' in port.upper() else 'CABEDELO'
      dict_packing['customer'] = customer
      dict_packing['port_dest'] = port

      # use lookbehind and lookahead to remove last space
      description = fill_list(re.findall('(\d{3}\/\d{2}R.*?)\s\d{4}\.\d{4}', text))
      description = tuple(re.sub(r'(?<=\d{2})\s(?=[TH]$)', '', desc) for desc in description)
      size = fill_list(re.findall('(\d{3}\/\d{2}R\d{2})', text))
      qty = fill_list(re.findall('\d{3}\/\d{2}R.*?\s\d{4}\.\d{4}\s([\d,\.]+)\s\d+', text))
      qty = tuple(v.replace(',', '') for v in qty)
      pl_unit_weight = fill_list(re.findall('\d{3}\/\d{2}R.*?\s\d{4}\.\d{4}\s[\d,\.]+\s([\d,\.]+)', text))

      itens = list(zip(description, size, qty, pl_unit_weight))

      dict_packing['invoice_number'] = invoice_number[0]
      dict_packing['container_num'] = container_num[0]
      dict_packing['itens'] = itens

      # verifica se já há invoice no BD
      invoice_items = Invoice.objects.filter(
                        invoice_number__contains=dict_packing['invoice_number'])
      
      if not invoice_items:
            dict_packing['msg'] = f"ERRO: Invoice {dict_packing['invoice_number']} ainda não importada!"
      
      return dict_packing
      
def add_packing_data(self):

      lst_msg = []
      invoice_num = dict_packing['invoice_number'][0:10] # base number
      container_num = dict_packing['container_num']
      customer = dict_packing['customer']

      for item in dict_packing['itens']:
            size=item[1],
            qty = item[2]
            weight = float(item[3])
            
            invoice_item = Invoice.objects.filter(
                              customer=customer,
                              invoice_number__contains=invoice_num,
                              size=size[0],
                              quantity=qty)
            
            if invoice_item:
                  invoice_item.update(
                              pl_unit_weight=weight,
                              container_num=container_num)
            else:
                  lst_msg.append(f"""Pneu {size} não encontrado na Invoice 
                              {invoice_num}. Peso não foi atualizado!\n""")
      
      if len(lst_msg) == 0:
            return "Peso dos pneus atualizados com sucesso!"
      else:
            return lst_msg

def get_bill_data1(bill): # Bill of Lading 1
     
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      bill = re.sub('[()]', '', bill)
      bill_path = BASE_DIR + '/media/invoices/' + bill

      global dict_bill
      dict_bill = {}
      
      with pdfplumber.open(bill_path) as pdf: 
            text1 = pdf.pages[0].extract_text()
            text2 = pdf.pages[1].extract_text() # ATTACHED SHEET 
      
      reader = PdfReader(bill_path)
      page = reader.pages[0]
      text = page.extract_text()
      invoices = fill_list(re.findall('CI\s?-\s?\d\d\s?-\s?\d{4}', text))
      invoices = ';'.join(invoices)
      invoices = re.sub('\s', '', invoices)
      dict_bill['invoices'] = invoices

      bill_number = fill_list(re.findall('[Ll]ading\s[Nn]umber[\S\s]*?(RSL.*?)\s', text1))
      vessel_name = fill_list(re.findall('[Ll]oading[\S\s]*?(MV.*)\sCOLOMBO', text1))
      port = fill_list(re.findall('(\w+),?\sBRAZIL', text1)) #'delivery:[\S\s]*?(\w+),\sBRAZIL'
      
      port = port[0]
      customer = 'CATARINENSE' if 'ITAPOA' in port.upper() else 'CABEDELO'
      dict_bill['customer'] = customer
      dict_bill['port_dest'] = port
      
      freight = re.findall('FREIGHT\sUSD\s([\d+,\.]+)', text1)
      freight = 0 if len(freight)==0 else freight[0] 
      
      dict_bill['bill_number'] = bill_number[0]
      dict_bill['vessel_name'] = vessel_name[0]
      dict_bill['freight'] = freight
      
      qty = fill_list(re.findall('[Pp]ieces\s(\d+,?\d+)', text2))
      container = fill_list(re.findall('[Pp]ieces\s[\d+,\.]+\s(.*?)\s', text2))
      net_weight = fill_list(re.findall('[Pp]ieces\s[\d+,\.]+\s.*?\s(\d+,?\d+\.\d\d)', text2))
      gross_weight = fill_list(re.findall('[Pp]ieces\s[\d+,\.]+\s.*?\s\d+,?\d+\.\d\d\s(\d+,?\d+\.\d\d)', text2))
      
      qty = tuple(v.replace(',', '') for v in qty)
      net_weight = tuple(v.replace(',', '') for v in net_weight)
      gross_weight = tuple(v.replace(',', '') for v in gross_weight)

      itens = list(zip(qty, container, net_weight, gross_weight))
      dict_bill['itens'] = itens
      
      return dict_bill

def get_bill_data2(bill): # Bill of Lading 2: update freight
     
      BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
      bill = re.sub('[()]', '', bill)
      bill_path = BASE_DIR + '/media/invoices/' + bill

      with pdfplumber.open(bill_path) as pdf: 
            text = pdf.pages[0].extract_text()

      bill_number = re.findall('[Ll]ading\s[Nn]umber[\S\s]*(RSL.*?)\s', text)
      freight = re.findall('FREIGHT\sUSD\s(\d+,?\d+)\n', text)
      freight = 0 if len(freight)==0 else freight[0] 

      port = re.findall('delivery:\n(.*?),\sBRAZIL', text)
      port = port[0]
      customer = 'CATARINENSE' if 'ITAPOA' in port.upper() else 'CABEDELO'

      BillLading.objects.filter(
                  customer=customer,
                  bill_number=bill_number[0]).update(freight=freight)
      
      return 'Valor do Frete atualizado com sucesso!'

def add_bill_lading(self):
      
      # se bill_number já estiver no BD, não importa!
      bill_number_items = BillLading.objects.filter(
                              bill_number=dict_bill['bill_number'])
      
      if not bill_number_items:
            for item_ in dict_bill['itens']:

                  bill = BillLading(bill_number=dict_bill['bill_number'], 
                                    port=dict_bill['port_dest'],
                                    vessel_name=dict_bill['vessel_name'],
                                    customer=dict_bill['customer'],
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

def fill_list(list):
      return list if list else ['None']



