import re

from django import forms

from .models import Expense


class ExpenseDateField(forms.DateField):
    def __init__(self, **kwargs):
        super().__init__(
            input_formats=["%Y-%m-%d"],
            widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            error_messages={"invalid": "Enter a valid date in YYYY-MM-DD format."},
            **kwargs,
        )

    def to_python(self, value):
        if isinstance(value, str) and value and not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise forms.ValidationError(self.error_messages["invalid"], code="invalid")
        return super().to_python(value)


class ExpenseForm(forms.ModelForm):
    date = ExpenseDateField()

    class Meta:
        model = Expense
        fields = ["category", "amount", "date", "description"]
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "placeholder": "0.00"}),
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "What was it for?"}),
        }

    def clean_description(self):
        description = self.cleaned_data["description"]
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", description).strip()


class ExpenseFilterForm(forms.Form):
    date = ExpenseDateField(required=False)
    category = forms.ChoiceField(
        choices=[("", "All categories"), *Expense.Category.choices], required=False
    )
