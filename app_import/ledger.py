from .models import Ledger, ProForma, Invoice
from django.db.models import Sum
from datetime import datetime
import pandas as pd

def get_proforma_balance(self, customer='None', invoices_excl='None'):

    df_proforma = pd.DataFrame.from_records(ProForma.objects.all().values())
    
    if customer != 'None':
        df_proforma = df_proforma.query('customer==@customer')

    df_proforma = (df_proforma.groupby(['id', 'pi_ref', 'proforma_date', 
                                        'size', 'customer'], as_index=False)
                                    .agg(qty=('quantity', 'sum')))
    
    df_proforma = df_proforma.sort_values(['proforma_date'], ascending=[True])

    used = (Ledger.objects.values('proforma_id')
                          .annotate(used=Sum('quantity_used')))
    df_used = pd.DataFrame(list(used))

    if df_proforma.empty:
        df_proforma = pd.DataFrame([[0, '0', None, '0', 0]], 
                               columns=['id', 'pi_ref', 'size', 'qty'])

    if df_used.empty:
        df_used = pd.DataFrame([[0, 0]], columns=['proforma_id', 'used'])

    df_proforma = df_proforma.merge(df_used, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')
 
    df_proforma.fillna(0, inplace = True) 
    df_proforma['balance'] = df_proforma['qty'] - df_proforma['used']
    df_proforma = df_proforma.sort_values(['customer', 'proforma_date', 'pi_ref', 'size'], 
                                          ascending = [True, True, True, True])
    #df_proforma = df_proforma.query('balance > 0')
    
    return df_proforma

def get_tyres_balance(self):

    df_proforma = get_proforma_balance(self)
    df_proforma = df_proforma[['pi_ref', 'proforma_date', 'size',
                           'qty', 'used', 'balance', 'customer']]

    df_proforma = (df_proforma.groupby(['customer', 'size'], as_index=False)
                                .agg(balance=('balance', 'sum')))
    
    df_proforma = df_proforma.sort_values(['customer', 'balance'], ascending = [True, False])
    #df_proforma = df_proforma.query('balance > 0')
    df_proforma['balance']  = df_proforma['balance'].map('{:,.0f}'.format)
    
    """df_proforma = (df_proforma.pivot_table(index=['size'],
                                        columns='customer',
                                        values='balance',
                                        aggfunc='sum')
                                        .rename_axis(columns=None)
                                        .reset_index())"""

    return df_proforma

def update_saldo_ini(id):

    proforma = ProForma.objects.all().values()
    df_proforma = pd.DataFrame.from_records(proforma)
    
    ledger = Ledger.objects.all().values()
    df_ledger = pd.DataFrame.from_records(ledger)

    if df_ledger.empty:
        df_ledger = pd.DataFrame(columns=['id', 'proforma_id', 'proforma_ref', 
                                          'proforma_date', 'invoice_id', 
                                          'invoice_ref', 'invoice_date', 
                                          'description', 'quantity_used'])
        
    df_proforma = df_proforma.merge(df_ledger, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')

    df_proforma = df_proforma[df_proforma['id_x'] == id]

    return df_proforma.iloc[0]

def update_record_saldo_ini(request, id):
    
    idx = request.POST['id_x']
    prof_date = ProForma.objects.filter(id=idx).values()
    prof_date =prof_date[0]['proforma_date']
    #prof_date = datetime.strptime(prof_date, '%b. %d, %Y').date()
    pi_ref = request.POST['pi_ref']
    description = request.POST.get('description_x')
    used = request.POST['quantity_used']
    customer = request.POST['customer']
    
    ledger = Ledger(customer = customer,
                    proforma_id = int(idx),
                    proforma_ref = pi_ref,
                    proforma_date = prof_date.strftime('%Y-%m-%d'),
                    invoice_id = 0,
                    invoice_ref = "CI-INICIAL",
                    invoice_date = prof_date.strftime('%Y-%m-%d'), #datetime.today().strftime('%Y-%m-%d'),
                    description = description,
                    size = description[0:9],
                    quantity_used = int(used))
    ledger.save()

    return "Quantidade Atualizada!"

def show_ledger_balance(self):

    proforma = ProForma.objects.all().values()
    df_proforma = pd.DataFrame.from_records(proforma)

    ledger = Ledger.objects.all().values()
    df_ledger = pd.DataFrame.from_records(ledger)

    if df_ledger.empty:
        df_ledger = pd.DataFrame(columns=['id', 'customer', 'proforma_id', 
                                          'proforma_ref', 'proforma_date', 
                                          'invoice_id', 'invoice_ref', 
                                          'invoice_date', 'size', 'quantity_used'])

    df_proforma = df_proforma.merge(df_ledger, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')
    
    df_proforma['invoice_ref'].fillna('Nenhuma', inplace = True)
    df_proforma['invoice_date'].fillna('Nenhuma', inplace = True)
    df_proforma['quantity_used'].fillna(0, inplace = True)

    df_proforma = df_proforma[['id_x', 'customer_x', 'pi_ref', 'proforma_date_x', 
                           'invoice_ref', 'invoice_date', 'size_x', 
                           'quantity', 'quantity_used']]

    df_proforma = df_proforma.sort_values(['customer_x', 'proforma_date_x', 'size_x', 'invoice_date'], 
                                          ascending=[True, True, True, True])
    
    df_proforma.reset_index(drop=True, inplace=True) # to keep ordered in .loc

    n = len(df_proforma)

    for i in range(1, n): # use .shitf()?
        cust = df_proforma.loc[i, 'customer_x'] == df_proforma.loc[i-1, 'customer_x']
        prof = df_proforma.loc[i, 'pi_ref'] == df_proforma.loc[i-1, 'pi_ref']
        desc = df_proforma.loc[i, 'size_x'] == df_proforma.loc[i-1, 'size_x']

        if cust and prof and desc: # se cliente, proforma e pneu não mudaram, altera saldo inicial
            df_proforma.loc[i, 'quantity'] = (df_proforma.loc[i-1, 'quantity'] 
                                                - df_proforma.loc[i-1, 'quantity_used'])
            
    df_proforma['balance'] = df_proforma['quantity'] - df_proforma['quantity_used']

    df_proforma['quantity']  = df_proforma['quantity'] .map('{:,.0f}'.format)
    df_proforma['quantity_used']  = df_proforma['quantity_used'] .map('{:,.0f}'.format)
    df_proforma['balance']  = df_proforma['balance'] .map('{:,.0f}'.format)
    
    return df_proforma

def register_invoices_used(self, invoice, customer):

    #global lst_msg 
    lst_msg = []
    dict_msg = {}

    df_balance = get_proforma_balance(self, customer) 
    df_balance = df_balance.query('balance > 0')
    # ['id', 'pi_ref', 'proforma_date', 'description', 'qty', 'used', 'balance'] 

    invoice_itens = Invoice.objects.filter(invoice_number=invoice)
    # ['id', 'invoice_number', 'invoice_date', 'description', 'quantity', 'unit_value']

    for item in invoice_itens:

        df_balance_item = df_balance.loc[df_balance['size']==item.size]
        total_balance = df_balance_item['balance'].sum() 
        quantity = item.quantity 

        dict_msg['invoice_number'] = item.invoice_number
        dict_msg['invoice_date'] = item.invoice_date
        dict_msg['size'] = item.size
        dict_msg['quantity'] = quantity  
        dict_msg['balance'] = f"{total_balance:,.0f}"      

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
            
            used_ledger = (Ledger.objects.filter(invoice_ref = item.invoice_number,
                                                size=item.description[0:9])
                                                .aggregate(Sum('quantity_used'))
                                                ['quantity_used__sum'])
            if not used_ledger:
                used_ledger = 0
            
            if used_ledger < item.quantity:
                ledger_new = Ledger(customer=customer,
                            proforma_id = df_balance_item['id'].iloc[0],
                            proforma_ref = df_balance_item['pi_ref'].iloc[0],
                            proforma_date = df_balance_item['proforma_date'].iloc[0],
                            invoice_id = item.id,
                            invoice_ref = item.invoice_number,
                            invoice_date = item.invoice_date,
                            description = item.description,
                            size = item.description[0:9],
                            quantity_used = alocate)
                ledger_new.save()
            
            # update df_balance if there is more to alocate
            if quantity > 0:
                df_balance = get_proforma_balance(self, customer)
                df_balance = df_balance.query('balance > 0')
                df_balance_item = df_balance.loc[df_balance['size']==item.size]
                total_balance = df_balance_item['balance'].sum() 

        #if proforma[-1] == '/': proforma = proforma[:-1]
        #dict_msg['msg'] = f'Alocado nas ProFormas {proforma}'
        #dict_msg['color'] = 'DarkGreen' 
        #lst_msg.append(dict_msg.copy())
    
    return lst_msg

