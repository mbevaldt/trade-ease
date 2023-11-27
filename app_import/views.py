import os
import mimetypes
from django.http import Http404
from django.conf import settings
from django.shortcuts import render, HttpResponse
from django.template import loader
from .forms import InvoiceForm
from . import invoice


def index(request):
    return render(request, 'index.html')

def upload_file(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST, request.FILES)

        if form.is_valid():
            invoice.remove_invoices()
            form.save() #return HttpResponse('The invoice was saved')
            filename = request.FILES['file'].name.replace(' ','_')
            invoice_data = invoice.get_invoice_data(filename)
            context = {'invoice_data' : invoice_data}
            return render(request, 'download.html', context)
    else:
        form = InvoiceForm()

    context = {'form':form,}
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
    











































