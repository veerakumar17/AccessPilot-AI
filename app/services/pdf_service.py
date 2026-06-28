import json
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import List, Optional

import structlog
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    NextPageTemplate,
)
from reportlab.platypus.doctemplate import PageTemplate

from app.core.exceptions import NotFoundException
from app.models.audit import Audit
from app.models.page import Page
from app.models.project import Project
from app.models.report import Report
from app.models.violation import Violation
from app.repositories.audit_repo import AuditRepository
from app.repositories.project_repo import ProjectRepository
from app.repositories.report_repo import ReportRepository
from app.schemas.report import ReportResponse

logger = structlog.get_logger(__name__)

# ── Colour palette ──────────────────────────────────────────────────────────
NAVY = colors.HexColor("#0a1628")
NAVY_LIGHT = colors.HexColor("#1a2744")
NAVY_CARD = colors.HexColor("#0f1d35")
ACCENT = colors.HexColor("#3b82f6")
ACCENT_LIGHT = colors.HexColor("#60a5fa")
WHITE = colors.white
GRAY = colors.HexColor("#94a3b8")
GRAY_LIGHT = colors.HexColor("#e2e8f0")
GREEN = colors.HexColor("#22c55e")
RED = colors.HexColor("#ef4444")
YELLOW = colors.HexColor("#eab308")
ORANGE = colors.HexColor("#f97316")
PURPLE = colors.HexColor("#a855f7")
BLUE = colors.HexColor("#3b82f6")
DIVIDER = colors.HexColor("#1e3a5f")

# ── Page dimensions ─────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_TOP = 22 * mm
MARGIN_BOTTOM = 22 * mm
MARGIN_LEFT = 22 * mm
MARGIN_RIGHT = 22 * mm
CONTENT_W = PAGE_W - MARGIN_LEFT - MARGIN_RIGHT

# ── Helpers ─────────────────────────────────────────────────────────────────

def _score_to_grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _severity_color(severity: str) -> colors.Color:
    mapping = {
        "critical": RED,
        "serious": ORANGE,
        "moderate": YELLOW,
        "minor": BLUE,
    }
    return mapping.get(severity.lower(), GRAY)


def _safe_json_parse(value: Optional[str]) -> Optional[dict]:
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


# ── Styles ──────────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()

# Cover page
COVER_TITLE = ParagraphStyle(
    "CoverTitle", parent=styles["Title"],
    fontSize=32, textColor=ACCENT, spaceAfter=4, alignment=TA_CENTER,
    leading=38,
)
COVER_SUBTITLE = ParagraphStyle(
    "CoverSubtitle", parent=styles["Normal"],
    fontSize=14, textColor=GRAY, spaceAfter=6, alignment=TA_CENTER,
    leading=18,
)
COVER_LABEL = ParagraphStyle(
    "CoverLabel", parent=styles["Normal"],
    fontSize=10, textColor=GRAY, spaceAfter=2, alignment=TA_LEFT,
    leading=13,
)
COVER_VALUE = ParagraphStyle(
    "CoverValue", parent=styles["Normal"],
    fontSize=11, textColor=WHITE, spaceAfter=2, alignment=TA_LEFT,
    leading=14,
)
COVER_FOOTER = ParagraphStyle(
    "CoverFooter", parent=styles["Normal"],
    fontSize=9, textColor=GRAY, spaceAfter=0, alignment=TA_CENTER,
    leading=12,
)

# Section headings
SECTION_TITLE = ParagraphStyle(
    "SectionTitle", parent=styles["Heading1"],
    fontSize=20, textColor=ACCENT, spaceBefore=24, spaceAfter=14,
    leading=26, borderPadding=0,
)
SUBSECTION_TITLE = ParagraphStyle(
    "SubsectionTitle", parent=styles["Heading2"],
    fontSize=15, textColor=WHITE, spaceBefore=16, spaceAfter=8,
    leading=20,
)

# Body text
BODY = ParagraphStyle(
    "Body", parent=styles["Normal"],
    fontSize=10, textColor=GRAY, spaceAfter=6, leading=15,
    alignment=TA_LEFT,
)
BODY_WHITE = ParagraphStyle(
    "BodyWhite", parent=styles["Normal"],
    fontSize=10, textColor=WHITE, spaceAfter=4, leading=15,
    alignment=TA_LEFT,
)

# Labels and values
LABEL = ParagraphStyle(
    "Label", parent=styles["Normal"],
    fontSize=9, textColor=GRAY, spaceAfter=2, leading=12,
)
VALUE = ParagraphStyle(
    "Value", parent=styles["Normal"],
    fontSize=10, textColor=WHITE, spaceAfter=4, leading=14,
)

# Footer
FOOTER_STYLE = ParagraphStyle(
    "Footer", parent=styles["Normal"],
    fontSize=8, textColor=GRAY, alignment=TA_CENTER, leading=10,
)

# Code
CODE = ParagraphStyle(
    "Code", parent=styles["Code"],
    fontSize=8, textColor=colors.HexColor("#e2e8f0"),
    backColor=colors.HexColor("#0a1628"),
    borderPadding=8, spaceAfter=8, leading=12,
    fontName="Courier",
)

# Severity badge
SEVERITY_STYLE = ParagraphStyle(
    "Severity", parent=styles["Normal"],
    fontSize=8, textColor=WHITE, spaceAfter=0, leading=10,
)

# Large metric values
LARGE_METRIC = ParagraphStyle(
    "LargeMetric", parent=styles["Normal"],
    fontSize=28, textColor=WHITE, alignment=TA_CENTER, leading=34,
)
LARGE_METRIC_ACCENT = ParagraphStyle(
    "LargeMetricAccent", parent=styles["Normal"],
    fontSize=28, textColor=ACCENT, alignment=TA_CENTER, leading=34,
)
LARGE_METRIC_GREEN = ParagraphStyle(
    "LargeMetricGreen", parent=styles["Normal"],
    fontSize=28, textColor=GREEN, alignment=TA_CENTER, leading=34,
)

# Stat card value
STAT_VALUE = ParagraphStyle(
    "StatValue", parent=styles["Normal"],
    fontSize=18, textColor=WHITE, alignment=TA_CENTER, leading=22,
)

# Page header
PAGE_HEADER_TITLE = ParagraphStyle(
    "PageHeaderTitle", parent=styles["Normal"],
    fontSize=9, textColor=ACCENT, alignment=TA_LEFT, leading=12,
)
PAGE_HEADER_SUB = ParagraphStyle(
    "PageHeaderSub", parent=styles["Normal"],
    fontSize=8, textColor=GRAY, alignment=TA_LEFT, leading=10,
)

# Violation number
VIOLATION_NUM = ParagraphStyle(
    "ViolationNum", parent=styles["Normal"],
    fontSize=13, textColor=ACCENT, leading=16,
)


# ── Severity badge ──────────────────────────────────────────────────────────

def _severity_badge(severity: str) -> Table:
    """A small coloured badge for severity."""
    c = _severity_color(severity)
    t = Table([[Paragraph(severity.upper(), SEVERITY_STYLE)]], colWidths=65, rowHeights=16)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ── Card helper ─────────────────────────────────────────────────────────────

def _make_card(content: list, col_width: float) -> Table:
    """Wrap content in a navy card with consistent padding."""
    t = Table(content, colWidths=[col_width])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, NAVY_LIGHT),
        ("BACKGROUND", (0, 0), (-1, -1), NAVY_CARD),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


# ── Page templates ──────────────────────────────────────────────────────────

def _cover_page_template(doc):
    """Page template for the cover page (no header/footer)."""
    frame = Frame(
        MARGIN_LEFT, MARGIN_BOTTOM,
        CONTENT_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM,
        id="cover",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    return PageTemplate(id="Cover", frames=[frame], onPage=_cover_page_style)


def _cover_page_style(canvas, doc):
    """Draw nothing on cover page — clean slate."""
    pass


def _content_page_template(doc):
    """Page template for content pages (with header and footer)."""
    frame = Frame(
        MARGIN_LEFT, MARGIN_BOTTOM + 10 * mm,
        CONTENT_W, PAGE_H - MARGIN_TOP - MARGIN_BOTTOM - 14 * mm,
        id="content",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    return PageTemplate(id="Content", frames=[frame], onPage=_content_page_style)


def _content_page_style(canvas, doc):
    """Draw header and footer on content pages."""
    w, h = A4

    # ── Header ──────────────────────────────────────────────────────────
    header_y = h - MARGIN_TOP + 4 * mm
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(MARGIN_LEFT, header_y, "AccessPilot AI")
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(MARGIN_LEFT, header_y - 11, "Accessibility Audit Report")

    # Header divider
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_LEFT, header_y - 16, w - MARGIN_RIGHT, header_y - 16)

    # ── Footer ──────────────────────────────────────────────────────────
    footer_y = MARGIN_BOTTOM - 6 * mm
    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, footer_y, f"Page {doc.page}")

    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(w / 2, footer_y - 10, "Generated by AccessPilot AI")

    # Footer divider
    canvas.setStrokeColor(DIVIDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_LEFT, footer_y + 4, w - MARGIN_RIGHT, footer_y + 4)


# ── PDF Builder ─────────────────────────────────────────────────────────────

class PdfReportBuilder:
    """Builds a complete PDF accessibility report for a given audit."""

    def __init__(self, audit: Audit, project: Project, report: Report, pages: List[Page], violations: List[Violation]):
        self.audit = audit
        self.project = project
        self.report = report
        self.pages = pages
        self.violations = violations
        self.buf = BytesIO()
        self.elements: list = []

    def build(self) -> BytesIO:
        doc = BaseDocTemplate(
            self.buf,
            pagesize=A4,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            title=f"Accessibility Report - {self.project.name}",
            author="AccessPilot AI",
        )

        # Register page templates
        doc.addPageTemplates([
            _cover_page_template(doc),
            _content_page_template(doc),
        ])

        # Build all elements
        self._cover_page()
        self.elements.append(NextPageTemplate("Content"))
        self.elements.append(PageBreak())
        self._executive_summary()
        self.elements.append(PageBreak())
        self._violations_section()

        doc.build(self.elements)
        self.buf.seek(0)
        return self.buf

    # ── Cover Page ──────────────────────────────────────────────────────

    def _cover_page(self):
        # Vertical spacer to push content toward center
        self.elements.append(Spacer(1, 60))

        # Title
        self.elements.append(Paragraph("AccessPilot AI", COVER_TITLE))
        self.elements.append(Spacer(1, 2))
        self.elements.append(Paragraph("AI Accessibility Audit Report", COVER_SUBTITLE))
        self.elements.append(Spacer(1, 20))

        # Divider line
        line = Table([[""]], colWidths=140, rowHeights=2)
        line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), ACCENT)]))
        self.elements.append(line)
        self.elements.append(Spacer(1, 24))

        # Audit details in a two-column table
        col_w = CONTENT_W / 2 - 10
        details_data = [
            [Paragraph("Project Name", COVER_LABEL), Paragraph("Target URL", COVER_LABEL)],
            [Paragraph(self.project.name, COVER_VALUE), Paragraph(self.project.base_url, COVER_VALUE)],
            [Paragraph("Audit ID", COVER_LABEL), Paragraph("Audit Date", COVER_LABEL)],
            [Paragraph(str(self.audit.id), COVER_VALUE),
             Paragraph(self.audit.started_at.strftime("%B %d, %Y %H:%M UTC") if self.audit.started_at else "N/A", COVER_VALUE)],
            [Paragraph("Status", COVER_LABEL), Paragraph("", COVER_LABEL)],
            [Paragraph(self.audit.status.value if hasattr(self.audit.status, 'value') else str(self.audit.status), COVER_VALUE),
             Paragraph("", COVER_VALUE)],
        ]
        details_table = Table(details_data, colWidths=[col_w, col_w])
        details_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        self.elements.append(details_table)

        # Push footer to bottom
        self.elements.append(Spacer(1, 100))
        self.elements.append(Paragraph("Generated by AccessPilot AI", COVER_FOOTER))

    # ── Executive Summary ───────────────────────────────────────────────

    def _executive_summary(self):
        self.elements.append(Paragraph("Executive Summary", SECTION_TITLE))
        self.elements.append(Spacer(1, 6))

        score = self.report.accessibility_score
        grade = _score_to_grade(score)

        # Score and Grade — emphasized cards
        card_w = (CONTENT_W - 12) / 2
        score_card = _make_card(
            [[Paragraph("Accessibility Score", LABEL)],
             [Paragraph(f"{score:.1f}%", LARGE_METRIC_ACCENT)]],
            card_w,
        )
        grade_card = _make_card(
            [[Paragraph("Grade", LABEL)],
             [Paragraph(grade, LARGE_METRIC_GREEN)]],
            card_w,
        )

        score_grade_table = Table([[score_card, grade_card]], colWidths=[card_w, card_w])
        score_grade_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        self.elements.append(score_grade_table)
        self.elements.append(Spacer(1, 14))

        # Stats grid — 4 columns of equal width
        stats = [
            ("Pages Scanned", str(self.report.pages_scanned)),
            ("Total Violations", str(self.report.total_violations)),
            ("Critical", str(self.report.critical_count)),
            ("Serious", str(self.report.serious_count)),
            ("Moderate", str(self.report.moderate_count)),
            ("Minor", str(self.report.minor_count)),
        ]

        stat_card_w = (CONTENT_W - 18) / 4
        stat_cards = []
        for label_text, value_text in stats:
            card = _make_card(
                [[Paragraph(label_text, LABEL)],
                 [Paragraph(value_text, STAT_VALUE)]],
                stat_card_w,
            )
            stat_cards.append(card)

        # Arrange in rows of 4
        stat_rows = []
        for i in range(0, len(stat_cards), 4):
            row_cards = stat_cards[i:i + 4]
            # Pad with empty cells if needed
            while len(row_cards) < 4:
                row_cards.append(Paragraph("", LABEL))
            stat_rows.append(row_cards)

        stat_grid = Table(stat_rows, colWidths=[stat_card_w] * 4)
        stat_grid.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        self.elements.append(stat_grid)
        self.elements.append(Spacer(1, 14))

        # Summary text
        if self.report.summary_text:
            self.elements.append(Paragraph("Summary", SUBSECTION_TITLE))
            self.elements.append(Paragraph(self.report.summary_text, BODY))

    # ── Violations Section ──────────────────────────────────────────────

    def _violations_section(self):
        self.elements.append(Paragraph("Violations", SECTION_TITLE))
        self.elements.append(Spacer(1, 6))

        if not self.violations:
            self.elements.append(Paragraph("No violations found.", BODY))
            return

        for idx, v in enumerate(self.violations, 1):
            self._violation_entry(idx, v)
            if idx < len(self.violations):
                self.elements.append(Spacer(1, 16))

    def _violation_entry(self, idx: int, v: Violation):
        # ── Header ──────────────────────────────────────────────────────
        header_data = [
            [Paragraph(f"Violation #{idx}", VIOLATION_NUM),
             _severity_badge(v.severity.value if hasattr(v.severity, 'value') else v.severity)],
        ]
        header_table = Table(header_data, colWidths=[CONTENT_W - 85, 85])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("BACKGROUND", (0, 0), (-1, -1), NAVY_LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        self.elements.append(header_table)
        self.elements.append(Spacer(1, 6))

        # ── Details ─────────────────────────────────────────────────────
        details = [
            ("Rule ID", v.rule_id),
        ]
        if v.wcag_criteria:
            details.append(("WCAG Criterion", v.wcag_criteria))

        for label_text, value_text in details:
            row_data = [
                [Paragraph(label_text, LABEL)],
                [Paragraph(str(value_text), BODY_WHITE)],
            ]
            row_table = Table(row_data, colWidths=[100, CONTENT_W - 100])
            row_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            self.elements.append(row_table)

        # HTML Snippet
        if v.html_snippet:
            self.elements.append(Spacer(1, 4))
            self.elements.append(Paragraph("HTML Snippet", LABEL))
            snippet = v.html_snippet[:500] + "..." if len(v.html_snippet) > 500 else v.html_snippet
            # Wrap in a bordered code container
            code_table = Table(
                [[Paragraph(f"<pre>{snippet}</pre>", CODE)]],
                colWidths=[CONTENT_W],
            )
            code_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, NAVY_LIGHT),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0a1628")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            self.elements.append(code_table)

        # ── AI Explanation ──────────────────────────────────────────────
        ai_explanation = _safe_json_parse(v.ai_explanation)
        if ai_explanation:
            self.elements.append(Spacer(1, 8))
            self.elements.append(Paragraph("AI Explanation", SUBSECTION_TITLE))
            for field, label_text in [("plain_english", "Plain English"), ("business_impact", "Business Impact"), ("recommendation", "Recommendation")]:
                val = ai_explanation.get(field)
                if val:
                    self.elements.append(Paragraph(f"<b>{label_text}:</b>", LABEL))
                    self.elements.append(Paragraph(str(val), BODY))

        # ── AI Fix ──────────────────────────────────────────────────────
        ai_fix = _safe_json_parse(v.ai_fix)
        if ai_fix:
            self.elements.append(Spacer(1, 8))
            self.elements.append(Paragraph("AI Fix", SUBSECTION_TITLE))
            for field, label_text in [("problem", "Problem"), ("recommended_fix", "Recommended Fix"), ("priority", "Priority")]:
                val = ai_fix.get(field)
                if val:
                    self.elements.append(Paragraph(f"<b>{label_text}:</b>", LABEL))
                    self.elements.append(Paragraph(str(val), BODY))

            code_example = ai_fix.get("code_example")
            if code_example:
                self.elements.append(Paragraph("Code Example", LABEL))
                code_table = Table(
                    [[Paragraph(f"<pre>{code_example}</pre>", CODE)]],
                    colWidths=[CONTENT_W],
                )
                code_table.setStyle(TableStyle([
                    ("BOX", (0, 0), (-1, -1), 0.5, NAVY_LIGHT),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0a1628")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                self.elements.append(code_table)

            steps = ai_fix.get("implementation_steps")
            if steps and isinstance(steps, list):
                self.elements.append(Paragraph("Implementation Steps", LABEL))
                for step in steps:
                    self.elements.append(Paragraph(f"• {step}", BODY))

        # ── General User Impact ────────────────────────────────────────
        ai_simulation = _safe_json_parse(v.ai_simulation)
        if ai_simulation:
            general_impact = ai_simulation.get("general_user_impact")
            if general_impact:
                self.elements.append(Spacer(1, 8))
                self.elements.append(Paragraph("General User Impact", SUBSECTION_TITLE))
                self.elements.append(Paragraph(str(general_impact), BODY))

        # ── Accessibility Impact by User Group ──────────────────────────
        if ai_simulation:
            self.elements.append(Spacer(1, 8))
            self.elements.append(Paragraph("Accessibility Impact by User Group", SUBSECTION_TITLE))

            affected = ai_simulation.get("affected_groups", [])
            if affected:
                for group in affected:
                    disability = group.get("disability", "Unknown").replace("_", " ").title()
                    impact = group.get("impact", "")
                    self.elements.append(Paragraph(f"<b>{disability}:</b> {impact}", BODY))

            user_exp = ai_simulation.get("user_experience")
            if user_exp:
                self.elements.append(Paragraph(f"<i>\"{user_exp}\"</i>", BODY))


# ── Service ─────────────────────────────────────────────────────────────────

class PdfService:
    """Service that generates PDF reports for audits."""

    def __init__(self, db):
        self.db = db
        self.audit_repo = AuditRepository(db)
        self.project_repo = ProjectRepository(db)
        self.report_repo = ReportRepository(db)

    async def generate_pdf(self, user_id: str, audit_id: uuid.UUID) -> BytesIO:
        """Generate a PDF report for the given audit. Raises NotFoundException if not found."""
        # Fetch audit
        audit = await self.audit_repo.get_by_id(audit_id)
        if not audit:
            raise NotFoundException("Audit", str(audit_id))

        # Verify ownership
        project = await self.project_repo.get_by_id(audit.project_id)
        if not project or str(project.user_id) != user_id:
            raise NotFoundException("Audit", str(audit_id))

        # Fetch report
        report = await self.report_repo.get_by_audit_id(audit_id)
        if not report:
            raise NotFoundException("Report", str(audit_id))

        # Fetch pages and violations
        pages = await self.audit_repo.get_pages(audit_id)
        violations = await self.audit_repo.get_violations(audit_id)

        builder = PdfReportBuilder(audit, project, report, pages, violations)
        return builder.build()