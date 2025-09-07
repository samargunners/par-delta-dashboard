from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Heading', fontSize=20, leading=24, spaceAfter=16, alignment=1, textColor=colors.HexColor('#2E4053')))
styles.add(ParagraphStyle(name='SubHeading', fontSize=14, leading=18, spaceAfter=10, textColor=colors.HexColor('#2874A6')))
styles.add(ParagraphStyle(name='Tree', fontSize=11, leading=14, leftIndent=20, spaceAfter=6, textColor=colors.HexColor('#212F3C')))

roadmap = [
    ['Programming Fundamentals', ['Python (syntax, data structures, OOP)', 'Libraries (pandas, numpy, matplotlib)']],
    ['Version Control', ['Git (commits, branches, merging)', 'Collaboration (GitHub, GitLab)']],
    ['Project Structure & Organization', ['Modular code (functions, classes, packages)', 'Documentation (README, docstrings)']],
    ['Testing', ['Unit Testing (pytest, unittest)', 'Integration Testing', 'Test Coverage']],
    ['Software Design', ['Design Patterns (MVC, Singleton, etc.)', 'Best Practices (DRY, SOLID)']],
    ['Web Development', ['Backend (Flask, Django)', 'Frontend (HTML, CSS, JS basics)', 'APIs (REST, GraphQL)']],
    ['Data Engineering', ['Databases (SQL, NoSQL)', 'ETL Pipelines', 'Data Visualization']],
    ['Deployment', ['Packaging (pip, setup.py, requirements.txt)', 'Containerization (Docker)', 'Cloud Basics (AWS, Azure, GCP)', 'CI/CD (Continuous Integration/Deployment)']],
    ['Maintenance & Monitoring', ['Logging', 'Error Tracking', 'Performance Monitoring']],
    ['Collaboration & Soft Skills', ['Code Reviews', 'Agile/Scrum', 'Communication']]
]

def build_roadmap_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    story.append(Paragraph('Software Engineering Roadmap', styles['Heading']))
    story.append(Spacer(1, 12))
    for domain, topics in roadmap:
        story.append(Paragraph(domain, styles['SubHeading']))
        for topic in topics:
            story.append(Paragraph(f'• {topic}', styles['Tree']))
        story.append(Spacer(1, 6))
    doc.build(story)

if __name__ == '__main__':
    build_roadmap_pdf('Software_Engineering_Roadmap.pdf')
