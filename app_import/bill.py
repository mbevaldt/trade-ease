import os
import pandas as pd
import openpyxl
from openpyxl.styles import Alignment, Border, Side
from .models import BillLading, Invoice, ProForma, Ledger

def get_bills_imported():
    bills = BillLading.objects.values('bill_number').distinct()
    #QuerySet [{'bill_number': 'RSLCMBITP285'}]
    return bills

def check_bill_to_create_docs(bill_number_selected):

    bill = BillLading.objects.filter(bill_number=bill_number_selected).values()
    invoices_bill = bill[0]['invoices']
    invoices_bill = invoices_bill.split('>')
    container_bill = [reg['container'] for reg in bill]

    invoices_bd = Invoice.objects.values('invoice_number').distinct()
    invoices_bd = '_'.join(v for dict in invoices_bd for v in dict.values())
    container_bd = Invoice.objects.values('container_num').distinct()
    container_bd = '_'.join(v for dict in container_bd for v in dict.values())

    invoice_records = Invoice.objects.filter(invoice_number__in=invoices_bill).values()
    df_invoice = pd.DataFrame.from_records(invoice_records) 
    df_invoice = df_invoice[df_invoice['pl_unit_weight']==0]
    lst_cont_pl = df_invoice['container_num'].unique().tolist()

    lst_inv=[]
    for inv in invoices_bill:
        lst_inv.append('Sim' if inv in invoices_bd else 'Não')
    
    lst_cont=[]
    for cont in container_bill:
        lst_cont.append('Sim' if cont in container_bd else 'Não')
    
    df_check_inv = pd.DataFrame()
    df_check_inv['ref_number'] = invoices_bill
    df_check_inv['type'] = 'Invoice'
    df_check_inv['bd'] = lst_inv

    df_check_cont = pd.DataFrame()
    df_check_cont['ref_number'] = container_bill
    df_check_cont['type'] = 'Container'
    df_check_cont['bd'] = lst_cont  

    df_check_pl = pd.DataFrame()
    df_check_pl['ref_number'] = lst_cont_pl
    df_check_pl['type'] = 'Container/PL Weight'
    df_check_pl['bd'] = ['Não'] * len(lst_cont_pl)

    df_check = df_check_inv.append(df_check_cont)
    df_check = df_check.append(df_check_pl)

    dict_msg={}
    df_check = df_check[df_check['bd'] == 'Não']
    erro = 'Sim' if 'Não' in df_check['bd'] else 'Não'
    dict_msg['erro'] = erro
    dict_msg['bill_number'] = bill_number_selected
    dict_msg['df'] = df_check # {k: v for k, v in dict_msg.items() if v == 'Não'}
    
    return dict_msg

def get_data_to_excel(bill_number_selected):
    
    bill = BillLading.objects.filter(bill_number=bill_number_selected).values()
    df_bill = pd.DataFrame.from_records(bill)
    invoices_bill = bill[0]['invoices'].split('>')

    invoice = Invoice.objects.filter(invoice_number__in=invoices_bill).values()
    df_invoice = pd.DataFrame.from_records(invoice) 

    ledger = Ledger.objects.filter(invoice_ref__in=invoices_bill).values()
    df_ledger = pd.DataFrame.from_records(ledger)
    pformas = df_ledger.proforma_ref.unique()

    proforma = ProForma.objects.filter(pi_ref__in=pformas).values()
    df_proforma = pd.DataFrame.from_records(proforma)
    brand = proforma[0]['brand'] 

    df_goods_excel = df_ledger.merge(df_invoice, 
                                 how='left', 
                                 left_on=['invoice_ref', 'description'],
                                 right_on=['invoice_number', 'description'])    

    df_goods_excel['brand'] = brand
    df_goods_excel['total_weight'] = df_goods_excel['quantity_used'] * df_goods_excel['pl_unit_weight']
    df_goods_excel['total_amount'] = df_goods_excel['quantity_used'] * df_goods_excel['unit_value']

    return df_bill, df_proforma, df_invoice, df_goods_excel


def export_to_excel(bill_number):

    CONT = 10 # number of blanks rows to list containers
    GOODS_CI = 20 # number of blanks rows to list goods in CI
    GOODS_PL = 50 # number of blanks rows to list goods in PL

    df_bill, df_proforma, df_invoice, df_goods_excel = get_data_to_excel(bill_number)

    dict_excel={}
    dict_excel['bill_number'] = bill_number
    dict_excel['min_dt_invoice'] = df_invoice['invoice_date'].min().strftime('%Y-%m-%d')
    dict_excel['proformas_used'] = ', '.join(df_proforma['pi_ref'].unique())
    dict_excel['invoices_bill'] = ', '.join(df_bill['invoices'][0].split('>'))
    dict_excel['containers_list'] = df_bill['container'].values.tolist() 
    dict_excel['qtd_cont'] = len(dict_excel['containers_list'])
    dict_excel['net_weight'] = f"{df_goods_excel['total_weight'].sum():,.2f}" 
    dict_excel['total_pieces'] = f"{df_bill['quantity'].sum():,.0f}" 
    dict_excel['port_dest'] = df_bill.loc[0, 'port']
    dict_excel['ci_description_goods'] = 'function'
    dict_excel['pl_description_goods'] = 'function'

    model_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/media/CI-PL.xlsx'
    wb = openpyxl.load_workbook(model_path)
    
    for ws in wb.worksheets:
        for row in ws.iter_rows(min_row=1, max_row=150, min_col=1, max_col=15): 
            for cell in row:
                if cell.value is not None:
                    for key, val in dict_excel.items(): 
                        if key in str(cell.value): # key may be a substring of a cell value
                            
                            if key == 'containers_list':
                                _write_container_list(dict_excel, ws, cell, CONT)
                            
                            if key == 'ci_description_goods':
                                _write_goods_list_ci(df_goods_excel, ws, cell, GOODS_CI)
                            
                            if key == 'pl_description_goods':
                                _write_goods_list_pl(df_goods_excel, ws, cell, GOODS_PL)

                            else:                  
                                cell.value = str(cell.value).replace(key, str(val))  

                            continue

    wb.save(f'{model_path[0:-5]}-{bill_number}.xlsx')
    wb.close()

    return f'CI-PL-{bill_number}.xlsx'


def _write_container_list(dict_excel, ws, cell, CONT):
    
    c = len(dict_excel['containers_list']) 

    for r in range(CONT+1): # blanks row in the model
        if r < c: # write container number to cell
            ws.cell(row=(cell.row + r), 
                    column=cell.column, 
                    value=dict_excel['containers_list'][r])
        else:
            if (r>=5 and r>=c): # hide blanks rows
                ws.row_dimensions[cell.row + r].hidden = True

def _write_goods_list_ci(df_goods_excel, ws, cell, GOODS_CI):

    df_goods_ci = df_goods_excel[['brand',  'proforma_ref', 'description', 
                                  'quantity_used', 'unit_value', 'total_amount']]
    
    df_goods_ci = (df_goods_ci.groupby(['brand', 'proforma_ref', 'description'], as_index=False)
                                .agg(quantity_used=('quantity_used', 'sum'), 
                                     unit_value=('unit_value', 'mean'),
                                     total_amount=('total_amount', 'sum')))
    
    df_goods_ci = df_goods_ci.sort_values(['proforma_ref', 'description'],
                                          ascending = [True, True])
    n = df_goods_ci.shape[0]
    p = df_goods_ci['proforma_ref'].unique().size
    n = n + p # adiciona linhas que vai conter apenas o numero da proforma
    df = 0 # controla a linha do dataframe que está sendo escrita
    proforma = True # controla quando deve escrever só o numero da proforma

    for r in range(GOODS_CI+1): # blanks row in the model
        if r < n: # write list of goods to cell

            if proforma and df_goods_ci.iloc[df,1] != df_goods_ci.iloc[df-1,1]:
                # se mudou proforma, escreve apenas o numero da proforma
                
                #for col in range(7):
                #    ws.cell(row=(cell.row + r), column=(col + 1)).border = Border(top=Side(style='thin')) 

                ws.cell(row=(cell.row + r), column=(cell.column + 1)).alignment = Alignment(horizontal='left')
                ws.cell(row=(cell.row + r), column=(cell.column + 1), value = df_goods_ci.iloc[df,1])
                ws.cell(row=(cell.row + r), column=(cell.column), value = '')
                ws.cell(row=(cell.row + r), column=(cell.column + 7), value = '')
                proforma = False

            else:
                ws.cell(row=(cell.row + r), column=(cell.column), value = df_goods_ci.iloc[df,0])
                ws.cell(row=(cell.row + r), column=(cell.column + 1), value = df_goods_ci.iloc[df,2])
                ws.cell(row=(cell.row + r), column=(cell.column + 5), value = df_goods_ci.iloc[df,3])
                ws.cell(row=(cell.row + r), column=(cell.column + 6), value = df_goods_ci.iloc[df,4])
                proforma = True
                df += 1
                
        else:# hide blanks rows
            ws.row_dimensions[cell.row + r].hidden = True

def _write_goods_list_pl(df_goods_excel, ws, cell, GOODS_PL):

    df_goods_pl = df_goods_excel[['brand', 'container_num',  'proforma_ref', 
                                  'description', 'quantity_used', 'total_weight']]
    
    df_goods_pl = (df_goods_pl.groupby(['brand', 'container_num', 'proforma_ref', 
                                        'description'], as_index=False)
                                .agg(quantity_used=('quantity_used', 'sum'), 
                                     total_weight=('total_weight', 'sum')))
    
    df_goods_pl = df_goods_pl.sort_values(['container_num', 'proforma_ref', 'description'],
                                          ascending = [True, True, True])
    n = df_goods_pl.shape[0]

    for r in range(GOODS_PL+1): # blanks row in the model

        if r < n: # write list of goods to cell
            for c in [0, 1, 2, 3, 5, 6]: # collumn 4 is merged
                col = c if c<5 else c - 1 

                ws.cell(row=(cell.row + r), 
                        column=(cell.column + c), 
                        value = df_goods_pl.iloc[r,col])
                
        else:# hide blanks rows
            ws.row_dimensions[cell.row + r].hidden = True