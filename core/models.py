from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal

class Establishment(models.Model):
    name = models.CharField("Nome do estabelecimento", max_length=150)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_establishments")
    address = models.CharField("Endereço", max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Membership(models.Model):
    OWNER = "owner"
    WORKER = "worker"
    ROLE_CHOICES = [(OWNER, "Proprietário"), (WORKER, "Trabalhador")]
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    active = models.BooleanField(default=True)
    phone = models.CharField("Telefone", max_length=25, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = [("establishment", "user")]
    def __str__(self):
        return f"{self.user} - {self.establishment} ({self.role})"

class Product(models.Model):
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=60, blank=True)
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    stock = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    min_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["name"]
    def __str__(self):
        return self.name

class CashSession(models.Model):
    INDIVIDUAL = "individual"
    SHARED = "shared"
    MODE_CHOICES = [(INDIVIDUAL, "Individual"), (SHARED, "Comum")]
    OPEN = "open"
    CLOSED = "closed"
    STATUS_CHOICES = [(OPEN, "Aberta"), (CLOSED, "Fechada")]
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name="cash_sessions")
    mode = models.CharField(max_length=12, choices=MODE_CHOICES)
    opened_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="opened_cash_sessions")
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OPEN)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="closed_cash_sessions")
    closed_at = models.DateTimeField(null=True, blank=True)
    counted_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    def __str__(self):
        return f"{self.establishment} - {self.get_mode_display()} - {self.opened_at:%d/%m/%Y}"

class Sale(models.Model):
    CASH = "cash"
    TRANSFER = "transfer"
    CARD = "card"
    OTHER = "other"
    PAYMENT_CHOICES = [(CASH, "Numerário"), (TRANSFER, "Transferência"), (CARD, "Cartão"), (OTHER, "Outro")]
    establishment = models.ForeignKey(Establishment, on_delete=models.PROTECT, related_name="sales")
    worker = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sales_made")
    cash_session = models.ForeignKey(CashSession, on_delete=models.PROTECT, related_name="sales")
    payment_method = models.CharField(max_length=12, choices=PAYMENT_CHOICES)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    voided = models.BooleanField(default=False)
    def __str__(self):
        return f"Venda #{self.pk} - {self.total}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    @property
    def subtotal(self):
        return self.quantity * self.unit_price

class Expense(models.Model):
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE, related_name="expenses")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    def __str__(self):
        return f"{self.description} - {self.amount}"

class StockMovement(models.Model):
    IN = "in"
    OUT = "out"
    LOSS = "loss"
    RETURN = "return"
    TYPES = [(IN, "Entrada"), (OUT, "Saída"), (LOSS, "Perda"), (RETURN, "Devolução")]
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    movement_type = models.CharField(max_length=10, choices=TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
