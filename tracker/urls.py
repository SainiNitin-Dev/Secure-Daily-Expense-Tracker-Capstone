from django.contrib.auth import views as auth_views
from django.urls import path

from expenses import views


urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("expenses/<int:expense_id>/delete/", views.delete_expense, name="expense_delete"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
