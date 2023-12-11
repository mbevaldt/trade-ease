from django import forms  
from .models import UploadInvoice

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = UploadInvoice
        fields = ['file']

class SaldoInicialForm(forms.ModelForm):
    id_x = forms.IntegerField()
    proforma_date_x = forms.DateField()
    pi_ref = forms.CharField(max_length=20)
    proforma_ref = forms.CharField(max_length=20)
    description_x = forms.CharField(max_length=100)
    quantity_used = forms.IntegerField()
