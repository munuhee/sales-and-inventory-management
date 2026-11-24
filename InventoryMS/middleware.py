"""
Security headers that Django 5.2 does not set by itself.

Django's SecurityMiddleware already handles HSTS, X-Content-Type-Options,
Referrer-Policy and Cross-Origin-Opener-Policy. This adds a Content Security
Policy for HTML pages and a few cross-origin and feature restrictions for every
response. Each header can be changed or switched off in settings.
"""
from django.conf import settings


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = getattr(settings, 'CONTENT_SECURITY_POLICY', '')
        self.headers = {
            'Permissions-Policy': getattr(settings, 'PERMISSIONS_POLICY', ''),
            'Cross-Origin-Embedder-Policy': getattr(settings, 'CROSS_ORIGIN_EMBEDDER_POLICY', ''),
            'Cross-Origin-Resource-Policy': getattr(settings, 'CROSS_ORIGIN_RESOURCE_POLICY', ''),
        }

    def __call__(self, request):
        response = self.get_response(request)
        for name, value in self.headers.items():
            if value:
                response.headers.setdefault(name, value)
        # The policy is written for HTML pages. PDFs and downloads keep the
        # browser's built-in viewers working by not getting one.
        content_type = response.headers.get('Content-Type', '')
        # Django's DEBUG error pages use inline styles; production error
        # pages are our own templates and keep the policy.
        debug_error_page = settings.DEBUG and response.status_code >= 400
        if self.csp and content_type.startswith('text/html') and not debug_error_page:
            response.headers.setdefault('Content-Security-Policy', self.csp)
        return response
