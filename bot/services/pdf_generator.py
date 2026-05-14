import os
import re
import tempfile
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle,
)
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from bot.config import logger
from bot.database.models import User
from bot.utils.text_helpers import generate_summary

FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

# Color palette
PRIMARY = HexColor("#1a1a2e")
SECONDARY = HexColor("#16213e")
TEXT_DARK = HexColor("#2c2c2c")
TEXT_MEDIUM = HexColor("#555555")
TEXT_LIGHT = HexColor("#777777")
ACCENT = HexColor("#0f3460")
LINE_COLOR = HexColor("#d0d0d0")
BG_HEADER = HexColor("#f5f5f5")

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text))


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

    return {
        "name": ParagraphStyle(
            "Name",
            fontName=bold_font,
            fontSize=20,
            textColor=PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=2,
            leading=26,
        ),
        "job_title": ParagraphStyle(
            "JobTitle",
            fontName=font_name,
            fontSize=12,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceAfter=4,
            leading=16,
        ),
        "contact": ParagraphStyle(
            "Contact",
            fontName=font_name,
            fontSize=9,
            textColor=TEXT_MEDIUM,
            alignment=TA_CENTER,
            spaceAfter=2,
            leading=13,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            fontName=bold_font,
            fontSize=13,
            textColor=PRIMARY,
            alignment=TA_RIGHT,
            spaceBefore=0,
            spaceAfter=6,
            leading=18,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=font_name,
            fontSize=10,
            textColor=TEXT_DARK,
            alignment=TA_RIGHT,
            spaceAfter=4,
            leading=16,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold",
            fontName=bold_font,
            fontSize=10,
            textColor=TEXT_DARK,
            alignment=TA_RIGHT,
            spaceAfter=2,
            leading=16,
        ),
        "body_light": ParagraphStyle(
            "BodyLight",
            fontName=font_name,
            fontSize=9,
            textColor=TEXT_LIGHT,
            alignment=TA_RIGHT,
            spaceAfter=2,
            leading=13,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName=font_name,
            fontSize=10,
            textColor=TEXT_DARK,
            alignment=TA_RIGHT,
            spaceAfter=2,
            leading=15,
            leftIndent=15,
            rightIndent=15,
        ),
    }


def _reshape_arabic(text: str) -> str:
    if not _has_arabic(text):
        return text
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


def _add_section_header(elements: list, title: str, styles: dict) -> None:
    elements.append(Spacer(1, 8 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT, spaceAfter=3))
    elements.append(Paragraph(_reshape_arabic(title), styles["section_title"]))
    elements.append(Spacer(1, 2 * mm))


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
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
        )

        elements: list = []

        # ── Header Section ──
        if user.full_name:
            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(_escape(user.full_name), styles["name"]))

        if user.job_title:
            elements.append(Paragraph(_escape(user.job_title), styles["job_title"]))

        elements.append(Spacer(1, 3 * mm))

        # Contact info (centered, single line with separators)
        contact_parts = []
        if user.phone:
            contact_parts.append(user.phone)
        if user.email:
            contact_parts.append(user.email)
        if user.city_country:
            contact_parts.append(_escape(user.city_country))
        if contact_parts:
            elements.append(Paragraph("  |  ".join(contact_parts), styles["contact"]))

        links = []
        if user.linkedin:
            links.append(user.linkedin)
        if user.portfolio:
            links.append(user.portfolio)
        if links:
            elements.append(Paragraph("  |  ".join(links), styles["contact"]))

        elements.append(Spacer(1, 4 * mm))
        elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=2))

        # ── Professional Summary ──
        summary = user.summary or generate_summary(user)
        if summary:
            _add_section_header(elements, "الملخص المهني", styles)
            elements.append(Paragraph(_escape(summary), styles["body"]))

        # ── Work Experience ──
        if user.experiences:
            _add_section_header(elements, "الخبرات العملية", styles)
            for i, exp in enumerate(user.experiences):
                end = exp.end_date or "حتى الآن"
                elements.append(
                    Paragraph(
                        _escape(f"{exp.title}  —  {exp.company}"),
                        styles["body_bold"],
                    )
                )
                elements.append(
                    Paragraph(
                        _escape(f"{exp.start_date}  —  {end}"),
                        styles["body_light"],
                    )
                )
                if exp.responsibilities:
                    elements.append(Spacer(1, 1.5 * mm))
                    for line in exp.responsibilities.split("\n"):
                        line = line.strip()
                        if line:
                            elements.append(
                                Paragraph(
                                    _escape(f"\u2022  {line}"),
                                    styles["bullet"],
                                )
                            )
                if i < len(user.experiences) - 1:
                    elements.append(Spacer(1, 5 * mm))

        # ── Education ──
        if user.educations:
            _add_section_header(elements, "التعليم", styles)
            for i, edu in enumerate(user.educations):
                elements.append(
                    Paragraph(
                        _escape(f"{edu.degree}  —  {edu.institution}"),
                        styles["body_bold"],
                    )
                )
                if edu.graduation_year:
                    elements.append(
                        Paragraph(
                            _escape(edu.graduation_year),
                            styles["body_light"],
                        )
                    )
                if i < len(user.educations) - 1:
                    elements.append(Spacer(1, 3 * mm))

        # ── Skills ──
        if user.skills:
            _add_section_header(elements, "المهارات", styles)
            elements.append(Paragraph(_escape(user.skills), styles["body"]))

        # ── Languages ──
        if user.languages:
            _add_section_header(elements, "اللغات", styles)
            elements.append(Paragraph(_escape(user.languages), styles["body"]))

        # ── Courses & Certifications ──
        if user.courses:
            _add_section_header(elements, "الدورات والشهادات", styles)
            for i, c in enumerate(user.courses):
                parts = [c.name]
                if c.provider:
                    parts.append(c.provider)
                elements.append(
                    Paragraph(
                        _escape("  —  ".join(parts)),
                        styles["body_bold"],
                    )
                )
                if c.year:
                    elements.append(
                        Paragraph(_escape(c.year), styles["body_light"])
                    )
                if i < len(user.courses) - 1:
                    elements.append(Spacer(1, 2 * mm))

        # ── Projects ──
        if user.projects:
            _add_section_header(elements, "المشاريع", styles)
            for i, p in enumerate(user.projects):
                elements.append(Paragraph(_escape(p.name), styles["body_bold"]))
                if p.description:
                    elements.append(Paragraph(_escape(p.description), styles["body"]))
                if p.link:
                    elements.append(Paragraph(p.link, styles["body_light"]))
                if i < len(user.projects) - 1:
                    elements.append(Spacer(1, 3 * mm))

        doc.build(elements)
        logger.info("PDF generated: %s", filepath)
        return filepath

    except Exception:
        logger.exception("Failed to generate PDF")
        return None
