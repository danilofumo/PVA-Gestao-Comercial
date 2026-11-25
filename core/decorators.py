from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from .models import Membership

def current_membership(user):
    if not user.is_authenticated:
        return None
    return Membership.objects.filter(user=user, active=True).select_related("establishment").first()

def owner_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        membership = current_membership(request.user)
        if not membership or membership.role != Membership.OWNER:
            messages.error(request, "Esta operação é exclusiva do proprietário.")
            return redirect("dashboard")
        request.membership = membership
        return view(request, *args, **kwargs)
    return wrapper

def member_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        membership = current_membership(request.user)
        if not membership:
            messages.error(request, "A tua conta não está associada a um estabelecimento.")
            return redirect("login")
        request.membership = membership
        return view(request, *args, **kwargs)
    return wrapper
