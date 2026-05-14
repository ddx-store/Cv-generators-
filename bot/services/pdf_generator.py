import os
import re
import tempfile
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
)
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from bot.config import logger
from bot.database.models import User
from bot.utils.text_helpers import generate_summary

FONTS_DIR = Path(__file__).parent.parent.parent / "fonts"

SECTION_HEADERS = {
    "ar": {
        "summary": "الملخص المهني",
        "skills": "المهارات الأساسية",
        "experience": "الخبرات العملية",
        "education": "التعليم",
        "courses": "الشهادات والدورات",
        "languages": "اللغات",
        "projects": "المشاريع",
        "present": "حتى الآن",
    },
    "en": {
        "summary": "Professional Summary",
        "skills": "Core Skills",
        "experience": "Professional Experience",
        "education": "Education",
        "courses": "Awards & Certifications",
        "languages": "Languages",
        "projects": "Projects",
        "present": "Present",
    },
}

BLUE = HexColor("#1a5276")
BLACK = HexColor("#1a1a1a")
GRAY = HexColor("#444444")
LIGHT_GRAY = HexColor("#666666")
LINE_BLUE = HexColor("#2980b9")

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


def _get_styles(font_name: str, lang: str = "ar") -> dict:
    bold_font = "ArabicBold" if font_name == "Arabic" else "Helvetica-Bold"
    body_align = TA_RIGHT if lang == "ar" else TA_LEFT

    return {
        "name": ParagraphStyle(
            "Name",
            fontName=bold_font,
            fontSize=22,
            textColor=BLUE,
            alignment=body_align,
            spaceAfter=2,
            leading=28,
        ),
        "contact": ParagraphStyle(
            "Contact",
            fontName=font_name,
            fontSize=9,
            textColor=GRAY,
            alignment=body_align,
            spaceAfter=2,
            leading=13,
        ),
        "section_title": ParagraphStyle(
            "SectionTitle",
            fontName=bold_font,
            fontSize=12,
            textColor=BLUE,
            alignment=body_align,
            spaceBefore=0,
            spaceAfter=4,
            leading=16,
        ),
        "body": ParagraphStyle(
            "Body",
            fontName=font_name,
            fontSize=10,
            textColor=BLACK,
            alignment=body_align,
            spaceAfter=3,
            leading=15,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold",
            fontName=bold_font,
            fontSize=10,
            textColor=BLACK,
            alignment=body_align,
            spaceAfter=1,
            leading=15,
        ),
        "body_light": ParagraphStyle(
            "BodyLight",
            fontName=bold_font,
            fontSize=9,
            textColor=GRAY,
            alignment=body_align,
            spaceAfter=2,
            leading=13,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            fontName=font_name,
            fontSize=10,
            textColor=BLACK,
            alignment=body_align,
            spaceAfter=2,
            leading=14,
            leftIndent=12 if lang != "ar" else 0,
            rightIndent=12 if lang == "ar" else 0,
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
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(_reshape_arabic(title), styles["section_title"]))
    elements.append(Spacer(1, 1 * mm))


async def generate_cv_pdf(user: User) -> str | None:
    try:
        font_name = _register_fonts()
        lang = getattr(user, "cv_language", "ar") or "ar"
        headers = SECTION_HEADERS.get(lang, SECTION_HEADERS["ar"])
        styles = _get_styles(font_name, lang)

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
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements: list = []

        # ── Name ──
        if user.full_name:
            elements.append(Paragraph(_escape(user.full_name), styles["name"]))

        # ── Blue line under name ──
        elements.append(Spacer(1, 2 * mm))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=LINE_BLUE, spaceAfter=4))

        # ── Contact info on one line ──
        contact_parts = []
        if user.phone:
            contact_parts.append(user.phone)
        if user.email:
            contact_parts.append(user.email)
        if user.city_country:
            contact_parts.append(_escape(user.city_country))
        if user.linkedin:
            link_text = user.linkedin.replace("https://", "").replace("http://", "")
            contact_parts.append(
                f'<a href="{user.linkedin}" color="#2980b9">{link_text}</a>'
            )
        if user.portfolio:
            link_text = user.portfolio.replace("https://", "").replace("http://", "")
            contact_parts.append(
                f'<a href="{user.portfolio}" color="#2980b9">{link_text}</a>'
            )
        if contact_parts:
            elements.append(Paragraph(" | ".join(contact_parts), styles["contact"]))

        # ── Professional Summary ──
        summary = user.summary or generate_summary(user)
        if summary:
            _add_section_header(elements, headers["summary"], styles)
            elements.append(Paragraph(_escape(summary), styles["body"]))

        # ── Core Skills ──
        if user.skills:
            _add_section_header(elements, headers["skills"], styles)
            skills_list = [s.strip() for s in user.skills.split(",") if s.strip()]
            for skill in skills_list:
                elements.append(
                    Paragraph(_escape(f"\u2022 {skill}"), styles["bullet"])
                )

        # ── Professional Experience ──
        if user.experiences:
            _add_section_header(elements, headers["experience"], styles)
            for i, exp in enumerate(user.experiences):
                end = exp.end_date or headers["present"]
                # Job title bold
                elements.append(
                    Paragraph(
                        _escape(exp.title),
                        styles["body_bold"],
                    )
                )
                # Company — Location on same line
                elements.append(
                    Paragraph(
                        _escape(f"{exp.company}"),
                        styles["body"],
                    )
                )
                # Dates bold
                elements.append(
                    Paragraph(
                        _escape(f"{exp.start_date} \u2013 {end}"),
                        styles["body_light"],
                    )
                )
                if exp.responsibilities:
                    elements.append(Spacer(1, 1 * mm))
                    for line in exp.responsibilities.split("\n"):
                        line = line.strip()
                        if line:
                            elements.append(
                                Paragraph(
                                    _escape(f"\u2022 {line}"),
                                    styles["bullet"],
                                )
                            )
                if i < len(user.experiences) - 1:
                    elements.append(Spacer(1, 4 * mm))

        # ── Education ──
        if user.educations:
            _add_section_header(elements, headers["education"], styles)
            for i, edu in enumerate(user.educations):
                parts = [edu.degree]
                if edu.institution:
                    parts.append(edu.institution)
                if edu.graduation_year:
                    parts.append(edu.graduation_year)
                elements.append(
                    Paragraph(
                        _escape(", ".join(parts)),
                        styles["body"],
                    )
                )
                if i < len(user.educations) - 1:
                    elements.append(Spacer(1, 2 * mm))

        # ── Courses & Certifications ──
        if user.courses:
            _add_section_header(elements, headers["courses"], styles)
            for c in user.courses:
                parts = [c.name]
                if c.provider:
                    parts.append(c.provider)
                if c.year:
                    parts.append(f"({c.year})")
                elements.append(
                    Paragraph(
                        _escape(f"\u2022 {' \u2013 '.join(parts)}"),
                        styles["bullet"],
                    )
                )

        # ── Languages ──
        if user.languages:
            _add_section_header(elements, headers["languages"], styles)
            lang_list = [l.strip() for l in user.languages.split(",") if l.strip()]
            for lang_item in lang_list:
                elements.append(
                    Paragraph(_escape(f"\u2022 {lang_item}"), styles["bullet"])
                )

        # ── Projects ──
        if user.projects:
            _add_section_header(elements, headers["projects"], styles)
            for i, p in enumerate(user.projects):
                elements.append(Paragraph(_escape(p.name), styles["body_bold"]))
                if p.description:
                    elements.append(Paragraph(_escape(p.description), styles["body"]))
                if p.link:
                    elements.append(
                        Paragraph(
                            f'<a href="{p.link}" color="#2980b9">{p.link}</a>',
                            styles["body"],
                        )
                    )
                if i < len(user.projects) - 1:
                    elements.append(Spacer(1, 3 * mm))

        doc.build(elements)
        logger.info("PDF generated: %s", filepath)
        return filepath

    except Exception:
        logger.exception("Failed to generate PDF")
        return None
