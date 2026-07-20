"""
generate_sample_pdf.py

Generates a fictional company fact sheet PDF into documents/, useful as
test input for rag_pipeline.py since its facts have clear, unambiguous answers.
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT_PATH = Path(__file__).resolve().parent / "documents" / "sample_company.pdf"

SECTIONS = [
    ("Company Overview", """Nimbus Robotics Inc. is a robotics company founded in 2018 and headquartered
    in Austin, Texas. The company designs autonomous warehouse robots used by logistics providers to
    move inventory between shelves and packing stations. Nimbus Robotics currently employs 340 people
    across three offices: Austin, Denver, and Toronto."""),

    ("Founders and Leadership", """Nimbus Robotics was founded by Maria Chen and David Okafor. Maria Chen
    serves as Chief Executive Officer and David Okafor serves as Chief Technology Officer. The company's
    Chief Financial Officer is Priya Nair, who joined in 2021."""),

    ("Flagship Product", """The company's flagship product is the NimbusCart, an autonomous mobile robot
    that can carry up to 500 kilograms and navigate warehouse floors using LIDAR and computer vision.
    The NimbusCart has a battery life of 10 hours per charge and a maximum speed of 2.2 meters per second."""),

    ("Funding History", """Nimbus Robotics raised a $5 million seed round in 2018, a $22 million Series A
    round in 2020 led by Highline Ventures, and a $60 million Series B round in 2023 led by Cascade
    Capital Partners. Total funding raised to date is $87 million."""),

    ("Customers", """Nimbus Robotics serves over 40 warehouse customers, including two of the five largest
    grocery distributors in North America. Its largest customer, FreshLine Distribution, has deployed
    120 NimbusCart units across four regional warehouses since signing a contract in 2022."""),

    ("Recent Milestones", """In January 2025, Nimbus Robotics announced the NimbusCart Mini, a smaller
    robot designed for retail backrooms rather than large warehouses. In June 2025, the company opened
    its Toronto office to support Canadian customers and expand its robotics engineering team."""),
]


def create_sample_pdf(out_path: Path = OUT_PATH, sections=SECTIONS) -> Path:
    """Render `sections` as a titled PDF fact sheet at `out_path`."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(out_path), pagesize=letter)

    story = [Paragraph("Nimbus Robotics: Company Fact Sheet", styles["Title"]), Spacer(1, 18)]
    for heading, body in sections:
        story.append(Paragraph(heading, styles["Heading2"]))
        story.append(Paragraph(" ".join(body.split()), styles["BodyText"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    return out_path


if __name__ == "__main__":
    path = create_sample_pdf()
    print("Wrote", path)
