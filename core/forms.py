from django import forms
from django.contrib.auth.models import User
from .models import Establishment, Product, CashSession, Expense

class RegisterForm(forms.Form):
    establishment = forms.CharField(label="Nome do estabelecimento", max_length=150)
    owner_name = forms.CharField(label="Nome do proprietário", max_length=150)
    username = forms.CharField(label="Utilizador", max_length=150)
    password = forms.CharField(label="Palavra-passe", widget=forms.PasswordInput, min_length=8)
    address = forms.CharField(label="Endereço", max_length=250, required=False)

class WorkerForm(forms.Form):
    username = forms.CharField(label="Nome de utilizador", max_length=150)
    first_name = forms.CharField(label="Nome completo", max_length=150)
    phone = forms.CharField(label="Telefone com indicativo", max_length=25)

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "code", "purchase_price", "sale_price", "stock", "min_stock"]

class CashOpenForm(forms.Form):
    mode = forms.ChoiceField(label="Tipo de caixa", choices=CashSession.MODE_CHOICES)
    opening_amount = forms.DecimalField(label="Fundo inicial (MT)", min_value=0, decimal_places=2, max_digits=12)

class CashCloseForm(forms.Form):
    counted_amount = forms.DecimalField(label="Valor contado no fecho (MT)", min_value=0, decimal_places=2, max_digits=12)
    notes = forms.CharField(label="Observações", required=False, widget=forms.Textarea)

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["description", "amount", "notes"]

class SaleForm(forms.Form):
    product = forms.ModelChoiceField(queryset=Product.objects.none(), label="Produto")
    quantity = forms.DecimalField(min_value=0.01, decimal_places=2, max_digits=12, label="Quantidade")
    payment_method = forms.ChoiceField(choices=[
        ("cash", "Numerário"), ("transfer", "Transferência"),
        ("card", "Cartão"), ("other", "Outro")
    ], label="Forma de pagamento")
    def __init__(self, *args, establishment=None, **kwargs):
        super().__init__(*args, **kwargs)
        if establishment:
            self.fields["product"].queryset = Product.objects.filter(establishment=establishment, active=True, stock__gt=0)
