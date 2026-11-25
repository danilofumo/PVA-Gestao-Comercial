from django.contrib import admin
from .models import Establishment, Membership, Product, Sale, SaleItem, CashSession, Expense, StockMovement

admin.site.register(Establishment)
admin.site.register(Membership)
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(CashSession)
admin.site.register(Expense)
admin.site.register(StockMovement)
