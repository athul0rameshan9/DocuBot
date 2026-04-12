"""
generate_sample_docs.py
────────────────────────
Creates realistic .docx files to demo DocuBot without real documents.
Run: python generate_sample_docs.py
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path


def create_employee_handbook():
    doc = Document()
    doc.add_heading("Employee Handbook 2024", 0)

    doc.add_paragraph(
        "This handbook outlines company policies, procedures, and guidelines "
        "for all employees of TechCorp Inc. Please read carefully and retain for reference."
    )

    doc.add_heading("1. Company Overview", 1)
    doc.add_paragraph(
        "TechCorp Inc. was founded in 2015 and specializes in enterprise software solutions. "
        "We have over 200 employees across Engineering, Product, Sales, HR, Design, and Marketing departments. "
        "Our mission is to empower businesses with intelligent software."
    )

    doc.add_heading("2. Compensation Policy", 1)
    doc.add_paragraph(
        "Salary reviews occur annually in Q4. Performance bonuses are awarded based on KPIs. "
        "Engineering roles have a base range of $70,000–$150,000 depending on seniority. "
        "All employees are eligible for health insurance, 401k matching, and stock options after 1 year."
    )

    doc.add_heading("3. Leave Policy", 1)
    items = [
        "Annual Leave: 20 days per year",
        "Sick Leave: 10 days per year (no carryover)",
        "Parental Leave: 16 weeks fully paid",
        "Public Holidays: As per state law",
    ]
    for item in items:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("4. Performance Reviews", 1)
    doc.add_paragraph(
        "Performance reviews are conducted bi-annually (June and December). "
        "Employees are rated on a scale of 1-5 across: Technical Skills, Collaboration, "
        "Communication, and Initiative. Ratings above 4.0 qualify for promotion consideration."
    )

    doc.add_heading("5. Remote Work Policy", 1)
    doc.add_paragraph(
        "Hybrid work is standard: 3 days in-office, 2 days remote. Engineering teams may "
        "negotiate fully remote arrangements with manager approval. All remote employees must "
        "maintain core hours of 10am–3pm in their local timezone."
    )

    # Table
    doc.add_heading("6. Department Heads", 1)
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Department"
    hdr[1].text = "Head"
    hdr[2].text = "Team Size"

    dept_data = [
        ("Engineering", "Henry Davis", "45"),
        ("Product", "Carol White", "12"),
        ("Sales", "James Wilson", "18"),
        ("HR", "Eva Chen", "5"),
        ("Design", "Grace Lee", "8"),
    ]
    for dept, head, size in dept_data:
        row = table.add_row().cells
        row[0].text = dept
        row[1].text = head
        row[2].text = size

    path = "sample_docs/employee_handbook.docx"
    doc.save(path)
    print(f"✅ Created: {path}")


def create_product_catalog():
    doc = Document()
    doc.add_heading("Product Catalog — Q1 2024", 0)

    doc.add_paragraph(
        "This catalog describes our current software product lineup, pricing, and technical specifications. "
        "All prices are annual subscription unless otherwise noted."
    )

    products = [
        {
            "name": "CloudSync Pro",
            "sku": "CSP-001",
            "category": "Software",
            "price": "$299.99/mo",
            "desc": "Enterprise cloud synchronization platform supporting real-time sync across 50+ cloud providers. "
                    "Includes end-to-end encryption, audit logs, and 99.99% SLA.",
            "features": ["Multi-cloud support", "Real-time sync", "256-bit encryption", "REST API access"],
        },
        {
            "name": "AI Analyzer",
            "sku": "AIA-004",
            "category": "AI/ML",
            "price": "$899.99/mo",
            "desc": "Document intelligence platform powered by large language models. "
                    "Automatically extracts, classifies, and analyzes documents at scale.",
            "features": ["LLM-powered extraction", "Multi-format support", "Custom training", "Batch processing"],
        },
        {
            "name": "API Gateway",
            "sku": "APG-003",
            "category": "Infrastructure",
            "price": "$499.99/mo",
            "desc": "Scalable API management and orchestration layer. "
                    "Supports rate limiting, authentication, monitoring, and routing.",
            "features": ["Rate limiting", "OAuth 2.0", "Analytics dashboard", "Load balancing"],
        },
    ]

    for p in products:
        doc.add_heading(f"{p['name']} ({p['sku']})", 2)
        doc.add_paragraph(f"Category: {p['category']} | Price: {p['price']}")
        doc.add_paragraph(p["desc"])
        doc.add_paragraph("Key Features:")
        for f in p["features"]:
            doc.add_paragraph(f, style="List Bullet")

    doc.add_heading("Pricing Summary", 1)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    hdr[0].text = "Product"
    hdr[1].text = "SKU"
    hdr[2].text = "Price"
    hdr[3].text = "Category"

    for p in products:
        row = table.add_row().cells
        row[0].text = p["name"]
        row[1].text = p["sku"]
        row[2].text = p["price"]
        row[3].text = p["category"]

    path = "sample_docs/product_catalog.docx"
    doc.save(path)
    print(f"✅ Created: {path}")


def create_project_report():
    doc = Document()
    doc.add_heading("Q1 2024 Project Status Report", 0)
    doc.add_paragraph(f"Report Date: March 31, 2024 | Prepared by: Henry Davis")

    doc.add_heading("Executive Summary", 1)
    doc.add_paragraph(
        "This quarter saw significant progress across all active projects. The DocuBot Integration "
        "project reached 60% completion ahead of schedule. AI Migration remains in planning phase "
        "pending budget approval. The Mobile App Launch is progressing well with beta release targeted "
        "for May 2024."
    )

    doc.add_heading("Project Status Overview", 1)
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, h in enumerate(["Project", "Status", "Budget", "% Complete", "Risk"]):
        hdr[i].text = h

    projects = [
        ("DocuBot Integration", "In Progress", "$250,000", "60%", "Low"),
        ("AI Migration", "Planning", "$400,000", "15%", "Medium"),
        ("Mobile App Launch", "In Progress", "$320,000", "45%", "Low"),
        ("Customer Portal v2", "Completed", "$180,000", "100%", "None"),
        ("Security Audit", "Completed", "$95,000", "100%", "None"),
    ]
    for proj in projects:
        row = table.add_row().cells
        for i, val in enumerate(proj):
            row[i].text = val

    doc.add_heading("Key Risks & Mitigations", 1)
    risks = [
        "AI Migration: Vendor lock-in risk — mitigated by multi-cloud architecture",
        "Mobile App Launch: Third-party SDK compatibility — mitigation in progress",
        "DocuBot Integration: LLM API rate limits — caching layer being implemented",
    ]
    for r in risks:
        doc.add_paragraph(r, style="List Bullet")

    doc.add_heading("Next Quarter Goals", 1)
    goals = [
        "Launch DocuBot v1.0 to production (June 2024)",
        "Complete AI Migration planning and begin Phase 1 implementation",
        "Release Mobile App beta to 500 test users",
        "Begin Q2 security compliance review",
    ]
    for g in goals:
        doc.add_paragraph(g, style="List Bullet")

    path = "sample_docs/project_report.docx"
    doc.save(path)
    print(f"✅ Created: {path}")


if __name__ == "__main__":
    Path("sample_docs").mkdir(exist_ok=True)
    create_employee_handbook()
    create_product_catalog()
    create_project_report()
    print("\n🎉 Sample documents ready in ./sample_docs/")
    print("Upload them to DocuBot to start chatting!")
