from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import get_object_or_404, redirect, render
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
        return redirect("expense_list")

    expenses = Expense.objects.filter(owner=request.user)
    filters = ExpenseFilterForm(request.GET or None, auto_id="filter_%s")
    if filters.is_bound:
        if filters.is_valid():
            if filters.cleaned_data["date"]:
                expenses = expenses.filter(date=filters.cleaned_data["date"])
            if filters.cleaned_data["category"]:
                expenses = expenses.filter(category=filters.cleaned_data["category"])
        else:
            expenses = expenses.none()

    return render(
        request,
        "expenses/expense_list.html",
        {"form": form, "filters": filters, "expenses": expenses},
    )


@login_required
@require_POST
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, pk=expense_id, owner=request.user)
    expense.delete()
    return redirect("expense_list")
