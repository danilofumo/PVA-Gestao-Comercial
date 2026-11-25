from decimal import Decimal
import secrets
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth import get_user_model
from django.core import signing
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponseForbidden
from .models import Establishment, Membership, Product, Sale, SaleItem, CashSession, Expense, StockMovement
from .forms import RegisterForm, WorkerForm, ProductForm, CashOpenForm, CashCloseForm, ExpenseForm, SaleForm
from .decorators import member_required, owner_required, current_membership

def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if User.objects.filter(username=data["username"]).exists():
            form.add_error("username", "Este nome de utilizador já existe.")
        else:
            user = User.objects.create_user(username=data["username"], password=data["password"], first_name=data["owner_name"])
            establishment = Establishment.objects.create(name=data["establishment"], owner=user, address=data["address"])
            Membership.objects.create(establishment=establishment, user=user, role=Membership.OWNER)
            login(request, user)
            messages.success(request, "Estabelecimento criado. Bem-vindo ao PVA!")
            return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Criar conta de comerciante", "button": "Criar estabelecimento"})

@login_required
def dashboard(request):
    membership = current_membership(request.user)
    if not membership:
        return redirect("login")
    est = membership.establishment
    today = timezone.localdate()
    sales = Sale.objects.filter(establishment=est, voided=False, created_at__date=today)
    total_sales = sales.aggregate(v=Sum("total"))["v"] or Decimal("0")
    product_count = Product.objects.filter(establishment=est, active=True).count()
    low_stock = Product.objects.filter(establishment=est, active=True, stock__lte=F("min_stock")).count()
    recent_sales = sales.select_related("worker").order_by("-created_at")[:10]
    context = {"membership": membership, "establishment": est, "total_sales": total_sales,
               "product_count": product_count, "low_stock": low_stock, "recent_sales": recent_sales}
    if membership.role == Membership.OWNER:
        context["worker_count"] = Membership.objects.filter(establishment=est, role=Membership.WORKER, active=True).count()
    else:
        context["my_sales"] = sales.filter(worker=request.user).aggregate(v=Sum("total"))["v"] or Decimal("0")
        context["recent_sales"] = recent_sales.filter(worker=request.user)
    return render(request, "core/dashboard.html", context)

@owner_required
def workers(request):
    est = request.membership.establishment
    form = WorkerForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data

        if User.objects.filter(username=d["username"]).exists():
            form.add_error("username", "Este utilizador já existe.")
        elif Membership.objects.filter(establishment=est, phone=d["phone"]).exists():
            form.add_error("phone", "Este telefone já está associado a um trabalhador.")
        else:
            user = User.objects.create_user(
                username=d["username"],
                password=secrets.token_urlsafe(32),
                first_name=d["first_name"],
                is_active=False
            )

            membership = Membership.objects.create(
                establishment=est,
                user=user,
                role=Membership.WORKER,
                phone=d["phone"]
            )

            token = signing.dumps(
                {"uid": user.pk, "mid": membership.pk},
                salt="pva-worker-invite"
            )

            invite_url = request.build_absolute_uri(
                reverse("worker_activate", args=[token])
            )

            from urllib.parse import quote

            message = quote(
                f"Olá {d['first_name']}! A tua conta PVA foi criada. "
                f"Abre este link para activar a tua conta e definir "
                f"a tua palavra-passe: {invite_url}"
            )

            whatsapp_url = (
                "https://wa.me/"
                + "".join(ch for ch in d["phone"] if ch.isdigit())
                + "?text="
                + message
            )

            messages.success(
                request,
                "Conta criada. Envia o convite pelo WhatsApp."
            )

            people = Membership.objects.filter(
                establishment=est,
                role=Membership.WORKER
            ).select_related("user")

            return render(request, "core/workers.html", {
                "form": WorkerForm(),
                "people": people,
                "invite_url": invite_url,
                "whatsapp_url": whatsapp_url
            })

    people = Membership.objects.filter(
        establishment=est,
        role=Membership.WORKER
    ).select_related("user")

    return render(request, "core/workers.html", {
        "form": form,
        "people": people
    })


def worker_activate(request, token):
    try:
        data = signing.loads(token, salt="pva-worker-invite", max_age=172800)
        user = User.objects.get(pk=data["uid"], is_active=False)
        membership = Membership.objects.get(pk=data["mid"], user=user, active=True, role=Membership.WORKER)
    except (signing.BadSignature, signing.SignatureExpired, User.DoesNotExist, Membership.DoesNotExist, KeyError):
        messages.error(request, "Convite inválido, expirado ou já utilizado. Solicita um novo convite ao proprietário.")
        return redirect("login")
    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")
        if len(password) < 8:
            messages.error(request, "A palavra-passe deve ter pelo menos 8 caracteres.")
        elif password != confirm:
            messages.error(request, "As palavras-passe não coincidem.")
        else:
            user.set_password(password)
            user.is_active = True
            user.save(update_fields=["password", "is_active"])
            login(request, user)
            messages.success(request, "Conta activada. Bem-vindo à tua área de trabalhador!")
            return redirect("dashboard")
    return render(request, "core/activate_worker.html", {"worker": user, "establishment": membership.establishment})

@owner_required
def toggle_worker(request, pk):
    if request.method != "POST":
        return redirect("workers")
    membership = get_object_or_404(Membership, pk=pk, establishment=request.membership.establishment, role=Membership.WORKER)
    membership.active = not membership.active
    membership.save(update_fields=["active"])
    messages.success(request, "Estado do trabalhador atualizado.")
    return redirect("workers")

@member_required
def products(request):
    est = request.membership.establishment
    if request.membership.role == Membership.OWNER:
        form = ProductForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            product = form.save(commit=False)
            product.establishment = est
            product.save()
            StockMovement.objects.create(establishment=est, product=product, user=request.user, movement_type="in", quantity=product.stock, note="Stock inicial")
            messages.success(request, "Produto adicionado.")
            return redirect("products")
    else:
        form = None
    items = Product.objects.filter(establishment=est, active=True)
    return render(request, "core/products.html", {"items": items, "form": form, "is_owner": request.membership.role == Membership.OWNER})

@owner_required
def stock_adjust(request, pk):
    est = request.membership.establishment
    product = get_object_or_404(Product, pk=pk, establishment=est, active=True)
    if request.method == "POST":
        try:
            qty = Decimal(request.POST.get("quantity", "0"))
            kind = request.POST.get("kind")
            note = request.POST.get("note", "")[:250]
            if qty <= 0 or kind not in ["in", "loss"]:
                raise ValueError()
            if kind == "loss" and qty > product.stock:
                messages.error(request, "A quantidade de perda não pode exceder o stock.")
            else:
                with transaction.atomic():
                    product.stock = product.stock + qty if kind == "in" else product.stock - qty
                    product.save(update_fields=["stock"])
                    StockMovement.objects.create(establishment=est, product=product, user=request.user, movement_type=kind, quantity=qty, note=note)
                messages.success(request, "Stock atualizado.")
        except (ValueError, ArithmeticError):
            messages.error(request, "Quantidade inválida.")
    return redirect("products")

@member_required
def sale_create(request):
    membership = request.membership
    if membership.role != Membership.WORKER:
        messages.error(request, "Apenas trabalhadores podem registar vendas.")
        return redirect("dashboard")
    est = membership.establishment
    form = SaleForm(request.POST or None, establishment=est)
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=d["product"].pk, establishment=est)
            cash = CashSession.objects.filter(establishment=est, status="open")
            if not cash.exists():
                messages.error(request, "Não existe uma caixa aberta. Solicita ao proprietário que abra uma caixa.")
                return redirect("sale_create")
            if membership.role == Membership.WORKER:
                cash = cash.filter(mode="shared") | cash.filter(mode="individual", opened_by=request.user)
            else:
                cash = cash.filter(mode="shared") | cash.filter(mode="individual", opened_by=request.user)
            session = cash.order_by("-opened_at").first()
            if not session:
                messages.error(request, "Não tens uma caixa aberta disponível.")
                return redirect("sale_create")
            if d["quantity"] > product.stock:
                messages.error(request, "Stock insuficiente.")
                return redirect("sale_create")
            product.stock -= d["quantity"]
            product.save(update_fields=["stock"])
            total = d["quantity"] * product.sale_price
            sale = Sale.objects.create(establishment=est, worker=request.user, cash_session=session,
                                       payment_method=d["payment_method"], total=total)
            SaleItem.objects.create(sale=sale, product=product, quantity=d["quantity"],
                                    unit_price=product.sale_price, unit_cost=product.purchase_price)
            StockMovement.objects.create(establishment=est, product=product, user=request.user,
                                         movement_type="out", quantity=d["quantity"], note=f"Venda #{sale.pk}")
        messages.success(request, f"Venda #{sale.pk} registada: {total} MT.")
        return redirect("sale_create")
    return render(request, "core/form_page.html", {"form": form, "title": "Registar venda", "button": "Confirmar venda"})

@member_required
def sales_list(request):
    est = request.membership.establishment
    qs = Sale.objects.filter(establishment=est, voided=False).select_related("worker").order_by("-created_at")
    if request.membership.role == Membership.WORKER:
        qs = qs.filter(worker=request.user)
    return render(request, "core/sales.html", {"sales": qs[:200], "is_owner": request.membership.role == Membership.OWNER})

@owner_required
def expense_create(request):
    est = request.membership.establishment
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        expense.establishment = est
        expense.created_by = request.user
        expense.save()
        messages.success(request, "Despesa registada.")
        return redirect("dashboard")
    return render(request, "core/form_page.html", {"form": form, "title": "Registar despesa", "button": "Guardar despesa"})

@member_required
def cash_list(request):
    est = request.membership.establishment
    sessions = CashSession.objects.filter(establishment=est).order_by("-opened_at")
    if request.membership.role == Membership.WORKER:
        sessions = sessions.filter(models_q_worker(request.user))
    return render(request, "core/cash.html", {"sessions": sessions[:100], "is_owner": request.membership.role == Membership.OWNER})

def models_q_worker(user):
    from django.db.models import Q
    return Q(mode="shared") | Q(mode="individual", opened_by=user)

@member_required
def cash_open(request):
    est = request.membership.establishment
    form = CashOpenForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        mode = form.cleaned_data["mode"]
        if request.membership.role == Membership.WORKER and mode != "individual":
            messages.error(request, "Apenas o proprietário pode abrir uma caixa comum.")
            return redirect("cash_open")
        if mode == "individual" and CashSession.objects.filter(establishment=est, mode="individual", opened_by=request.user, status="open").exists():
            messages.error(request, "Já tens uma caixa individual aberta.")
        elif mode == "shared" and CashSession.objects.filter(establishment=est, mode="shared", status="open").exists():
            messages.error(request, "Já existe uma caixa comum aberta.")
        else:
            CashSession.objects.create(establishment=est, mode=mode, opened_by=request.user,
                                       opening_amount=form.cleaned_data["opening_amount"])
            messages.success(request, "Caixa aberta.")
            return redirect("cash_list")
    return render(request, "core/form_page.html", {"form": form, "title": "Abrir caixa", "button": "Abrir caixa"})

@member_required
def cash_close(request, pk):
    est = request.membership.establishment
    session = get_object_or_404(CashSession, pk=pk, establishment=est, status="open")
    if session.mode == "individual" and session.opened_by != request.user and request.membership.role != Membership.OWNER:
        return HttpResponseForbidden("Sem permissão.")
    if session.mode == "shared" and request.membership.role != Membership.OWNER:
        return HttpResponseForbidden("Apenas o proprietário pode fechar a caixa comum.")
    form = CashCloseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        expected_sales = session.sales.filter(voided=False).aggregate(v=Sum("total"))["v"] or Decimal("0")
        expected = session.opening_amount + expected_sales
        session.counted_amount = form.cleaned_data["counted_amount"]
        session.notes = form.cleaned_data["notes"]
        session.closed_by = request.user
        session.closed_at = timezone.now()
        session.status = "closed"
        session.save()
        messages.success(request, f"Caixa fechada. Vendas: {expected} MT. Contado: {session.counted_amount} MT. Diferença: {session.counted_amount - expected} MT.")
        return redirect("cash_list")
    return render(request, "core/form_page.html", {"form": form, "title": "Fechar caixa", "button": "Confirmar fecho"})

@owner_required
def reports(request):
    est = request.membership.establishment
    sales = Sale.objects.filter(establishment=est, voided=False)
    total = sales.aggregate(v=Sum("total"))["v"] or Decimal("0")
    expenses = Expense.objects.filter(establishment=est).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    cost = SaleItem.objects.filter(sale__establishment=est, sale__voided=False).aggregate(
        v=Sum(F("quantity") * F("unit_cost")))["v"] or Decimal("0")
    gross_profit = total - cost
    return render(request, "core/reports.html", {"total": total, "expenses": expenses,
                  "gross_profit": gross_profit, "net_estimate": gross_profit-expenses,
                  "sales_count": sales.count()})
