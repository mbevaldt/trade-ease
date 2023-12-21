from django.db import models
import datetime
from django.utils.html import format_html

class UploadInvoice(models.Model):
    file = models.FileField(upload_to='invoices/')

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=20) #, primary_key=True) 
    invoice_date = models.DateField()
    container_num = models.CharField(max_length=20)
    port_dest = models.CharField(max_length=20)
    customer = models.CharField(max_length=20)
    #invoice_number = models.ForeignKey(InvoiceMaster, on_delete=models.CASCADE)
    num_item = models.IntegerField()
    description = models.CharField(max_length=100) 
    size = models.CharField(max_length=20) 
    quantity = models.IntegerField() #(null=True)
    unit_value = models.DecimalField(max_digits=5, decimal_places=2)
    #field comes from packing list from ferentino
    pl_unit_weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def year(self):
        year = datetime.datetime.strftime(self.invoice_date, "%Y") # January
        return format_html('<b>%s</b>' % (year))

    def __str__(self):
        return (f"""{self.invoice_number} at {self.invoice_date} with 
                {self.quantity} {self.size} to {self.customer}""")

class ProForma(models.Model):
    pi_ref = models.CharField(max_length=20) #, primary_key=True)
    other_ref = models.CharField(max_length=10)
    proforma_date = models.DateField()
    port_dest = models.CharField(max_length=20)
    customer = models.CharField(max_length=20)
    #pi_ref = models.ForeignKey(ProFormaMaster, on_delete=models.CASCADE)
    num_item = models.IntegerField()
    brand = models.CharField(max_length=20)
    description = models.CharField(max_length=100) 
    size = models.CharField(max_length=20) 
    quantity = models.IntegerField() #(null=True)
    ncm = models.CharField(max_length=20)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    unit_value = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return (f"""{self.pi_ref} at {self.proforma_date} with 
                {self.quantity} {self.size} to {self.customer}""")

class Ledger(models.Model):
    customer = models.CharField(max_length=20)
    proforma_id = models.IntegerField()
    proforma_ref = models.CharField(max_length=20) 
    proforma_date = models.DateField()

    invoice_id = models.IntegerField()
    invoice_ref = models.CharField(max_length=20) 
    invoice_date = models.DateField()

    description = models.CharField(max_length=100)
    size = models.CharField(max_length=20) 
    quantity_used = models.IntegerField()

    def __str__(self):
        return (f"""{self.invoice_ref} used {self.quantity_used} 
                {self.size} from {self.proforma_ref} to {self.customer}""")
    
class BillLading(models.Model):
    bill_number = models.CharField(max_length=20) 
    port = models.CharField(max_length=20) 
    vessel_name = models.CharField(max_length=30)
    customer = models.CharField(max_length=20)
    freight = models.DecimalField(max_digits=5, decimal_places=0)
    invoices = models.CharField(max_length=100) 
    quantity = models.IntegerField()
    container = models.CharField(max_length=20) 
    net_weight = models.FloatField()
    gross_weight = models.FloatField()

    def __str__(self):
        return (f"""{self.bill_number} with {self.quantity} 
                weight {self.net_weight} to {self.customer}""")


#python manage.py makemigrations app_import
#python manage.py migrate

"""
python manage.py shell
from app_import.models import BillLading
BillLading.objects.all().delete()
"""