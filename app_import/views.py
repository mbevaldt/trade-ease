import os
import pandas as pd
import mimetypes
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render, HttpResponse, Http404 
from django.template import loader
from django.urls import reverse
from .forms import InvoiceForm
from . import invoice, ledger, bill
from .models import Ledger, ProForma

def index(request):
    return render(request, 'index.html')

def upload_file(request, filetype):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)

        if form.is_valid():
            invoice.remove_invoices()
            form.save() #return HttpResponse('The invoice was saved')
            filename = request.FILES['file'].name.replace(' ','_')

            if filetype == 'invoice':
                invoice_data = invoice.get_invoice_data(filename)
                context = {'invoice_data' : invoice_data}
                return render(request, 'invoice.html', context)
            
            elif filetype == 'proforma':
                proforma_data = invoice.get_proforma_data(filename)
                context = {'proforma_data' : proforma_data}
                return render(request, 'proforma.html', context)
            
            elif filetype == 'packing':
                packing_data = invoice.get_packing_list_data(filename)
                context = {'packing_data' : packing_data}
                return render(request, 'packing_input.html', context)
            
            elif filetype == 'bill':
                bill_data = invoice.get_bill_data(filename)
                context = {'bill_data' : bill_data}
                return render(request, 'bill_lading.html', context)
    else:
        form = InvoiceForm()

    context = {'form' : form, 'filetype' : filetype}
    return render(request, 'upload.html', context)

# Define function to download file using template
def download_file(request, filename=''):
    if filename != '':
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = BASE_DIR + '/media/invoices/' + filename
        # Open the file for reading content
        path = open(filepath, 'rb')
        mime_type, _ = mimetypes.guess_type(filepath)
        response = HttpResponse(path, content_type=mime_type)
        # Set the HTTP header for sending to browser
        response['Content-Disposition'] = "attachment; filename=%s" % filename
        return response
    else:
        # Load the template
        return render(request, 'download.html')

def add_invoice_data(self):
    dict_invoice = invoice.add_invoice_data_bd(self)
    if str(dict_invoice)[0:4] == 'ERRO':
        template = loader.get_template('notification.html')
        return HttpResponse(template.render(context={'msg' : dict_invoice}))
    
    lst_msg = ledger.register_invoices_used(self, dict_invoice)
    template = loader.get_template('invoice_add.html')
    return HttpResponse(template.render(context={'lst_msg' : lst_msg}))
    
def add_proforma_data(self):
    msg = invoice.add_proforma_data_bd(self)
    #return HttpResponse(msg)
    template = loader.get_template('notification.html')
    return HttpResponse(template.render(context={'msg' : msg}))

def show_proforma_balance(self):
    df_proforma = ledger.get_proforma_balance(self)
    df_proforma = df_proforma[['pi_ref', 'description', 'qty', 'used', 'balance']]

    df_proforma['qty']  = df_proforma['qty'].astype(float).map('{:,.0f}'.format)
    df_proforma['used']  = df_proforma['used'].map('{:,.0f}'.format)
    df_proforma['balance']  = df_proforma['balance'].map('{:,.0f}'.format)

    template = loader.get_template('proforma_bd.html')
    context = {'df_proforma': df_proforma, }
    return HttpResponse(template.render(context))

def show_ledger(self):
    df_ledger = ledger.show_ledger_balance(self)
    template = loader.get_template('ledger.html')
    context = {'df_ledger': df_ledger, }
    return HttpResponse(template.render(context))

def update_saldo_ini(request, id):
    df_ledger_item = ledger.update_saldo_ini(id)
    template = loader.get_template('saldo_ini.html')
    context = {'df_ledger_item': df_ledger_item, }
    return HttpResponse(template.render(context, request))

def update_record_saldo_ini(request, id):
    msg = ledger.update_record_saldo_ini(request, id)
    return HttpResponseRedirect(reverse('show_ledger'))
    #return HttpResponse('Quantidade Atualizada')

def add_packing_data(self):
   msg = invoice.add_packing_data(self)
   template = loader.get_template('notification.html')
   return HttpResponse(template.render(context={'msg' : msg}))
   
def add_bill_lading(self):
    msg = invoice.add_bill_lading(self)
    template = loader.get_template('notification.html')
    return HttpResponse(template.render(context={'msg' : msg}))

def show_bill_excel(request):
    bills = bill.get_bills_imported()
    template = loader.get_template('bill_choose.html')
    context = {'bills': bills, }
    return HttpResponse(template.render(context, request))

def bill_check(request):
    bill_number = request.POST.get('bill_number')
    dict_msg = bill.check_bill_to_create_docs(bill_number)
    template = loader.get_template('bill_check.html')
    context = {'dict_msg': dict_msg, }
    return HttpResponse(template.render(context, request))

def export_to_excel(self, bill_number):
    file  = bill.export_to_excel(bill_number)
    file_path = os.path.join(settings.MEDIA_ROOT, file)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + file
            return response
    raise Http404
















