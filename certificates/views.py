from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from .models import Certificate
import uuid

@login_required
def certificate_list(request):
    certs = Certificate.objects.filter(user=request.user, is_valid=True).select_related('course')
    return render(request, 'certificates/list.html', {'certificates': certs})

def certificate_view(request, cert_id):
    cert = get_object_or_404(Certificate, certificate_id=cert_id, is_valid=True)
    return render(request, 'certificates/view.html', {'certificate': cert})

@login_required
def certificate_download(request, cert_id):
    cert = get_object_or_404(Certificate, certificate_id=cert_id, user=request.user, is_valid=True)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from io import BytesIO
        import datetime

        buffer = BytesIO()
        w, h = landscape(A4)
        c = canvas.Canvas(buffer, pagesize=landscape(A4))

        # Background gradient effect
        c.setFillColorRGB(0.97, 0.97, 1.0)
        c.rect(0, 0, w, h, fill=True, stroke=False)

        # Decorative border
        c.setStrokeColorRGB(0.4, 0.2, 0.8)
        c.setLineWidth(8)
        c.rect(20, 20, w-40, h-40, fill=False)
        c.setLineWidth(2)
        c.setStrokeColorRGB(0.6, 0.4, 0.9)
        c.rect(30, 30, w-60, h-60, fill=False)

        # Header
        c.setFillColorRGB(0.4, 0.2, 0.8)
        c.setFont("Helvetica-Bold", 42)
        c.drawCentredString(w/2, h-100, "CERTIFICATE OF COMPLETION")

        # Subtitle line
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica", 16)
        c.drawCentredString(w/2, h-130, "This certifies that")

        # Student name
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica-Bold", 36)
        name = cert.user.get_full_name() or cert.user.username
        c.drawCentredString(w/2, h-185, name)

        # Underline name
        name_width = c.stringWidth(name, "Helvetica-Bold", 36)
        c.setStrokeColorRGB(0.4, 0.2, 0.8)
        c.setLineWidth(1.5)
        c.line(w/2 - name_width/2, h-192, w/2 + name_width/2, h-192)

        # Has completed
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica", 16)
        c.drawCentredString(w/2, h-225, "has successfully completed the course")

        # Course name
        c.setFillColorRGB(0.2, 0.5, 0.2)
        c.setFont("Helvetica-Bold", 28)
        course_title = cert.course.title
        if len(course_title) > 50:
            course_title = course_title[:47] + "..."
        c.drawCentredString(w/2, h-270, f'"{course_title}"')

        # Date
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica", 14)
        date_str = cert.issued_at.strftime("%B %d, %Y")
        c.drawCentredString(w/2, h-315, f"Issued on {date_str}")

        # Certificate ID
        c.setFillColorRGB(0.6, 0.6, 0.6)
        c.setFont("Helvetica", 10)
        c.drawCentredString(w/2, 60, f"Certificate ID: {cert.certificate_id}")

        # Signature lines
        c.setStrokeColorRGB(0.3, 0.3, 0.3)
        c.setLineWidth(1)
        c.line(100, 110, 280, 110)
        c.line(w-280, 110, w-100, 110)
        c.setFont("Helvetica", 12)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawCentredString(190, 95, "Instructor")
        c.drawCentredString(w-190, 95, "Platform Director")

        # Platform name
        c.setFillColorRGB(0.4, 0.2, 0.8)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(w/2, h-360, "🎓 EduLearn LMS Platform")

        c.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificate-{cert.certificate_id}.pdf"'
        return response

    except ImportError:
        return HttpResponse("PDF generation requires reportlab. Install it with: pip install reportlab", status=500)

def verify_certificate(request, cert_id):
    try:
        uid = uuid.UUID(str(cert_id))
        cert = Certificate.objects.get(certificate_id=uid)
        return render(request, 'certificates/verify.html', {'certificate': cert, 'valid': cert.is_valid})
    except (Certificate.DoesNotExist, ValueError):
        return render(request, 'certificates/verify.html', {'valid': False})
