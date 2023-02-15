from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .models import Profile
from django.contrib.auth.decorators import login_required
from .forms import CreateUserForm, UserUpdateForm, ProfileUpdateForm
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin
from django_tables2.export.export import TableExport
from .tables import ProfileTable

from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
    )

# Create your views here.


def register(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('user-login')
    else:
        form = CreateUserForm()
    context = {
        'form': form
    }
    return render(request, 'accounts/register.html', context)


def profile(request):
    context = {

    }
    return render(request, 'accounts/profile.html', context)


def profile_update(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('user-profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form,
    }
    return render(request, 'accounts/profile_update.html', context)

class ProfileListView(LoginRequiredMixin, ExportMixin, tables.SingleTableView):
    model = Profile
    template_name = 'accounts/stafflist.html'
    context_object_name = 'profiles'
    pagination = 10
    table_class = ProfileTable
    SingleTableView.table_pagination = False

class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = Profile
    template_name = 'accounts/staffcreate'
    fields = ['user','role', 'status']

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False

    def get_success_url(self):
        return reverse('profile_list')

class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Profile
    template_name = 'accounts/staffupdate.html'
    fields = ['user','role', 'status']

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False
    def get_success_url(self):
        return reverse('profile_list')


class ProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Profile
    template_name = 'accounts/staffdelete.html'

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False
    def get_success_url(self):
        return reverse('profile_list')