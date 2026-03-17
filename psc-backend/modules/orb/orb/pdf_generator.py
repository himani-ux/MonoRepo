# orb/pdf_generator.py
from weasyprint import HTML
from django.utils import timezone
from django.template.loader import render_to_string
from .models import ORBEntry, ORBPagedSignature

def generate_orb_pdf_page(ship, page_number, entries, master_signature=None):
    html_string = render_to_string('orb/orb_page.html', {
        'ship': ship,
        'page_number': page_number,
        'entries': entries,
        'master_signature': master_signature,
        'today': timezone.now()
    })

    html = HTML(string=html_string)
    return html.write_pdf()

