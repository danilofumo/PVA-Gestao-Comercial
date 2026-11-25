from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("registar/", views.register, name="register"),
    path("entrar/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("trabalhadores/", views.workers, name="workers"),
    path("activar-trabalhador/<str:token>/", views.worker_activate, name="worker_activate"),
    path("trabalhadores/<int:pk>/alternar/", views.toggle_worker, name="toggle_worker"),
    path("produtos/", views.products, name="products"),
    path("produtos/<int:pk>/stock/", views.stock_adjust, name="stock_adjust"),
    path("vendas/nova/", views.sale_create, name="sale_create"),
    path("vendas/", views.sales_list, name="sales_list"),
    path("despesas/nova/", views.expense_create, name="expense_create"),
    path("caixas/", views.cash_list, name="cash_list"),
    path("caixas/abrir/", views.cash_open, name="cash_open"),
    path("caixas/<int:pk>/fechar/", views.cash_close, name="cash_close"),
    path("relatorios/", views.reports, name="reports"),
]
