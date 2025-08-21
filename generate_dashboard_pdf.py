from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", size=12)

with open("Par_Delta_Dashboard_Overview.txt", "r", encoding="utf-8") as f:
    for line in f:
        pdf.multi_cell(0, 10, line.strip())

pdf.output("Par_Delta_Dashboard_Overview.pdf")
print("PDF generated: Par_Delta_Dashboard_Overview.pdf")
