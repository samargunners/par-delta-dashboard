from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Heading', fontSize=22, leading=28, spaceAfter=18, alignment=1, textColor=colors.HexColor('#2E4053')))
styles.add(ParagraphStyle(name='SubHeading', fontSize=16, leading=20, spaceAfter=12, textColor=colors.HexColor('#2874A6')))
styles.add(ParagraphStyle(name='Body', fontSize=11, leading=15, spaceAfter=8, textColor=colors.HexColor('#212F3C')))
styles.add(ParagraphStyle(name='List', fontSize=11, leading=14, leftIndent=20, spaceAfter=6, textColor=colors.HexColor('#212F3C')))

sections = [
    ('Project Overview', [
        'par-delta-streamlit is a data dashboard project built with Streamlit and Python, designed to visualize, analyze, and report business metrics.',
        'The project includes modules for data ingestion, processing, visualization, and user management.'
    ]),
    ('Project Structure', [
        'Key folders: streamlit_app/, dashboard/, data/, database/, scripts/.',
        'Each folder contains modules for specific responsibilities (UI, data, database, automation, uploads).',
        'Understanding the flow: Data is ingested, processed, stored, and visualized through Streamlit dashboards.'
    ]),
    ('Key Technologies', [
        'Python: Main language for backend and data processing.',
        'Streamlit: For interactive dashboards.',
        'pandas, numpy: Data analysis and manipulation.',
        'SQL/Supabase: Database management.',
        'Docker: Containerization for deployment.'
    ]),
    ('Software Engineering Practices', [
        'Project Organization: Modularize code into packages and submodules.',
        'Version Control: Use Git for tracking changes and collaboration.',
        'Testing: Add unit and integration tests using pytest.',
        'Documentation: Maintain README, docstrings, and usage guides.'
    ]),
    ('Microservices Architecture', [
        'Split monolithic code into independent services (e.g., data ingestion, reporting, user management).',
        'Use REST APIs (Flask/FastAPI) for communication between services.',
        'Deploy services separately using Docker containers.'
    ]),
    ('Agility & Speed', [
        'Implement CI/CD pipelines for automated testing and deployment.',
        'Modularize code for faster development and easier updates.',
        'Use feature branches and code reviews for rapid iteration.'
    ]),
    ('Scalability', [
        'Move heavy data processing to background jobs (Celery, RQ).',
        'Use cloud databases and storage (Supabase, AWS RDS).',
        'Containerize with Docker for easy scaling.'
    ]),
    ('Resilience', [
        'Implement error handling and retries in data pipelines.',
        'Use health checks and monitoring (Prometheus, Grafana).',
        'Design for graceful degradation and failover.'
    ]),
    ('Debugging & Logging', [
        'Add logging to all major modules using Python’s logging library.',
        'Log errors, warnings, and key events.',
        'Use centralized log management (ELK stack, cloud logging).',
        'Add debugging tools (Streamlit debug mode, Python debuggers).'
    ]),
    ('Actionable Next Steps', [
        'Explore the codebase and map out the data flow.',
        'Identify bottlenecks and areas for improvement.',
        'Experiment with refactoring and modularization.',
        'Add logging and basic tests to one module.',
        'Research microservices and build a small REST API.',
        'Set up Docker and containerize the app.'
    ])
]

def build_detailed_roadmap_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    story.append(Paragraph('Comprehensive Guide: Engineering & Scaling par-delta-streamlit', styles['Heading']))
    story.append(Spacer(1, 18))
    for section, items in sections:
        story.append(Paragraph(section, styles['SubHeading']))
        story.append(Spacer(1, 6))
        story.append(ListFlowable([
            ListItem(Paragraph(item, styles['List'])) for item in items
        ], bulletType='bullet'))
        story.append(PageBreak())
    doc.build(story)

if __name__ == '__main__':
    build_detailed_roadmap_pdf('par-delta-streamlit_Engineering_Guide.pdf')
