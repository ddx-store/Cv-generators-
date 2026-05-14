import os
import tempfile
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from bot.config import logger
from bot.database.models import User
from bot.utils.text_helpers import generate_summary

FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

HEADER_COLOR = HexColor("#1a1a2e")
SECTION_COLOR = HexColor("#16213e")
TEXT_COLOR = HexColor("#333333")
ACCENT_COLOR = HexColor("#0f3460")
LINE_COLOR = HexColor("#cccccc")


def _register_fonts() -> str:
    font_name = "Arabic"
    if font_name in pdfmetrics.getRegisteredFontNames():
        return font_name

    arabic_font_path = FONTS_DIR / "Amiri-Regular.ttf"
    arabic_bold_path = FONTS_DIR / "Amiri-Bold.ttf"

    if arabic_font_path.exists():
        pdfmetrics.registerFont(TTFont("Arabic", str(arabic_font_path)))
        if arabic_bold_path.exists():
            pdfmetrics.registerFont(TTFont("ArabicBold", str(arabic_bold_path)))
        else:
            pdfmetrics.registerFont(TTFont("ArabicBold", str(arabic_font_path)))
        return "Arabic"

    logger.warning("Arabic font not found at %s, falling back to Helvetica", arabic_font_path)
    return "Helvetica"


def _get_styles(font_name: str) -> dict:
    bold_font = "ArabicBold" if font_name == "Arabic" else "Helvetica-Bold"
    alignment = TA_RIGHT if font_name == "Arabic" else TA_LEFT

    return {
        "name": ParagraphStyle(
            "Name",
            fontName=bold_font,
            fontSize=18,
            textColor=HEADER_COLOR,
            alignment=alignment,
            spaceAfter=4,
            wordWrap="RTL" if font_name == "Arabic" else "LTR",
        ),
        "job_title": ParagraphStyle(
            "JobTitle",
            fontName=font_name,
            fontSize=13,
            textColor=ACCENT_COLOR,
            alignment=alignment,
            spaceAfter=6,
            wordWrap="RTL" if font_name == "Arabic" else "LTR",
        ),
        "contact": ParagraphStyle(
            "Contact",
            fontName=font_name,
            fontSize=9,
            textColor=TEXT_COLOR,
            alignment=alignment,
            spaceAfter=2,
            wordWrap="RTL" if font_name == "Arabic" else "LTR",
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            fontName=bold_font,
            fontSize=13,
            textColor=SECTION_COLOR,
            alignment=alignment,
            spaceBefore=10,
            spaceAfter=4,
            wordWrap="RTL" if font_name == "Arabic" else "LTR",
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=font_name,
            fontSize=10,
            textColor=TEXT_COLOR,
            alignment=alignment,
            spaceAfter=3,
            leading=14,
            wordWrap="RTL" if font_name == "Arabic" else "LTR",
        ),
        "body_bold": ParagraphStyle(
            "BodyBold",
            fontName=bold_font,
            fontSize=10,
            textColor=TEXT_COLOR,
            alignment=alignment,
            spaceAfter=2,
            leading=14,
            wordWrap="RTL" if font_name == "Arabic" else "LTR",
        ),
    }


def _add_section_header(elements: list, title: str, styles: dict) -> None:
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=LINE_COLOR))
    elements.append(Spacer(1, 0.15 * cm))
    elements.append(Paragraph(_reshape_arabic(title), styles["section_title"]))


def _reshape_arabic(text: str) -> str:
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _escape(text: str | None) -> str:
    if not text:
        return ""
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return _reshape_arabic(escaped)


async def generate_cv_pdf(user: User) -> str | None:
    try:
        font_name = _register_fonts()
        styles = _get_styles(font_name)

        safe_name = "".join(c for c in (user.full_name or "cv") if c.isalnum() or c in " _-")
        safe_name = safe_name.strip().replace(" ", "_") or "cv"
        filename = f"CV_{safe_name}.pdf"

        tmp_dir = tempfile.mkdtemp()
        filepath = os.path.join(tmp_dir, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements: list = []

        # Header
        if user.full_name:
            elements.append(Paragraph(_escape(user.full_name), styles["name"]))
        if user.job_title:
            elements.append(Paragraph(_escape(user.job_title), styles["job_title"]))

        # Contact info
        contact_parts = []
        if user.phone:
            contact_parts.append(user.phone)
        if user.email:
            contact_parts.append(user.email)
        if user.city_country:
            contact_parts.append(user.city_country)
        if contact_parts:
            elements.append(Paragraph(_escape(" | ".join(contact_parts)), styles["contact"]))

        links = []
        if user.linkedin:
            links.append(user.linkedin)
        if user.portfolio:
            links.append(user.portfolio)
        if links:
            elements.append(Paragraph(_escape(" | ".join(links)), styles["contact"]))

        # Professional Summary
        summary = user.summary or generate_summary(user)
        if summary:
            _add_section_header(elements, "الملخص المهني", styles)
            elements.append(Paragraph(_escape(summary), styles["body"]))

        # Work Experience
        if user.experiences:
            _add_section_header(elements, "الخبرات العملية", styles)
            for exp in user.experiences:
                end = exp.end_date or "حتى الآن"
                elements.append(
                    Paragraph(
                        _escape(f"{exp.title} - {exp.company}"),
                        styles["body_bold"],
                    )
                )
                elements.append(
                    Paragraph(
                        _escape(f"{exp.start_date} - {end}"),
                        styles["body"],
                    )
                )
                if exp.responsibilities:
                    for line in exp.responsibilities.split("\n"):
                        line = line.strip()
                        if line:
                            elements.append(Paragraph(_escape(f"- {line}"), styles["body"]))
                elements.append(Spacer(1, 0.15 * cm))

        # Education
        if user.educations:
            _add_section_header(elements, "التعليم", styles)
            for edu in user.educations:
                year = f" ({edu.graduation_year})" if edu.graduation_year else ""
                elements.append(
                    Paragraph(
                        _escape(f"{edu.degree} - {edu.institution}{year}"),
                        styles["body"],
                    )
                )

        # Skills
        if user.skills:
            _add_section_header(elements, "المهارات", styles)
            elements.append(Paragraph(_escape(user.skills), styles["body"]))

        # Languages
        if user.languages:
            _add_section_header(elements, "اللغات", styles)
            elements.append(Paragraph(_escape(user.languages), styles["body"]))

        # Courses
        if user.courses:
            _add_section_header(elements, "الدورات والشهادات", styles)
            for c in user.courses:
                provider = f" - {c.provider}" if c.provider else ""
                year = f" ({c.year})" if c.year else ""
                elements.append(
                    Paragraph(_escape(f"{c.name}{provider}{year}"), styles["body"])
                )

        # Projects
        if user.projects:
            _add_section_header(elements, "المشاريع", styles)
            for p in user.projects:
                elements.append(Paragraph(_escape(p.name), styles["body_bold"]))
                if p.description:
                    elements.append(Paragraph(_escape(p.description), styles["body"]))
                if p.link:
                    elements.append(Paragraph(_escape(p.link), styles["body"]))
                elements.append(Spacer(1, 0.1 * cm))

        doc.build(elements)
        logger.info("PDF generated: %s", filepath)
        return filepath

    except Exception:
        logger.exception("Failed to generate PDF")
        return None
