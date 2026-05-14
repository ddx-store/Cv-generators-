from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.cv_states import CVForm
from bot.keyboards.reply_kb import skip_kb, add_more_kb, main_menu_kb, cv_language_kb
from bot.database.engine import get_session
from bot.database.crud import (
    update_user_field,
    add_experience,
    add_education,
    add_course,
    add_project,
    delete_user_experiences,
    delete_user_educations,
    delete_user_courses,
    delete_user_projects,
)
from bot.utils.validators import validate_email, validate_phone
from bot.config import logger

router = Router()

SKIP = "تخطي"
CANCEL = "إلغاء"

TOTAL_STEPS = 10  # language, name, title, phone, email, city, linkedin, portfolio, summary, skills/languages


def _is_skip(message: Message) -> bool:
    return message.text and message.text.strip() == SKIP


def _is_cancel(message: Message) -> bool:
    return message.text and message.text.strip() == CANCEL


def _progress(step: int, total: int = TOTAL_STEPS) -> str:
    filled = round(step / total * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"[{bar}] {step}/{total}"


async def _do_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("تم الإلغاء والعودة للقائمة الرئيسية.", reply_markup=main_menu_kb())


# ── Job field templates ────────────────────────────────────────

JOB_TEMPLATES = {
    "software engineer": {
        "skills": "Python, JavaScript, SQL, Git, REST APIs, Docker, AWS, Agile",
        "summary_en": "Results-driven software engineer with experience in designing, developing, and deploying scalable applications.",
        "summary_ar": "مهندس برمجيات متميز ذو خبرة في تصميم وتطوير ونشر التطبيقات القابلة للتوسع.",
    },
    "مهندس برمجيات": {
        "skills": "Python, JavaScript, SQL, Git, REST APIs, Docker, AWS, Agile",
        "summary_en": "Results-driven software engineer with experience in designing, developing, and deploying scalable applications.",
        "summary_ar": "مهندس برمجيات متميز ذو خبرة في تصميم وتطوير ونشر التطبيقات القابلة للتوسع.",
    },
    "data analyst": {
        "skills": "Python, SQL, Excel, Power BI, Tableau, Data Visualization, Statistics",
        "summary_en": "Detail-oriented data analyst skilled in transforming complex data into actionable business insights.",
        "summary_ar": "محلل بيانات دقيق ماهر في تحويل البيانات المعقدة إلى رؤى أعمال قابلة للتنفيذ.",
    },
    "محلل بيانات": {
        "skills": "Python, SQL, Excel, Power BI, Tableau, Data Visualization, Statistics",
        "summary_en": "Detail-oriented data analyst skilled in transforming complex data into actionable business insights.",
        "summary_ar": "محلل بيانات دقيق ماهر في تحويل البيانات المعقدة إلى رؤى أعمال قابلة للتنفيذ.",
    },
    "graphic designer": {
        "skills": "Adobe Photoshop, Illustrator, InDesign, Figma, UI/UX, Branding, Typography",
        "summary_en": "Creative graphic designer with a strong portfolio in branding, digital design, and visual communication.",
        "summary_ar": "مصمم جرافيك مبدع يمتلك محفظة قوية في الهوية البصرية والتصميم الرقمي.",
    },
    "مصمم جرافيك": {
        "skills": "Adobe Photoshop, Illustrator, InDesign, Figma, UI/UX, Branding, Typography",
        "summary_en": "Creative graphic designer with a strong portfolio in branding, digital design, and visual communication.",
        "summary_ar": "مصمم جرافيك مبدع يمتلك محفظة قوية في الهوية البصرية والتصميم الرقمي.",
    },
    "marketing": {
        "skills": "Digital Marketing, SEO, SEM, Google Ads, Social Media, Content Marketing, Analytics",
        "summary_en": "Strategic marketing professional experienced in digital campaigns, brand growth, and data-driven strategies.",
        "summary_ar": "محترف تسويق استراتيجي ذو خبرة في الحملات الرقمية ونمو العلامات التجارية.",
    },
    "تسويق": {
        "skills": "Digital Marketing, SEO, SEM, Google Ads, Social Media, Content Marketing, Analytics",
        "summary_en": "Strategic marketing professional experienced in digital campaigns, brand growth, and data-driven strategies.",
        "summary_ar": "محترف تسويق استراتيجي ذو خبرة في الحملات الرقمية ونمو العلامات التجارية.",
    },
    "accountant": {
        "skills": "Financial Reporting, Excel, QuickBooks, SAP, Auditing, Tax, Budgeting, IFRS",
        "summary_en": "Detail-oriented accountant with expertise in financial reporting, auditing, and compliance.",
        "summary_ar": "محاسب دقيق ذو خبرة في التقارير المالية والمراجعة والامتثال.",
    },
    "محاسب": {
        "skills": "Financial Reporting, Excel, QuickBooks, SAP, Auditing, Tax, Budgeting, IFRS",
        "summary_en": "Detail-oriented accountant with expertise in financial reporting, auditing, and compliance.",
        "summary_ar": "محاسب دقيق ذو خبرة في التقارير المالية والمراجعة والامتثال.",
    },
    "project manager": {
        "skills": "Project Planning, Agile, Scrum, Jira, Risk Management, Stakeholder Management, Budgeting",
        "summary_en": "Experienced project manager skilled in leading cross-functional teams and delivering projects on time and within budget.",
        "summary_ar": "مدير مشاريع ذو خبرة في قيادة الفرق متعددة التخصصات وتسليم المشاريع في الوقت المحدد.",
    },
    "مدير مشاريع": {
        "skills": "Project Planning, Agile, Scrum, Jira, Risk Management, Stakeholder Management, Budgeting",
        "summary_en": "Experienced project manager skilled in leading cross-functional teams and delivering projects on time and within budget.",
        "summary_ar": "مدير مشاريع ذو خبرة في قيادة الفرق متعددة التخصصات وتسليم المشاريع في الوقت المحدد.",
    },
    "human resources": {
        "skills": "Recruitment, Onboarding, Employee Relations, HRIS, Performance Management, Labor Law",
        "summary_en": "HR professional with experience in talent acquisition, employee engagement, and organizational development.",
        "summary_ar": "محترف موارد بشرية ذو خبرة في استقطاب المواهب وتطوير بيئة العمل.",
    },
    "موارد بشرية": {
        "skills": "Recruitment, Onboarding, Employee Relations, HRIS, Performance Management, Labor Law",
        "summary_en": "HR professional with experience in talent acquisition, employee engagement, and organizational development.",
        "summary_ar": "محترف موارد بشرية ذو خبرة في استقطاب المواهب وتطوير بيئة العمل.",
    },
    "teacher": {
        "skills": "Curriculum Design, Classroom Management, Assessment, Communication, EdTech, Mentoring",
        "summary_en": "Dedicated educator with experience in curriculum development, student engagement, and educational technology.",
        "summary_ar": "معلم متفانٍ ذو خبرة في تطوير المناهج والتقنيات التعليمية.",
    },
    "معلم": {
        "skills": "Curriculum Design, Classroom Management, Assessment, Communication, EdTech, Mentoring",
        "summary_en": "Dedicated educator with experience in curriculum development, student engagement, and educational technology.",
        "summary_ar": "معلم متفانٍ ذو خبرة في تطوير المناهج والتقنيات التعليمية.",
    },
    "sales": {
        "skills": "CRM, Negotiation, B2B Sales, Lead Generation, Customer Relations, Salesforce, Presentations",
        "summary_en": "Results-oriented sales professional with a proven track record in revenue growth and client relationship management.",
        "summary_ar": "محترف مبيعات يركز على النتائج مع سجل حافل في نمو الإيرادات وإدارة العملاء.",
    },
    "مبيعات": {
        "skills": "CRM, Negotiation, B2B Sales, Lead Generation, Customer Relations, Salesforce, Presentations",
        "summary_en": "Results-oriented sales professional with a proven track record in revenue growth and client relationship management.",
        "summary_ar": "محترف مبيعات يركز على النتائج مع سجل حافل في نمو الإيرادات وإدارة العملاء.",
    },
}


def _find_template(job_title: str) -> dict | None:
    title_lower = job_title.lower().strip()
    for key, template in JOB_TEMPLATES.items():
        if key in title_lower or title_lower in key:
            return template
    return None


# ── Start CV creation ──────────────────────────────────────────

@router.message(F.text == "إنشاء سيرة ذاتية")
async def start_cv(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CVForm.cv_language)
    await message.answer(
        "اختر لغة السيرة الذاتية:\nChoose CV language:",
        reply_markup=cv_language_kb(),
    )


@router.message(CVForm.cv_language)
async def process_cv_language(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    text = message.text.strip()
    if "English" in text:
        lang = "en"
    elif "العربية" in text:
        lang = "ar"
    else:
        await message.answer(
            "اختر لغة السيرة الذاتية:\nChoose CV language:",
            reply_markup=cv_language_kb(),
        )
        return
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "cv_language", lang)
    await state.update_data(cv_language=lang)
    await state.set_state(CVForm.full_name)
    p = _progress(1)
    await message.answer(
        f"{p}\n\nما هو اسمك الكامل؟\n(يمكنك الضغط على 'تخطي' لأي خطوة أو 'إلغاء' للعودة)"
        if lang == "ar" else
        f"{p}\n\nWhat is your full name?\n(Press 'تخطي' to skip or 'إلغاء' to cancel)",
        reply_markup=skip_kb(),
    )


# ── Basic fields ───────────────────────────────────────────────

@router.message(CVForm.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "full_name", message.text.strip())
    await state.set_state(CVForm.job_title)
    await message.answer(
        f"{_progress(2)}\n\nما هو المسمى الوظيفي أو الوظيفة المطلوبة؟",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.job_title)
async def process_job_title(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    template_msg = ""
    if not _is_skip(message):
        job_title = message.text.strip()
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "job_title", job_title)
        template = _find_template(job_title)
        if template:
            await state.update_data(job_template=template)
            template_msg = (
                f"\n\n💡 تم العثور على قالب لمجال \"{job_title}\"!\n"
                "سيتم اقتراح مهارات وملخص مهني لاحقاً."
            )
    await state.set_state(CVForm.phone)
    await message.answer(
        f"{_progress(3)}\n\nما هو رقم هاتفك؟ (مثال: +966501234567){template_msg}",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        pass
    else:
        phone = message.text.strip()
        if not validate_phone(phone):
            await message.answer(
                "رقم الهاتف غير صحيح. يرجى إدخال رقم صحيح (مثال: +966501234567)\n"
                "أو اضغط 'تخطي'",
                reply_markup=skip_kb(),
            )
            return
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "phone", phone)
    await state.set_state(CVForm.email)
    await message.answer(
        f"{_progress(4)}\n\nما هو بريدك الإلكتروني؟",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.email)
async def process_email(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        pass
    else:
        email = message.text.strip()
        if not validate_email(email):
            await message.answer(
                "البريد الإلكتروني غير صحيح. يرجى إدخال بريد صحيح (مثال: name@email.com)\n"
                "أو اضغط 'تخطي'",
                reply_markup=skip_kb(),
            )
            return
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "email", email)
    await state.set_state(CVForm.city_country)
    await message.answer(
        f"{_progress(5)}\n\nما هي مدينتك / دولتك؟ (مثال: الرياض، السعودية)",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.city_country)
async def process_city(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "city_country", message.text.strip())
    await state.set_state(CVForm.linkedin)
    await message.answer(
        f"{_progress(6)}\n\nما هو رابط حسابك على لينكد إن؟",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.linkedin)
async def process_linkedin(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "linkedin", message.text.strip())
    await state.set_state(CVForm.portfolio)
    await message.answer(
        f"{_progress(7)}\n\nما هو رابط موقعك الشخصي أو GitHub؟",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.portfolio)
async def process_portfolio(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "portfolio", message.text.strip())
    await state.set_state(CVForm.summary)

    data = await state.get_data()
    template = data.get("job_template")
    lang = data.get("cv_language", "ar")
    hint = ""
    if template:
        suggested = template.get("summary_ar" if lang == "ar" else "summary_en", "")
        if suggested:
            hint = f"\n\n💡 ملخص مقترح:\n\"{suggested}\"\n\nيمكنك نسخه أو كتابة ملخصك الخاص."

    await message.answer(
        f"{_progress(8)}\n\nاكتب ملخصك المهني (2-3 جمل عن نفسك وخبراتك).\n"
        f"إذا تخطيت، سيتم إنشاء ملخص تلقائي بناءً على بياناتك.{hint}",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.summary)
async def process_summary(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "summary", message.text.strip())
    await state.set_state(CVForm.exp_company)
    async with await get_session() as session:
        await delete_user_experiences(session, message.from_user.id)
    await message.answer(
        f"{_progress(9)}\n\nالآن سنضيف خبراتك العملية.\n\n"
        "ما هو اسم الشركة؟\n"
        "(اضغط 'تخطي' لتجاوز الخبرات العملية)",
        reply_markup=skip_kb(),
    )


# ── Experience ─────────────────────────────────────────────────

@router.message(CVForm.exp_company)
async def process_exp_company(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        await _go_to_education(message, state)
        return
    await state.update_data(exp_company=message.text.strip())
    await state.set_state(CVForm.exp_title)
    await message.answer("ما هو مسماك الوظيفي في هذه الشركة؟", reply_markup=skip_kb())


@router.message(CVForm.exp_title)
async def process_exp_title(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    title = "" if _is_skip(message) else message.text.strip()
    await state.update_data(exp_title=title)
    await state.set_state(CVForm.exp_start)
    await message.answer("متى بدأت العمل؟ (مثال: يناير 2020)", reply_markup=skip_kb())


@router.message(CVForm.exp_start)
async def process_exp_start(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    start = "" if _is_skip(message) else message.text.strip()
    await state.update_data(exp_start=start)
    await state.set_state(CVForm.exp_end)
    await message.answer(
        "متى انتهيت من العمل؟ (مثال: ديسمبر 2023)\n"
        "إذا كنت لا تزال تعمل هنا، اكتب 'حتى الآن'",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.exp_end)
async def process_exp_end(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        end_date = None
    else:
        text = message.text.strip()
        end_date = None if text == "حتى الآن" else text
    await state.update_data(exp_end=end_date)
    await state.set_state(CVForm.exp_responsibilities)
    await message.answer("اكتب أهم المهام والإنجازات (كل مهمة في سطر جديد):", reply_markup=skip_kb())


@router.message(CVForm.exp_responsibilities)
async def process_exp_responsibilities(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    resp = None if _is_skip(message) else message.text.strip()
    await state.update_data(exp_responsibilities=resp)

    data = await state.get_data()
    company = data.get("exp_company", "")
    title = data.get("exp_title", "")
    if company or title:
        async with await get_session() as session:
            await add_experience(session, message.from_user.id, {
                "company": company or title,
                "title": title or company,
                "start_date": data.get("exp_start", ""),
                "end_date": data.get("exp_end"),
                "responsibilities": resp,
            })

    await state.set_state(CVForm.exp_add_more)
    await message.answer(
        "تم إضافة الخبرة بنجاح!\nهل تريد إضافة خبرة عمل أخرى؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.exp_add_more, F.text == "إلغاء")
async def cancel_at_exp_more(message: Message, state: FSMContext) -> None:
    await _do_cancel(message, state)


@router.message(CVForm.exp_add_more, F.text == "إضافة المزيد")
async def add_more_exp(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.exp_company)
    await message.answer("ما هو اسم الشركة التالية؟", reply_markup=skip_kb())


@router.message(CVForm.exp_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_exp(message: Message, state: FSMContext) -> None:
    await _go_to_education(message, state)


async def _go_to_education(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.edu_degree)
    async with await get_session() as session:
        await delete_user_educations(session, message.from_user.id)
    await message.answer(
        "الآن سنضيف التعليم.\n\n"
        "ما هي الدرجة العلمية؟ (مثال: بكالوريوس هندسة حاسب)\n"
        "(اضغط 'تخطي' لتجاوز التعليم)",
        reply_markup=skip_kb(),
    )


# ── Education ──────────────────────────────────────────────────

@router.message(CVForm.edu_degree)
async def process_edu_degree(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        await _go_to_skills(message, state)
        return
    await state.update_data(edu_degree=message.text.strip())
    await state.set_state(CVForm.edu_institution)
    await message.answer("ما هو اسم الجامعة أو المؤسسة التعليمية؟", reply_markup=skip_kb())


@router.message(CVForm.edu_institution)
async def process_edu_institution(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    inst = "" if _is_skip(message) else message.text.strip()
    await state.update_data(edu_institution=inst)
    await state.set_state(CVForm.edu_year)
    await message.answer("ما هي سنة التخرج؟ (مثال: 2022)", reply_markup=skip_kb())


@router.message(CVForm.edu_year)
async def process_edu_year(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    year = None if _is_skip(message) else message.text.strip()
    await state.update_data(edu_year=year)

    data = await state.get_data()
    degree = data.get("edu_degree", "")
    if degree:
        async with await get_session() as session:
            await add_education(session, message.from_user.id, {
                "degree": degree,
                "institution": data.get("edu_institution", ""),
                "graduation_year": data.get("edu_year"),
            })

    await state.set_state(CVForm.edu_add_more)
    await message.answer(
        "تم إضافة التعليم بنجاح!\nهل تريد إضافة شهادة تعليمية أخرى؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.edu_add_more, F.text == "إلغاء")
async def cancel_at_edu_more(message: Message, state: FSMContext) -> None:
    await _do_cancel(message, state)


@router.message(CVForm.edu_add_more, F.text == "إضافة المزيد")
async def add_more_edu(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.edu_degree)
    await message.answer("ما هي الدرجة العلمية التالية؟", reply_markup=skip_kb())


@router.message(CVForm.edu_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_edu(message: Message, state: FSMContext) -> None:
    await _go_to_skills(message, state)


async def _go_to_skills(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    template = data.get("job_template")
    hint = ""
    if template:
        suggested_skills = template.get("skills", "")
        if suggested_skills:
            hint = f"\n\n💡 مهارات مقترحة:\n\"{suggested_skills}\"\n\nيمكنك نسخها أو كتابة مهاراتك الخاصة."

    await state.set_state(CVForm.skills)
    await message.answer(
        f"{_progress(10)}\n\nاكتب مهاراتك مفصولة بفواصل:\n"
        f"(مثال: Python, Excel, إدارة المشاريع){hint}",
        reply_markup=skip_kb(),
    )


# ── Skills & Languages ─────────────────────────────────────────

@router.message(CVForm.skills)
async def process_skills(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "skills", message.text.strip())
    await state.set_state(CVForm.languages)
    await message.answer(
        "اكتب اللغات التي تتحدثها مع المستوى:\n"
        "(مثال: العربية - اللغة الأم، الإنجليزية - متقدم)",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.languages)
async def process_languages(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if not _is_skip(message):
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "languages", message.text.strip())
    await state.set_state(CVForm.course_name)
    async with await get_session() as session:
        await delete_user_courses(session, message.from_user.id)
    await message.answer(
        "هل لديك دورات أو شهادات مهنية؟\n"
        "اكتب اسم الدورة أو اضغط 'تخطي'",
        reply_markup=skip_kb(),
    )


# ── Courses ────────────────────────────────────────────────────

@router.message(CVForm.course_name)
async def process_course_name(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        await _go_to_projects(message, state)
        return
    await state.update_data(course_name=message.text.strip())
    await state.set_state(CVForm.course_provider)
    await message.answer("من هي الجهة المقدمة للدورة؟", reply_markup=skip_kb())


@router.message(CVForm.course_provider)
async def process_course_provider(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    provider = None if _is_skip(message) else message.text.strip()
    await state.update_data(course_provider=provider)
    await state.set_state(CVForm.course_year)
    await message.answer("ما هي سنة الحصول عليها؟", reply_markup=skip_kb())


@router.message(CVForm.course_year)
async def process_course_year(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    year = None if _is_skip(message) else message.text.strip()
    await state.update_data(course_year=year)

    data = await state.get_data()
    async with await get_session() as session:
        await add_course(session, message.from_user.id, {
            "name": data["course_name"],
            "provider": data.get("course_provider"),
            "year": data.get("course_year"),
        })

    await state.set_state(CVForm.course_add_more)
    await message.answer(
        "تم إضافة الدورة بنجاح!\nهل تريد إضافة دورة أخرى؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.course_add_more, F.text == "إلغاء")
async def cancel_at_course_more(message: Message, state: FSMContext) -> None:
    await _do_cancel(message, state)


@router.message(CVForm.course_add_more, F.text == "إضافة المزيد")
async def add_more_course(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.course_name)
    await message.answer("ما هو اسم الدورة التالية؟", reply_markup=skip_kb())


@router.message(CVForm.course_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_courses(message: Message, state: FSMContext) -> None:
    await _go_to_projects(message, state)


async def _go_to_projects(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.project_name)
    async with await get_session() as session:
        await delete_user_projects(session, message.from_user.id)
    await message.answer(
        "هل لديك مشاريع تريد إضافتها؟\n"
        "اكتب اسم المشروع أو اضغط 'تخطي'",
        reply_markup=skip_kb(),
    )


# ── Projects ───────────────────────────────────────────────────

@router.message(CVForm.project_name)
async def process_project_name(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    if _is_skip(message):
        await _finish_collection(message, state)
        return
    await state.update_data(project_name=message.text.strip())
    await state.set_state(CVForm.project_description)
    await message.answer("اكتب وصفاً مختصراً للمشروع:", reply_markup=skip_kb())


@router.message(CVForm.project_description)
async def process_project_desc(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    desc = None if _is_skip(message) else message.text.strip()
    await state.update_data(project_description=desc)
    await state.set_state(CVForm.project_link)
    await message.answer("ما هو رابط المشروع؟", reply_markup=skip_kb())


@router.message(CVForm.project_link)
async def process_project_link(message: Message, state: FSMContext) -> None:
    if _is_cancel(message):
        await _do_cancel(message, state)
        return
    link = None if _is_skip(message) else message.text.strip()
    await state.update_data(project_link=link)

    data = await state.get_data()
    async with await get_session() as session:
        await add_project(session, message.from_user.id, {
            "name": data["project_name"],
            "description": data.get("project_description"),
            "link": data.get("project_link"),
        })

    await state.set_state(CVForm.project_add_more)
    await message.answer(
        "تم إضافة المشروع بنجاح!\nهل تريد إضافة مشروع آخر؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.project_add_more, F.text == "إلغاء")
async def cancel_at_project_more(message: Message, state: FSMContext) -> None:
    await _do_cancel(message, state)


@router.message(CVForm.project_add_more, F.text == "إضافة المزيد")
async def add_more_project(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.project_name)
    await message.answer("ما هو اسم المشروع التالي؟", reply_markup=skip_kb())


@router.message(CVForm.project_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_projects(message: Message, state: FSMContext) -> None:
    await _finish_collection(message, state)


async def _finish_collection(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "✅ تم إدخال جميع البيانات بنجاح!\n\n"
        "يمكنك الآن:\n"
        "- معاينة البيانات للتأكد من صحتها\n"
        "- تعديل البيانات إذا أردت تغيير أي شيء\n"
        "- إنشاء PDF لإنشاء سيرتك الذاتية\n"
        "- حفظ السيرة الذاتية كنسخة منفصلة",
        reply_markup=main_menu_kb(),
    )
