from bot.database.models import User


def format_preview(user: User) -> str:
    lines = []
    lines.append("=== معاينة بياناتك ===\n")

    lines.append(f"الاسم: {user.full_name or 'غير محدد'}")
    lines.append(f"المسمى الوظيفي: {user.job_title or 'غير محدد'}")
    lines.append(f"الهاتف: {user.phone or 'غير محدد'}")
    lines.append(f"البريد: {user.email or 'غير محدد'}")
    lines.append(f"المدينة / الدولة: {user.city_country or 'غير محدد'}")
    lines.append(f"لينكد إن: {user.linkedin or 'غير محدد'}")
    lines.append(f"الموقع / GitHub: {user.portfolio or 'غير محدد'}")
    lines.append(f"الملخص المهني: {user.summary or 'غير محدد'}")
    lines.append(f"المهارات: {user.skills or 'غير محدد'}")
    lines.append(f"اللغات: {user.languages or 'غير محدد'}")

    if user.experiences:
        lines.append("\n--- الخبرات العملية ---")
        for i, exp in enumerate(user.experiences, 1):
            end = exp.end_date or "حتى الآن"
            lines.append(f"{i}. {exp.title} في {exp.company} ({exp.start_date} - {end})")
            if exp.responsibilities:
                lines.append(f"   المهام: {exp.responsibilities}")

    if user.educations:
        lines.append("\n--- التعليم ---")
        for i, edu in enumerate(user.educations, 1):
            year = edu.graduation_year or ""
            lines.append(f"{i}. {edu.degree} - {edu.institution} {year}")

    if user.courses:
        lines.append("\n--- الدورات والشهادات ---")
        for i, c in enumerate(user.courses, 1):
            provider = f" - {c.provider}" if c.provider else ""
            year = f" ({c.year})" if c.year else ""
            lines.append(f"{i}. {c.name}{provider}{year}")

    if user.projects:
        lines.append("\n--- المشاريع ---")
        for i, p in enumerate(user.projects, 1):
            lines.append(f"{i}. {p.name}")
            if p.description:
                lines.append(f"   {p.description}")
            if p.link:
                lines.append(f"   الرابط: {p.link}")

    return "\n".join(lines)


def generate_summary(user: User) -> str:
    parts = []
    if user.job_title:
        parts.append(user.job_title)
    if user.skills:
        skill_list = [s.strip() for s in user.skills.split(",")][:5]
        parts.append("، ".join(skill_list))
    if user.experiences:
        years_count = len(user.experiences)
        parts.append(f"{years_count} خبرات عملية")

    if not parts:
        return "محترف متحمس يبحث عن فرص جديدة لتطوير مسيرته المهنية."

    return f"محترف في مجال {parts[0]} يمتلك مهارات في {', '.join(parts[1:])}، يبحث عن فرص جديدة لتطوير مسيرته المهنية والمساهمة في نجاح المؤسسة."
