import operator
from functools import reduce

from django.contrib import messages
from django.db.models import ProtectedError, Q
from django.http import HttpResponseRedirect


class SearchMixin:
    """
    Adds ``?q=`` search to a ListView. Every word must match at least one of
    ``search_fields``.
    """

    search_fields = ()

    def get_search_query(self):
        return (self.request.GET.get('q') or '').strip()[:100]

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.get_search_query()
        if query and self.search_fields:
            conditions = [
                reduce(operator.or_, (Q(**{f'{field}__icontains': word}) for field in self.search_fields))
                for word in query.split()
            ]
            queryset = queryset.filter(reduce(operator.and_, conditions))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.get_search_query()
        return context


class ProtectedDeleteMixin:
    """
    Delete with a friendly message instead of a 500 when other records still
    point at the object (sales history, purchases and so on).
    """

    protected_message = (
        'This record is used by other records (for example sales or purchases) '
        'and cannot be deleted.'
    )
    success_message = 'Deleted.'

    def form_valid(self, form):
        success_url = self.get_success_url()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return HttpResponseRedirect(success_url)
        except Exception as exc:  # e.g. stock would go negative
            from django.core.exceptions import ValidationError
            if isinstance(exc, ValidationError):
                messages.error(self.request, ' '.join(exc.messages))
                return HttpResponseRedirect(success_url)
            raise
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(success_url)
