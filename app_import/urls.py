from django.urls import path
from . import views # can have others views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload_file/<str:filetype>/', views.upload_file, name='upload_file'),
    path('add_invoice_data', views.add_invoice_data, name='add_invoice_data'),
    path('add_proforma_data', views.add_proforma_data, name='add_proforma_data'),
    path('show_proforma_balance', views.show_proforma_balance, name='show_proforma_balance'),
    path('show_ledger', views.show_ledger, name='show_ledger'),
    path('update/<int:id>', views.update_saldo_ini, name='update_saldo_ini'),
    path('update/updaterecord/<int:id>', views.update_record_saldo_ini, name='update_record_saldo_ini'),
    path('add_packing_data', views.add_packing_data, name='add_packing_data'),
    path('add_bill_lading', views.add_bill_lading, name='add_bill_lading'),
    path('show_bill_excel', views.show_bill_excel, name='show_bill_excel'),
    path('bill_check', views.bill_check, name='bill_check'),
    path('export_to_excel/<str:bill_number>', views.export_to_excel, name='export_to_excel'),
    ]



















