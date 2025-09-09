from fpdf import FPDF

def create_pdf(path, title, paragraphs):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, title, ln=True)
    pdf.ln(6)
    for p in paragraphs:
        pdf.multi_cell(0, 8, p)
        pdf.ln(2)
    pdf.output(path)
    print("Saved:", path)

if __name__ == "__main__":
    p1 = ["This is sample PDF 1. " * 6, "Page two text. " * 10]
    p2 = ["This is sample PDF 2. " * 8, ""]
    create_pdf("sample1.pdf", "Sample PDF 1", p1)
    create_pdf("sample2.pdf", "Sample PDF 2", p2)
