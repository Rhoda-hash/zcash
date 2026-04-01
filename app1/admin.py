from django.contrib import admin
from .models import Customer, Voucher, Transaction
# Register your models here.

admin.site.register(Customer)
admin.site.register([Voucher,Transaction])