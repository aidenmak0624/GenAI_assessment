"""
Generate sample company policy PDF documents for the knowledge base.
"""

import os

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
except ImportError:
    raise ImportError("Install reportlab: pip install reportlab")

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")


def _build_pdf(filename: str, title: str, sections: list[tuple[str, str]]):
    os.makedirs(DOCS_DIR, exist_ok=True)
    path = os.path.join(DOCS_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=letter,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"],
                                  fontSize=18, alignment=TA_CENTER)
    heading_style = ParagraphStyle("H2", parent=styles["Heading2"],
                                    fontSize=14, spaceAfter=6)
    body_style = ParagraphStyle("Body2", parent=styles["BodyText"],
                                 fontSize=11, leading=15, spaceAfter=10)
    story = [Paragraph(title, title_style), Spacer(1, 0.3*inch)]
    for heading, body in sections:
        story.append(Paragraph(heading, heading_style))
        for para in body.split("\n\n"):
            story.append(Paragraph(para.strip(), body_style))
        story.append(Spacer(1, 0.15*inch))
    doc.build(story)
    print(f"  Created {path}")


def generate_refund_policy():
    _build_pdf("refund_policy.pdf", "TechCorp — Refund & Returns Policy", [
        ("1. Overview",
         "TechCorp is committed to customer satisfaction. This policy outlines "
         "the conditions under which customers may request refunds or returns "
         "for products and services purchased from TechCorp."),
        ("2. Eligibility for Refunds",
         "Hardware products may be returned within 30 days of delivery for a "
         "full refund, provided the item is in its original packaging and "
         "undamaged. Software subscriptions may be refunded within 14 days of "
         "purchase if the customer has not used the service beyond the trial "
         "period.\n\n"
         "Service plans (TechCare Basic, TechCare Premium) are eligible for "
         "prorated refunds at any time. The refund amount is calculated based "
         "on the remaining unused days in the current billing cycle."),
        ("3. Non-Refundable Items",
         "The following are not eligible for refunds: one-time setup services "
         "(QuickSetup Service) once the service has been rendered, digital "
         "products that have been downloaded or activated, and any item "
         "returned after the applicable refund window."),
        ("4. How to Request a Refund",
         "Customers may request a refund by contacting our support team via "
         "email at support@techcorp.com, calling 1-800-TECHCORP, or opening "
         "a support ticket through the customer portal. Please include your "
         "order number and reason for the refund request.\n\n"
         "Refund requests are typically processed within 5-7 business days. "
         "The refund will be issued to the original payment method."),
        ("5. Exchanges",
         "Hardware products may be exchanged for the same item within 30 days "
         "if the original is defective. For exchanges to a different product, "
         "the customer must return the original item and place a new order."),
        ("6. Warranty Claims",
         "All hardware products include a 1-year manufacturer warranty. "
         "Warranty claims for defective products are handled separately from "
         "returns and do not fall under the 30-day return window. Contact "
         "support with your product serial number to initiate a warranty claim."),
    ])


def generate_privacy_policy():
    _build_pdf("privacy_policy.pdf", "TechCorp — Privacy Policy", [
        ("1. Introduction",
         "TechCorp values your privacy and is committed to protecting your "
         "personal data. This Privacy Policy explains how we collect, use, "
         "store, and share your information when you use our products and "
         "services."),
        ("2. Information We Collect",
         "We collect information you provide directly, such as your name, "
         "email address, phone number, and payment information when you "
         "create an account or make a purchase.\n\n"
         "We also collect usage data automatically, including device "
         "information, IP addresses, browser type, and interaction logs "
         "with our software products. CloudSync Pro collects file metadata "
         "(not file contents) to provide the sync service."),
        ("3. How We Use Your Information",
         "Your information is used to provide and improve our services, "
         "process transactions, send service notifications, and provide "
         "customer support. We may use anonymized, aggregated data for "
         "analytics and product improvement purposes."),
        ("4. Data Sharing",
         "TechCorp does not sell your personal information to third parties. "
         "We may share data with trusted service providers who assist in "
         "operating our services (e.g., payment processors, cloud hosting "
         "providers) under strict confidentiality agreements.\n\n"
         "We may disclose information if required by law or to protect "
         "TechCorp's legal rights."),
        ("5. Data Retention",
         "Customer account data is retained for the duration of the account "
         "plus 2 years after account closure. Support ticket data is retained "
         "for 5 years. Payment records are retained for 7 years as required "
         "by financial regulations."),
        ("6. Your Rights",
         "You have the right to access, correct, or delete your personal "
         "data. You may request a copy of your data or ask for account "
         "deletion by contacting privacy@techcorp.com. We will respond to "
         "requests within 30 days."),
        ("7. Security",
         "We implement industry-standard security measures including "
         "encryption at rest and in transit, regular security audits, and "
         "access controls. SecureVPN Plus uses AES-256 encryption for all "
         "tunnel traffic."),
    ])


def generate_support_policy():
    _build_pdf("support_policy.pdf", "TechCorp — Customer Support Policy", [
        ("1. Support Channels",
         "TechCorp provides customer support through multiple channels: "
         "email (support@techcorp.com), phone (1-800-TECHCORP, Mon-Fri "
         "8am-8pm EST), live chat on our website, and the self-service "
         "customer portal."),
        ("2. Support Tiers",
         "TechCare Basic subscribers receive email and portal support with "
         "a 48-hour response time SLA. TechCare Premium subscribers receive "
         "priority support across all channels with a 4-hour response time "
         "SLA and access to dedicated support agents.\n\n"
         "Customers without a support plan receive community forum access "
         "and email support with a 5-business-day response time."),
        ("3. Ticket Priority Levels",
         "Critical: System down or data loss — target resolution within 4 "
         "hours for Premium, 24 hours for Basic.\n\n"
         "High: Major feature broken — target resolution within 8 hours for "
         "Premium, 48 hours for Basic.\n\n"
         "Medium: Minor issue with workaround available — target resolution "
         "within 24 hours for Premium, 5 business days for Basic.\n\n"
         "Low: General question or feature request — target response within "
         "48 hours for Premium, 7 business days for Basic."),
        ("4. Escalation Process",
         "If a ticket is not resolved within the SLA, it is automatically "
         "escalated to a senior support engineer. Customers may request "
         "escalation at any time by replying to their ticket with "
         "'ESCALATE' in the subject line.\n\n"
         "Critical tickets that remain unresolved for more than double the "
         "SLA are escalated to the Support Director."),
        ("5. Customer Satisfaction",
         "After ticket resolution, customers receive a satisfaction survey. "
         "TechCorp targets a minimum CSAT score of 90%. Tickets with low "
         "satisfaction ratings are reviewed by the support team lead."),
        ("6. Knowledge Base",
         "TechCorp maintains a comprehensive knowledge base at "
         "help.techcorp.com with articles, video tutorials, and FAQs. "
         "Customers are encouraged to check the knowledge base before "
         "submitting a support ticket."),
    ])


def generate_all_policies():
    print("Generating policy PDFs...")
    generate_refund_policy()
    generate_privacy_policy()
    generate_support_policy()
    print("Done.")


if __name__ == "__main__":
    generate_all_policies()
