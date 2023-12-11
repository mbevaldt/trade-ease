from .models import Ledger, ProForma, Invoice
from django.db.models import Sum
from datetime import datetime
import pandas as pd
from .forms import SaldoInicialForm

def get_df_merged_prof_invoice():
    
    proforma = ProForma.objects.all().values()
    df_proforma = pd.DataFrame.from_records(proforma)
    # ['id', 'pi_ref', 'other_ref', 'proforma_date', 'port_dest', 'num_item', 
    # 'brand', 'description', 'quantity', 'ncm', 'weight', 'unit_value']

    ledger = Ledger.objects.all().values()
    df_ledger = pd.DataFrame.from_records(ledger)
    # ['id', 'proforma_id', 'proforma_ref', 'proforma_date', 'invoice_id', 
    # 'invoice_ref', 'invoice_date', 'description', 'quantity_used']

    if df_proforma.empty or df_ledger.empty:
        return pd.DataFrame()

    df_prof_invoice = df_proforma.merge(df_ledger, 
                                    how='left', 
                                    left_on='id', 
                                    right_on='proforma_id')
    # ['id_x', 'pi_ref', 'other_ref', 'proforma_date_x', 'port_dest', 
    # 'num_item', 'brand', 'description_x', 'quantity', 'ncm', 'weight', 
    # 'unit_value', 'id_y', 'proforma_id', 'proforma_ref', 'proforma_date_y', 
    # 'invoice_id', 'invoice_ref', 'invoice_date', 'des
    
    return df_prof_invoice
