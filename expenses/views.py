from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ExpenseFilterForm, ExpenseForm
from .models import Expense


@never_cache
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("expense_list")

    form = UserCreationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created. Log in to get started.")
        return redirect("login")

    return render(request, "registration/register.html", {"form": form})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def expense_list(request):
    form = ExpenseForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        expense.owner = request.user
        expense.save()
        messages.success(request, "Expense saved.")
        return redirect("expense_list")

    expenses = Expense.objects.filter(owner=request.user)
    categories = list(
        expenses.values("category")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total", "category")
    )
    total = sum(category["total"] for category in categories)
    expense_count = sum(category["count"] for category in categories)
    for category in categories:
        category["share"] = round(category["total"] / total * 100)

    filters = ExpenseFilterForm(request.GET or None, auto_id="filter_%s")
    active_filters = {}
    if filters.is_bound:
        if filters.is_valid():
            active_filters = {
                field: value for field, value in filters.cleaned_data.items() if value
            }
            expenses = expenses.filter(**active_filters)
        else:
            expenses = expenses.none()

    return render(
        request,
        "expenses/expense_list.html",
        {
            "form": form,
            "filters": filters,
            "filter_query": urlencode(active_filters),
            "expenses": expenses,
            "categories": categories,
            "total": total,
            "expense_count": expense_count,
        },
    )


@login_required
@require_POST
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id, owner=request.user)
    expense.delete()
    messages.success(request, "Expense deleted.")
    if request.GET:
        filters = ExpenseFilterForm(request.GET)
        if filters.is_valid():
            active_filters = {
                field: value for field, value in filters.cleaned_data.items() if value
            }
            if active_filters:
                return redirect(reverse("expense_list", query=active_filters, fragment="history"))
    return redirect("expense_list")
