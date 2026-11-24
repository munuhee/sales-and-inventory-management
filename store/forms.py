from django import forms
from .models import Item, Category, Delivery


class ItemForm(forms.ModelForm):
    """
    A form for creating or updating an Item in the inventory.
    """
    class Meta:
        model = Item
        fields = [
            'name',
            'description',
            'category',
            'quantity',
            'price',
            'expiring_date',
            'vendor'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2
                }
            ),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 1}),
            'price': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 0,
                    'step': '0.01'
                }
            ),
            'expiring_date': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M',
            ),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        category = self.fields['category']
        vendor = self.fields['vendor']
        category.empty_label = 'Choose a category'
        vendor.empty_label = 'No vendor (optional)'
        self.has_categories = category.queryset.exists()
        self.has_vendors = vendor.queryset.exists()
        category.help_text = 'Required to keep your inventory organized.'
        vendor.help_text = 'Optional. Link this product to its supplier.'


class CategoryForm(forms.ModelForm):
    """
    A form for creating or updating category.
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category name',
                'aria-label': 'Category Name'
            }),
        }
        labels = {
            'name': 'Category Name',
        }


class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = [
            'item',
            'customer_name',
            'phone_number',
            'location',
            'date',
            'is_delivered'
        ]
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter customer name',
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter delivery location',
            }),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }, format='%Y-%m-%dT%H:%M'),
            'is_delivered': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['item'].empty_label = 'Choose an item (optional)'
        self.has_items = self.fields['item'].queryset.exists()
