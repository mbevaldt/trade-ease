from django.contrib import admin
from .models import Invoice, ProForma, Ledger, BillLading

admin.site.site_title = 'TradeEase BD'
admin.site.site_header = 'TradeEase Database'
admin.site.index_title = 'Welcome to TradeEase'
num_pages = 20

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'invoice_date', 'container_num', 'quantity', 'size', 'customer')
    search_fields = ('invoice_number', 'container_num', 'size')
    #list_editable = ['invoice_date', 'container_num']
    list_filter = ('customer', 'size', 'invoice_number')
    list_per_page = num_pages
    
@admin.register(ProForma)
class ProFormaAdmin(admin.ModelAdmin):
    list_display = ('pi_ref', 'proforma_date', 'quantity', 'size', 'customer')
    search_fields = ('pi_ref', 'size')
    list_filter = ('customer', 'size', 'pi_ref')
    list_per_page = num_pages

@admin.register(Ledger)
class LedgerAdmin(admin.ModelAdmin):
    list_display = ('proforma_ref', 'invoice_ref', 'size', 'quantity_used', 'customer')
    search_fields = ('proforma_ref', 'invoice_ref', 'size')
    list_filter = ('customer', 'size', 'proforma_ref', 'invoice_ref')
    list_per_page = num_pages

@admin.register(BillLading)
class BillLadingAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'invoices', 'quantity', 'container', 'customer')
    search_fields = ('bill_number', 'invoices', 'container')
    list_filter = ('customer', 'bill_number', 'container')
    list_per_page = num_pages













