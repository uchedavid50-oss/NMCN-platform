import io
from datetime import datetime

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas

INK_NAVY = HexColor("#0F2438")
VITAL_TEAL = HexColor("#0E7C7B")
GRAPHITE = HexColor("#3A4550")


def generate_certificate_pdf(student_email: str, average_score: float, mock_count: int) -> bytes:
    buffer = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Border
    c.setStrokeColor(VITAL_TEAL)
    c.setLineWidth(3)
    c.rect(30, 30, width - 60, height - 60)

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(VITAL_TEAL)
    c.drawCentredString(width / 2, height - 90, "NMCN CBT PREP")

    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(INK_NAVY)
    c.drawCentredString(width / 2, height - 140, "Certificate of Exam-Readiness Practice")

    c.setFont("Helvetica", 14)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(width / 2, height - 190, "This certifies that")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(INK_NAVY)
    c.drawCentredString(width / 2, height - 225, student_email)

    c.setFont("Helvetica", 14)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(
        width / 2,
        height - 260,
        f"has completed {mock_count} timed mock exams with an average score of {average_score:.1f}%,",
    )
    c.drawCentredString(
        width / 2,
        height - 280,
        "demonstrating sustained, disciplined engagement with NMCN exam preparation.",
    )

    c.setFont("Helvetica", 9)
    c.setFillColor(GRAPHITE)
    c.drawCentredString(
        width / 2,
        90,
        "This certificate reflects platform practice engagement only. It is NOT an official credential",
    )
    c.drawCentredString(
        width / 2,
        78,
        "issued by the Nursing and Midwifery Council of Nigeria, and does not guarantee exam results.",
    )

    c.setFont("Helvetica", 10)
    c.drawString(60, 60, f"Issued: {datetime.utcnow().strftime('%B %d, %Y')}")

    c.showPage()
    c.save()
    return buffer.getvalue()
