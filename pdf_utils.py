
from fpdf import FPDF
from datetime import datetime


def generate_pdf(complaint_text: str, filename: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    try:
        pdf.image("logo.png", x=10, y=8, w=30)
    except Exception:
        pass
    pdf.ln(35)  # Отступ после логотипа
    for line in complaint_text.split("\n"):
        pdf.multi_cell(0, 8, line)
    pdf.output(filename)
    return filename
