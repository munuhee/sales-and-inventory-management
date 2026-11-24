"""
PDF rendering with WeasyPrint.

Documents (receipts, invoices) are plain Django templates styled with print
CSS. ``render_pdf_response`` turns one into a PDF served either inline (the
browser's PDF viewer opens it, ready to print) or as a download.

WeasyPrint is imported lazily so the rest of the app keeps working on a host
that is missing its system libraries (Pango). In that case PDF endpoints
answer 503 with a clear message instead of crashing the whole site.
"""
import logging

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class PdfUnavailable(RuntimeError):
    pass


def _url_fetcher(url, *args, **kwargs):
    """
    Resolve /static/ URLs from local files and refuse everything else, so a
    document can never make the server fetch remote or internal URLs.
    """
    from weasyprint import default_url_fetcher

    static_prefix = '/' + settings.STATIC_URL.lstrip('/')
    for prefix in (static_prefix, settings.STATIC_URL):
        if url.startswith(prefix):
            path = finders.find(url[len(prefix):])
            if path:
                return default_url_fetcher('file:///' + str(path).replace('\\', '/').lstrip('/'))
    if url.startswith('data:'):
        return default_url_fetcher(url)
    raise ValueError(f'Blocked external resource in PDF: {url}')


def render_pdf(template_name, context, request=None):
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as exc:  # OSError: Pango/GObject missing
        logger.error('WeasyPrint unavailable: %s', exc)
        raise PdfUnavailable(str(exc)) from exc

    html = render_to_string(template_name, context, request=request)
    base_url = request.build_absolute_uri('/') if request is not None else None
    return HTML(string=html, base_url=base_url, url_fetcher=_url_fetcher).write_pdf()


def render_pdf_response(template_name, context, filename, request=None, download=False):
    try:
        pdf = render_pdf(template_name, context, request=request)
    except PdfUnavailable:
        return HttpResponse(
            'PDF generation is not available on this server. '
            'Install WeasyPrint and its system libraries (Pango).',
            status=503, content_type='text/plain',
        )
    response = HttpResponse(pdf, content_type='application/pdf')
    disposition = 'attachment' if download else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    return response
