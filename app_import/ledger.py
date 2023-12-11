
from .models import Ledger, ProForma, Invoice
from django.db.models import Sum
from datetime import datetime
import pandas as pd
from .forms import SaldoInicialForm

def get_proforma_balance(self):

    proforma = (ProForma.objects.values('id', 'pi_ref', 'proforma_date', 'description')
                                .order_by('proforma_date')
                                .annotate(qty=Sum('quantity')))
    df_proforma = pd.DataFrame(list(proforma))

    used = (Ledger.objects.values('proforma_id')
                          .annotate(used=Sum('quantity_used')))
    df_used = pd.DataFrame(list(used))

    if df_proforma.empty:
        df_proforma = pd.DataFrame([[0, '0', None, '0', 0]], 
                               columns=['id', 'pi_ref', 'description', 'qty'])

    if df_used.empty:
        df_used = pd.DataFrame([[0, 0]], columns=['proforma_id', 'used'])

    df_proforma = df_proforma.merge(df_used, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')
 
    df_proforma.fillna(0, inplace = True) 
    df_proforma['balance'] = df_proforma['qty'] - df_proforma['used']
    df_proforma = df_proforma.query('balance > 0')

    return df_proforma

def update_saldo_ini(id):

    proforma = ProForma.objects.all().values()
    df_proforma = pd.DataFrame.from_records(proforma)
    # ['id', 'pi_ref', 'other_ref', 'proforma_date', 'port_dest', 'num_item', 'brand', 'description', 'quantity', 'ncm', 'weight', 'unit_value']

    ledger = Ledger.objects.all().values()
    df_ledger = pd.DataFrame.from_records(ledger)
    # ['id', 'proforma_id', 'proforma_ref', 'proforma_date', 'invoice_id', 'invoice_ref', 'invoice_date', 'description', 'quantity_used']

    df_proforma = df_proforma.merge(df_ledger, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')
    # ['id_x', 'pi_ref', 'other_ref', 'proforma_date_x', 'port_dest', 'num_item', 'brand', 'description_x', 'quantity', 'ncm', 'weight', 'unit_value', 'id_y', 'proforma_id', 'proforma_ref', 'proforma_date_y', 'invoice_id', 'invoice_ref', 'invoice_date', 'description_y', 'quantity_used']
    df_proforma = df_proforma[df_proforma['id_x'] == id]

    return df_proforma.iloc[0]

def update_record_saldo_ini(request, id):
    
    idx = request.POST['id_x']
    prof_date = request.POST['proforma_date_x']
    prof_date = datetime.strptime(prof_date, '%b. %d, %Y').date()
    pi_ref = request.POST['pi_ref']
    description = request.POST.get('description_x')
    used = request.POST['quantity_used']

    print(int(idx), pi_ref, prof_date.strftime('%Y-%m-%d'), description, used)
    # 7 None 2023-10-23 None 100

    ledger = Ledger(proforma_id = int(idx),
                    proforma_ref = pi_ref,
                    proforma_date = prof_date.strftime('%Y-%m-%d'),
                    invoice_id = 0,
                    invoice_ref = "CI-INICIAL",
                    invoice_date = datetime.today().strftime('%Y-%m-%d'),
                    description = description,
                    quantity_used = int(used))
    ledger.save()

    return "Quantidade Atualizada!"

def show_ledger_balance(self):

    proforma = ProForma.objects.all().values()
    df_proforma = pd.DataFrame.from_records(proforma)
    # ['id', 'pi_ref', 'other_ref', 'proforma_date', 'port_dest', 'num_item', 'brand', 'description', 'quantity', 'ncm', 'weight', 'unit_value']

    ledger = Ledger.objects.all().values()
    df_ledger = pd.DataFrame.from_records(ledger)
    # ['id', 'proforma_id', 'proforma_ref', 'proforma_date', 'invoice_id', 'invoice_ref', 'invoice_date', 'description', 'quantity_used']

    df_proforma = df_proforma.merge(df_ledger, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')
    # ['id_x', 'pi_ref', 'other_ref', 'proforma_date_x', 'port_dest', 'num_item', 'brand', 'description_x', 'quantity', 'ncm', 'weight', 'unit_value', 'id_y', 'proforma_id', 'proforma_ref', 'proforma_date_y', 'invoice_id', 'invoice_ref', 'invoice_date', 'description_y', 'quantity_used']
    
    df_proforma['invoice_ref'].fillna('Nenhuma', inplace = True)
    df_proforma['invoice_date'].fillna('Nenhuma', inplace = True)
    df_proforma['quantity_used'].fillna(0, inplace = True)

    df_proforma = df_proforma.sort_values(['proforma_date_x', 'description_x', 
                                           'invoice_date'], ascending=[True, True, True])
    
    df_proforma = df_proforma[['id_x', 'pi_ref', 'proforma_date_x', 
                           'invoice_ref', 'invoice_date', 'description_x', 
                           'quantity', 'quantity_used']]
    n = len(df_proforma)

    for i in range(1, n): # use .shitf()?
        prof = df_proforma.loc[i, 'pi_ref'] == df_proforma.loc[i-1, 'pi_ref']
        desc = df_proforma.loc[i, 'description_x'] == df_proforma.loc[i-1, 'description_x']

        if prof and desc: # se proforma e pneu não mudaram, altera saldo inicial
            df_proforma.loc[i, 'quantity'] = (df_proforma.loc[i-1, 'quantity'] 
                                                - df_proforma.loc[i-1, 'quantity_used'])

    df_proforma['balance'] = df_proforma['quantity'] - df_proforma['quantity_used']
    df_proforma['quantity']  = df_proforma['quantity'] .map('{:,.0f}'.format)
    df_proforma['quantity_used']  = df_proforma['quantity_used'] .map('{:,.0f}'.format)
    df_proforma['balance']  = df_proforma['balance'] .map('{:,.0f}'.format)
    
    return df_proforma

def register_invoices_used(self, dict_invoice):

    global lst_msg 
    lst_msg = []
    dict_msg = {}

    df_balance = get_proforma_balance(self) 
    # ['id', 'pi_ref', 'proforma_date', 'description', 'qty', 'used', 'balance'] 

    invoice_itens = Invoice.objects.filter(
                    invoice_number=dict_invoice['invoice_number'])
    # ['id', 'invoice_number', 'invoice_date', 'description', 'quantity', 'unit_value']

    for item in invoice_itens:

        df_balance_item = df_balance.loc[df_balance.description==item.description]
        total_balance = df_balance_item['balance'].sum() #4501
        quantity = item.quantity #167

        dict_msg['invoice_number'] = item.invoice_number
        dict_msg['invoice_date'] = item.invoice_date
        dict_msg['description'] = item.description
        dict_msg['quantity'] = quantity  
        dict_msg['balance'] = total_balance        

        if item.quantity > total_balance:
            dict_msg['msg'] = 'ERRO: não há saldo disponível, nada foi alocado!'
            dict_msg['color'] = 'red' 
            lst_msg.append(dict_msg.copy())
            continue
        
        proforma = ''
        while quantity > 0:

            balance = df_balance_item['balance'].iloc[0]
            alocate = min(quantity, balance) 
            quantity -= alocate 
            proforma += df_balance_item['pi_ref'].iloc[0] + '/'
 
            ledger = Ledger(proforma_id = df_balance_item['id'].iloc[0],
                            proforma_ref = df_balance_item['pi_ref'].iloc[0],
                            proforma_date = df_balance_item['proforma_date'].iloc[0],
                            invoice_id = item.id,
                            invoice_ref = item.invoice_number,
                            invoice_date = item.invoice_date,
                            description = item.description,
                            quantity_used = alocate)
            ledger.save()
            
            # update df_balance if there is more to alocate
            if quantity > 0:
                df_balance = get_proforma_balance(self)
                df_balance_item = df_balance.loc[df_balance.description==item.description]
                total_balance = df_balance_item['balance'].sum() 

        if proforma[-1] == '/': proforma = proforma[:-1]
        dict_msg['msg'] = f'Alocado nas ProFormas {proforma}'
        dict_msg['color'] = 'DarkGreen' 
        lst_msg.append(dict_msg.copy())
    
    return lst_msg

