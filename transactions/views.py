import json
from django.http import JsonResponse
from django.urls import reverse
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from store.models import Item
from accounts.models import Customer
from .models import Sale, Purchase, SaleDetail
from .forms import PurchaseForm


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


class SaleListView(LoginRequiredMixin, ListView):
    """
    View to list all sales with pagination.
    """

    model = Sale
    template_name = "transactions/sales_list.html"
    context_object_name = "sales"
    paginate_by = 10
    ordering = ['date_added']


class SaleDetailView(LoginRequiredMixin, DetailView):
    """
    View to display details of a specific sale.
    """

    model = Sale
    template_name = "transactions/saledetail.html"


def SaleCreateView(request):
    context = {
        "active_icon": "sales",
        "customers": [c.to_select2() for c in Customer.objects.all()]
    }

    if request.method == 'POST':
        if is_ajax(request=request):
            try:
                # Load the JSON data from the request body
                data = json.loads(request.body)

                # Validate required fields
                required_fields = [
                    'customer', 'sub_total', 'grand_total',
                    'amount_paid', 'amount_change', 'items'
                ]
                for field in required_fields:
                    if field not in data:
                        raise ValueError(f"Missing required field: {field}")

                # Create sale attributes
                sale_attributes = {
                    "customer": Customer.objects.get(id=int(data['customer'])),
                    "sub_total": float(data["sub_total"]),
                    "grand_total": float(data["grand_total"]),
                    "discount_amount": float(data.get("discount_amount", 0.0)),
                    "discount_percentage": float(data.get("discount_percentage", 0.0)),
                    "amount_paid": float(data["amount_paid"]),
                    "amount_change": float(data["amount_change"]),
                }

                # Create the sale
                new_sale = Sale.objects.create(**sale_attributes)

                # Create sale details
                items = data["items"]
                if not isinstance(items, list):
                    raise ValueError("Items should be a list")

                for item in items:
                    if not all(k in item for k in ["id", "price", "quantity", "total_item"]):
                        raise ValueError("Item is missing required fields")

                    detail_attributes = {
                        "sale": new_sale,
                        "item": Item.objects.get(id=int(item["id"])),
                        "price": float(item["price"]),
                        "quantity": int(item["quantity"]),
                        "total_detail": float(item["total_item"])
                    }
                    SaleDetail.objects.create(**detail_attributes)

                return JsonResponse({'status': 'success', 'message': 'Sale created successfully!', 'redirect': '/transactions/sales/'})

            except json.JSONDecodeError:
                return JsonResponse({'status': 'error', 'message': 'Invalid JSON format in request body!'}, status=400)
            except Customer.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Customer does not exist!'}, status=400)
            except Item.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Item does not exist!'}, status=400)
            except ValueError as ve:
                return JsonResponse({'status': 'error', 'message': f'Value error: {str(ve)}'}, status=400)
            except TypeError as te:
                return JsonResponse({'status': 'error', 'message': f'Type error: {str(te)}'}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'There was an error during the creation: {str(e)}'}, status=500)

    return render(request, "transactions/sale_create.html", context=context)


class SaleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete a sale.
    """

    model = Sale
    template_name = "transactions/saledelete.html"

    def get_success_url(self):
        """
        Redirect to the sales list after successful deletion.
        """
        return reverse("saleslist")

    def test_func(self):
        """
        Allow deletion only for superusers.
        """
        return self.request.user.is_superuser


class PurchaseListView(LoginRequiredMixin, ListView):
    """
    View to list all purchases with pagination.
    """

    model = Purchase
    template_name = "transactions/purchases_list.html"
    context_object_name = "purchases"
    paginate_by = 10


class PurchaseDetailView(LoginRequiredMixin, DetailView):
    """
    View to display details of a specific purchase.
    """

    model = Purchase
    template_name = "transactions/purchasedetail.html"


class PurchaseCreateView(LoginRequiredMixin, CreateView):
    """
    View to create a new purchase.
    """

    model = Purchase
    form_class = PurchaseForm
    template_name = "transactions/purchases_form.html"

    def get_success_url(self):
        """
        Redirect to the purchases list after successful form submission.
        """
        return reverse("purchaseslist")

    def form_valid(self, form):
        """
        Validates the form and updates item quantity and total value.
        """
        item = form.cleaned_data["item"]
        quantity = form.cleaned_data["quantity"]
        total_value = item.selling_price * quantity

        form.instance.total_value = total_value
        form.instance.price = item.selling_price
        item.quantity += quantity
        item.save()

        return super().form_valid(form)


class PurchaseUpdateView(LoginRequiredMixin, UpdateView):
    """
    View to update an existing purchase.
    """

    model = Purchase
    form_class = PurchaseForm
    template_name = "transactions/purchases_form.html"

    def get_success_url(self):
        """
        Redirect to the purchases list after successful form submission.
        """
        return reverse("purchaseslist")


class PurchaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View to delete a purchase.
    """

    model = Purchase
    template_name = "transactions/purchasedelete.html"

    def get_success_url(self):
        """
        Redirect to the purchases list after successful deletion.
        """
        return reverse("purchaseslist")

    def test_func(self):
        """
        Allow deletion only for superusers.
        """
        return self.request.user.is_superuser
