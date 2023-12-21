import os
import mimetypes
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render, HttpResponse, Http404 
from django.template import loader
from django.urls import reverse
from .forms import InvoiceForm
from . import ledger, bill, funcs, pdfs
from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, 'index.html')

def upload_file(request, filetype):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)

        if form.is_valid():
            pdfs.remove_invoices()
            form.save() #return HttpResponse('The invoice was saved')
            filename = request.FILES['file'].name.replace(' ','_')

            if filetype == 'invoice':
                invoice_data = pdfs.get_invoice_data(filename)
                context = {'invoice_data' : invoice_data}
                return render(request, 'invoice.html', context)
            
            elif filetype == 'proforma':
                proforma_data = pdfs.get_proforma_data(filename)
                context = {'proforma_data' : proforma_data}
                return render(request, 'proforma.html', context)
            
            elif filetype == 'packing':
                packing_data = pdfs.get_packing_list_data(filename)
                context = {'packing_data' : packing_data}
                return render(request, 'packing_input.html', context)
            
            elif filetype == 'bill1':
                bill_data = pdfs.get_bill_data1(filename)
                context = {'bill_data' : bill_data}
                return render(request, 'bill_lading1.html', context)
            
            elif filetype == 'bill2':
                msg = pdfs.get_bill_data2(filename)
                template = loader.get_template('notification.html')
                return HttpResponse(template.render(context={'msg' : msg}))
                
    else:
        form = InvoiceForm()

    context = {'form' : form, 'filetype' : filetype}
    return render(request, 'upload.html', context)

@login_required
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
    msg = pdfs.add_invoice_data_bd(self)
    template = loader.get_template('notification.html')
    return HttpResponse(template.render(context={'msg' : msg}))
    
def add_proforma_data(self):
    msg = pdfs.add_proforma_data_bd(self)
    #return HttpResponse(msg)
    template = loader.get_template('notification.html')
    return HttpResponse(template.render(context={'msg' : msg}))

@login_required
def show_proforma_balance(self):
    df_proforma = ledger.get_proforma_balance(self)
    df_proforma = df_proforma.query('balance > 0')
    df_proforma = df_proforma[['customer', 'pi_ref', 'proforma_date', 'size', 
                               'qty', 'used', 'balance']]

    df_proforma['qty']  = df_proforma['qty'].astype(float).map('{:,.0f}'.format)
    df_proforma['used']  = df_proforma['used'].map('{:,.0f}'.format)
    df_proforma['balance']  = df_proforma['balance'].map('{:,.0f}'.format)

    template = loader.get_template('proforma_bd.html')
    context = {'df_proforma': df_proforma, }
    return HttpResponse(template.render(context))

@login_required
def show_tyres_balance(self):
    df_proforma = ledger.get_tyres_balance(self)
    template = loader.get_template('tyres_balance.html')
    context = {'df_proforma': df_proforma, }
    return HttpResponse(template.render(context))

@login_required
def show_ledger(self):
    df_ledger = ledger.show_ledger_balance(self)
    template = loader.get_template('ledger.html')
    context = {'df_ledger': df_ledger, }
    return HttpResponse(template.render(context))

@login_required
def update_saldo_ini(request, id):
    df_ledger_item = ledger.update_saldo_ini(id)
    template = loader.get_template('saldo_ini.html')
    context = {'df_ledger_item': df_ledger_item, }
    return HttpResponse(template.render(context, request))

@login_required
def update_record_saldo_ini(request, id):
    msg = ledger.update_record_saldo_ini(request, id)
    return HttpResponseRedirect(reverse('show_ledger'))
    #return HttpResponse('Quantidade Atualizada')

def add_packing_data(self):
   msg = pdfs.add_packing_data(self)
   #return HttpResponseRedirect(reverse('index'))
   template = loader.get_template('notification.html')
   return HttpResponse(template.render(context={'msg' : msg}))
   
def add_bill_lading(self):
    msg = pdfs.add_bill_lading(self)
    template = loader.get_template('notification.html')
    return HttpResponse(template.render(context={'msg' : msg}))

@login_required
def show_bill_excel(request):
    bills = bill.get_bills_imported()
    template = loader.get_template('bill_choose.html')
    context = {'bills': bills, }
    return HttpResponse(template.render(context, request))

@login_required
def bill_check(request):
    bill_number = request.POST.get('bill_number')
    if 'Selecione' in bill_number: 
        return HttpResponseRedirect(reverse('index'))
    
    dict_msg = bill.check_bill_to_create_docs(bill_number)
    template = loader.get_template('bill_check.html')
    context = {'dict_msg': dict_msg, }
    return HttpResponse(template.render(context, request))

@login_required
def export_to_excel(self, bill_number):
    file  = bill.export_to_excel(bill_number)
    file_path = os.path.join(settings.MEDIA_ROOT, file)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + file
            return response
    raise Http404

@login_required
def invoice_mes(self):
    funcs.make_plotly_invoice()
    return HttpResponseRedirect(reverse('index'))

@login_required
def export_all_excel(self):
    file = funcs.export_all_excel(self)
    file_path = os.path.join(settings.MEDIA_ROOT, file)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + file
            return response
    raise Http404    

@login_required
def show_report_excel(self):
    file = funcs.show_report_excel(self)
    file_path = os.path.join(settings.MEDIA_ROOT, file)
    
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + file
            return response
    raise Http404    








