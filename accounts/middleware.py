from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect

from .permissions import is_active_member


class ActiveProfileMiddleware:
    """
    Sign out users whose staff profile is no longer Active (pending approval,
    deactivated or on leave), so revoking access takes effect immediately
    instead of when the session expires.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated and not is_active_member(user):
            logout(request)
            messages.warning(
                request,
                'Your account is not active. Contact an administrator.'
            )
            return redirect('user-login')
        return self.get_response(request)
