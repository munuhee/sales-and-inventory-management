from django import forms
from django.forms import ModelForm
from .models import Item

class ProductForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = '__all__'
        widgets = {
            'expiring_date': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker-input',
                'data-target': '#datetimepicker1',
                'placeholder': 'mm/dd/yyyy'
                }),
        }
