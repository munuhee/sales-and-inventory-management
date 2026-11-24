from django import forms

from .models import Purchase


class BootstrapMixin(forms.ModelForm):
    """Adds Bootstrap classes to every field."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)
        if 'item' in self.fields:
            self.fields['item'].empty_label = 'Choose a product'
            self.fields['vendor'].empty_label = 'Choose a vendor'
            self.has_items = self.fields['item'].queryset.exists()
            self.has_vendors = self.fields['vendor'].queryset.exists()


class PurchaseForm(BootstrapMixin, forms.ModelForm):
    """Create and update purchase orders."""

    class Meta:
        model = Purchase
        fields = [
            'item', 'vendor', 'quantity', 'price', 'description',
            'delivery_date', 'delivery_status',
        ]
        widgets = {
            'delivery_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
            'description': forms.Textarea(attrs={'rows': 2}),
            'quantity': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'price': forms.NumberInput(attrs={'min': 0, 'step': '0.01'}),
        }
        help_texts = {
            'delivery_status': 'Stock is added when the status is Successful.',
        }


class VoidSaleForm(forms.Form):
    reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Reason, for example customer returned all items',
        }),
    )
