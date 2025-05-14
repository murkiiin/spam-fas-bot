
from fpdf import FPDF
from datetime import datetime


def generate_pdf(complaint_text: str, filename: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in complaint_text.split("\n"):
        pdf.multi_cell(0, 8, line)
    pdf.output(filename)
    return filename
