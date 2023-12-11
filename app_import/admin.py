from django.contrib import admin
from .models import Invoice, ProForma, Ledger, BillLading

admin.site.register(Invoice)
admin.site.register(ProForma)
admin.site.register(Ledger)
admin.site.register(BillLading)