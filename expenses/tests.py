from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import Expense, FailedLoginAttempt


class AuthenticationTests(TestCase):
    def test_registration_hashes_password_and_supports_login_and_logout(self):
        password = "A sample passphrase 8072!"
        registration = self.client.post(
            reverse("register"),
            {"username": "alice", "password1": password, "password2": password},
        )
        self.assertRedirects(registration, reverse("login"))
        user = get_user_model().objects.get(username="alice")
        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))

        login = self.client.post(
            reverse("login"), {"username": "alice", "password": password}
        )
        self.assertRedirects(login, reverse("expense_list"))
        self.assertIn("_auth_user_id", self.client.session)
        self.assertTrue(login.cookies["sessionid"]["httponly"])
        self.assertEqual(login.cookies["sessionid"]["samesite"], "Lax")
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

        logout = self.client.post(reverse("logout"))
        self.assertRedirects(logout, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(self.client.get(reverse("expense_list")), "/login/?next=/")

    def test_failed_credentials_create_an_audit_record(self):
        response = self.client.post(
            reverse("login"), {"username": "unknown", "password": "incorrect password"}
        )
        self.assertContains(response, "Please enter a correct username and password")
        attempt = FailedLoginAttempt.objects.get()
        self.assertEqual(attempt.username, "unknown")
        self.assertIsNotNone(attempt.attempted_at)
        self.assertNotIn("_auth_user_id", self.client.session)


class ExpenseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = get_user_model().objects.create_user(username="alice")
        cls.bob = get_user_model().objects.create_user(username="bob")
        cls.alice_expense = Expense.objects.create(
            owner=cls.alice, category="Food", amount="19.50",
            date="2026-11-25", description="Lunch receipt",
        )
        cls.bob_expense = Expense.objects.create(
            owner=cls.bob, category="Food", amount="5.00",
            date="2026-11-25", description="Bob's snack",
        )

    def setUp(self):
        self.client.force_login(self.alice)
        self.dashboard = reverse("expense_list")
        self.input = {
            "category": "Travel", "amount": "2.50",
            "date": "2026-11-25", "description": "  Bus ticket  ",
        }

    def test_add_binds_the_expense_to_the_session_user(self):
        response = self.client.post(self.dashboard, {**self.input, "owner": self.bob.pk})
        self.assertRedirects(response, self.dashboard, fetch_redirect_response=False)
        expense = Expense.objects.get(category="Travel")
        self.assertEqual(expense.owner, self.alice)
        self.assertEqual(expense.description, "Bus ticket")
        self.assertContains(self.client.get(self.dashboard), "Expense saved.")

    def test_overview_is_private_and_remains_all_time_when_filtered(self):
        self.client.post(self.dashboard, self.input)
        response = self.client.get(self.dashboard, {"category": "Travel"})
        self.assertEqual(response.context["expense_count"], 2)
        self.assertEqual(response.context["total"], Decimal("22.00"))
        self.assertEqual(
            [(category["category"], category["share"]) for category in response.context["categories"]],
            [("Food", 89), ("Travel", 11)],
        )
        self.assertNotContains(response, "Lunch receipt")

    def test_delete_keeps_the_current_history_filters(self):
        own_url = reverse("expense_delete", args=[self.alice_expense.pk])
        response = self.client.post(f"{own_url}?category=Food")
        self.assertRedirects(response, "/?category=Food#history")
        self.assertFalse(Expense.objects.filter(pk=self.alice_expense.pk).exists())

    def test_list_and_filters_only_return_the_current_users_expenses(self):
        self.client.post(self.dashboard, self.input)
        self.client.post(
            self.dashboard, {**self.input, "date": "2026-11-24", "description": "Older bus ticket"}
        )
        all_expenses = self.client.get(self.dashboard)
        self.assertContains(all_expenses, "Lunch receipt")
        self.assertNotContains(all_expenses, "Bob")
        self.assertContains(self.client.get(self.dashboard, {"category": "Travel"}), "Older bus ticket")
        date_search = self.client.get(self.dashboard, {"date": "2026-11-25"})
        self.assertContains(date_search, "Lunch receipt")
        self.assertNotContains(date_search, "Older bus ticket")
        combined = self.client.get(self.dashboard, {"date": "2026-11-25", "category": "Travel"})
        self.assertContains(combined, "Bus ticket")
        self.assertNotContains(combined, "Older bus ticket")
        self.assertNotContains(combined, "Lunch receipt")

    def test_only_post_can_delete_and_only_for_the_owner(self):
        own_url = reverse("expense_delete", args=[self.alice_expense.pk])
        other_url = reverse("expense_delete", args=[self.bob_expense.pk])
        self.assertEqual(self.client.get(own_url).status_code, 405)
        self.assertEqual(self.client.post(other_url).status_code, 404)
        self.assertTrue(Expense.objects.filter(pk=self.bob_expense.pk).exists())
        self.assertRedirects(self.client.post(own_url), self.dashboard)
        self.assertFalse(Expense.objects.filter(pk=self.alice_expense.pk).exists())

    def test_add_rejects_invalid_amounts_dates_and_categories(self):
        invalid_values = {
            "amount": ["-1", "0", "hello", "NaN", "2.501"],
            "date": ["25/11/2026", "2026-1-05", "2026-02-30"],
            "category": ["Unlisted"],
        }
        for field, values in invalid_values.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    response = self.client.post(self.dashboard, {**self.input, field: value})
                    self.assertIn(field, response.context["form"].errors)
        self.assertEqual(Expense.objects.count(), 2)

    def test_brief_input_is_rejected_as_a_category_and_preserved_as_text(self):
        example = "Food'; DROP TABLE expenses; --"
        response = self.client.post(self.dashboard, {**self.input, "category": example})
        self.assertIn("category", response.context["form"].errors)
        search = self.client.get(self.dashboard, {"category": example})
        self.assertIn("category", search.context["filters"].errors)
        self.assertEqual(Expense.objects.count(), 2)

        self.assertRedirects(
            self.client.post(self.dashboard, {**self.input, "description": example}),
            self.dashboard,
        )
        self.assertEqual(Expense.objects.get(category="Travel").description, example)
        self.assertContains(self.client.get(self.dashboard), "DROP TABLE expenses")
        self.assertEqual(Expense.objects.count(), 3)

    def test_description_is_displayed_as_plain_text(self):
        self.client.post(self.dashboard, {**self.input, "description": "<b>Receipt</b>"})
        response = self.client.get(self.dashboard)
        self.assertContains(response, "&lt;b&gt;Receipt&lt;/b&gt;")
        self.assertNotContains(response, "<b>Receipt</b>")

    def test_add_and_delete_require_csrf_tokens(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.alice)
        delete_url = reverse("expense_delete", args=[self.alice_expense.pk])
        self.assertEqual(client.post(self.dashboard, self.input).status_code, 403)
        self.assertEqual(client.post(delete_url).status_code, 403)
        token = client.get(self.dashboard).cookies["csrftoken"].value
        self.assertEqual(client.post(
            self.dashboard, self.input, HTTP_X_CSRFTOKEN=token
        ).status_code, 302)
        self.assertEqual(client.post(delete_url, HTTP_X_CSRFTOKEN=token).status_code, 302)
