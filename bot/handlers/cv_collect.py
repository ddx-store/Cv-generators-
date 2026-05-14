from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.cv_states import CVForm
from bot.keyboards.reply_kb import skip_kb, add_more_kb, main_menu_kb
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


# ── Start CV creation ──────────────────────────────────────────

@router.message(F.text == "إنشاء سيرة ذاتية")
async def start_cv(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CVForm.full_name)
    await message.answer("ما هو اسمك الكامل؟")


# ── Basic fields ───────────────────────────────────────────────

@router.message(CVForm.full_name)
async def process_full_name(message: Message, state: FSMContext) -> None:
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "full_name", message.text.strip())
    await state.set_state(CVForm.job_title)
    await message.answer("ما هو المسمى الوظيفي أو الوظيفة المطلوبة؟")


@router.message(CVForm.job_title)
async def process_job_title(message: Message, state: FSMContext) -> None:
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "job_title", message.text.strip())
    await state.set_state(CVForm.phone)
    await message.answer("ما هو رقم هاتفك؟ (مثال: +966501234567)")


@router.message(CVForm.phone)
async def process_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    if not validate_phone(phone):
        await message.answer("رقم الهاتف غير صحيح. يرجى إدخال رقم صحيح (مثال: +966501234567)")
        return
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "phone", phone)
    await state.set_state(CVForm.email)
    await message.answer("ما هو بريدك الإلكتروني؟")


@router.message(CVForm.email)
async def process_email(message: Message, state: FSMContext) -> None:
    email = message.text.strip()
    if not validate_email(email):
        await message.answer("البريد الإلكتروني غير صحيح. يرجى إدخال بريد صحيح (مثال: name@email.com)")
        return
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "email", email)
    await state.set_state(CVForm.city_country)
    await message.answer("ما هي مدينتك / دولتك؟ (مثال: الرياض، السعودية)")


@router.message(CVForm.city_country)
async def process_city(message: Message, state: FSMContext) -> None:
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "city_country", message.text.strip())
    await state.set_state(CVForm.linkedin)
    await message.answer(
        "ما هو رابط حسابك على لينكد إن؟ (اختياري)",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.linkedin)
async def process_linkedin(message: Message, state: FSMContext) -> None:
    if message.text.strip() != "تخطي":
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "linkedin", message.text.strip())
    await state.set_state(CVForm.portfolio)
    await message.answer(
        "ما هو رابط موقعك الشخصي أو GitHub؟ (اختياري)",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.portfolio)
async def process_portfolio(message: Message, state: FSMContext) -> None:
    if message.text.strip() != "تخطي":
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "portfolio", message.text.strip())
    await state.set_state(CVForm.summary)
    await message.answer(
        "اكتب ملخصك المهني (2-3 جمل عن نفسك وخبراتك).\n"
        "إذا تركته فارغاً، سيتم إنشاء ملخص تلقائي بناءً على بياناتك.",
        reply_markup=skip_kb(),
    )


@router.message(CVForm.summary)
async def process_summary(message: Message, state: FSMContext) -> None:
    if message.text.strip() != "تخطي":
        async with await get_session() as session:
            await update_user_field(session, message.from_user.id, "summary", message.text.strip())
    # Move to experience collection
    await state.set_state(CVForm.exp_company)
    async with await get_session() as session:
        await delete_user_experiences(session, message.from_user.id)
    await message.answer(
        "الآن سنضيف خبراتك العملية.\n\nما هو اسم الشركة؟",
    )


# ── Experience ─────────────────────────────────────────────────

@router.message(CVForm.exp_company)
async def process_exp_company(message: Message, state: FSMContext) -> None:
    await state.update_data(exp_company=message.text.strip())
    await state.set_state(CVForm.exp_title)
    await message.answer("ما هو مسماك الوظيفي في هذه الشركة؟")


@router.message(CVForm.exp_title)
async def process_exp_title(message: Message, state: FSMContext) -> None:
    await state.update_data(exp_title=message.text.strip())
    await state.set_state(CVForm.exp_start)
    await message.answer("متى بدأت العمل؟ (مثال: يناير 2020)")


@router.message(CVForm.exp_start)
async def process_exp_start(message: Message, state: FSMContext) -> None:
    await state.update_data(exp_start=message.text.strip())
    await state.set_state(CVForm.exp_end)
    await message.answer(
        "متى انتهيت من العمل؟ (مثال: ديسمبر 2023)\n"
        "إذا كنت لا تزال تعمل هنا، اكتب 'حتى الآن'",
    )


@router.message(CVForm.exp_end)
async def process_exp_end(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    end_date = None if text == "حتى الآن" else text
    await state.update_data(exp_end=end_date)
    await state.set_state(CVForm.exp_responsibilities)
    await message.answer("اكتب أهم المهام والإنجازات (كل مهمة في سطر جديد):")


@router.message(CVForm.exp_responsibilities)
async def process_exp_responsibilities(message: Message, state: FSMContext) -> None:
    await state.update_data(exp_responsibilities=message.text.strip())

    data = await state.get_data()
    async with await get_session() as session:
        await add_experience(session, message.from_user.id, {
            "company": data["exp_company"],
            "title": data["exp_title"],
            "start_date": data["exp_start"],
            "end_date": data.get("exp_end"),
            "responsibilities": data["exp_responsibilities"],
        })

    await state.set_state(CVForm.exp_add_more)
    await message.answer(
        "تم إضافة الخبرة بنجاح!\n"
        "هل تريد إضافة خبرة عمل أخرى؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.exp_add_more, F.text == "إضافة المزيد")
async def add_more_exp(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.exp_company)
    await message.answer("ما هو اسم الشركة التالية؟")


@router.message(CVForm.exp_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_exp(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.edu_degree)
    async with await get_session() as session:
        await delete_user_educations(session, message.from_user.id)
    await message.answer("الآن سنضيف التعليم.\n\nما هي الدرجة العلمية؟ (مثال: بكالوريوس هندسة حاسب)")


# ── Education ──────────────────────────────────────────────────

@router.message(CVForm.edu_degree)
async def process_edu_degree(message: Message, state: FSMContext) -> None:
    await state.update_data(edu_degree=message.text.strip())
    await state.set_state(CVForm.edu_institution)
    await message.answer("ما هو اسم الجامعة أو المؤسسة التعليمية؟")


@router.message(CVForm.edu_institution)
async def process_edu_institution(message: Message, state: FSMContext) -> None:
    await state.update_data(edu_institution=message.text.strip())
    await state.set_state(CVForm.edu_year)
    await message.answer("ما هي سنة التخرج؟ (مثال: 2022)", reply_markup=skip_kb())


@router.message(CVForm.edu_year)
async def process_edu_year(message: Message, state: FSMContext) -> None:
    year = None if message.text.strip() == "تخطي" else message.text.strip()
    await state.update_data(edu_year=year)

    data = await state.get_data()
    async with await get_session() as session:
        await add_education(session, message.from_user.id, {
            "degree": data["edu_degree"],
            "institution": data["edu_institution"],
            "graduation_year": data.get("edu_year"),
        })

    await state.set_state(CVForm.edu_add_more)
    await message.answer(
        "تم إضافة التعليم بنجاح!\n"
        "هل تريد إضافة شهادة تعليمية أخرى؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.edu_add_more, F.text == "إضافة المزيد")
async def add_more_edu(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.edu_degree)
    await message.answer("ما هي الدرجة العلمية التالية؟")


@router.message(CVForm.edu_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_edu(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.skills)
    await message.answer("اكتب مهاراتك مفصولة بفواصل:\n(مثال: Python, Excel, إدارة المشاريع)")


# ── Skills & Languages ─────────────────────────────────────────

@router.message(CVForm.skills)
async def process_skills(message: Message, state: FSMContext) -> None:
    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, "skills", message.text.strip())
    await state.set_state(CVForm.languages)
    await message.answer("اكتب اللغات التي تتحدثها مع المستوى:\n(مثال: العربية - اللغة الأم، الإنجليزية - متقدم)")


@router.message(CVForm.languages)
async def process_languages(message: Message, state: FSMContext) -> None:
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
    if message.text.strip() == "تخطي":
        await state.set_state(CVForm.project_name)
        async with await get_session() as session:
            await delete_user_projects(session, message.from_user.id)
        await message.answer(
            "هل لديك مشاريع تريد إضافتها؟\n"
            "اكتب اسم المشروع أو اضغط 'تخطي'",
            reply_markup=skip_kb(),
        )
        return
    await state.update_data(course_name=message.text.strip())
    await state.set_state(CVForm.course_provider)
    await message.answer("من هي الجهة المقدمة للدورة؟ (اختياري)", reply_markup=skip_kb())


@router.message(CVForm.course_provider)
async def process_course_provider(message: Message, state: FSMContext) -> None:
    provider = None if message.text.strip() == "تخطي" else message.text.strip()
    await state.update_data(course_provider=provider)
    await state.set_state(CVForm.course_year)
    await message.answer("ما هي سنة الحصول عليها؟ (اختياري)", reply_markup=skip_kb())


@router.message(CVForm.course_year)
async def process_course_year(message: Message, state: FSMContext) -> None:
    year = None if message.text.strip() == "تخطي" else message.text.strip()
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
        "تم إضافة الدورة بنجاح!\n"
        "هل تريد إضافة دورة أخرى؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.course_add_more, F.text == "إضافة المزيد")
async def add_more_course(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.course_name)
    await message.answer("ما هو اسم الدورة التالية؟")


@router.message(CVForm.course_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_courses(message: Message, state: FSMContext) -> None:
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
    if message.text.strip() == "تخطي":
        await _finish_collection(message, state)
        return
    await state.update_data(project_name=message.text.strip())
    await state.set_state(CVForm.project_description)
    await message.answer("اكتب وصفاً مختصراً للمشروع:", reply_markup=skip_kb())


@router.message(CVForm.project_description)
async def process_project_desc(message: Message, state: FSMContext) -> None:
    desc = None if message.text.strip() == "تخطي" else message.text.strip()
    await state.update_data(project_description=desc)
    await state.set_state(CVForm.project_link)
    await message.answer("ما هو رابط المشروع؟ (اختياري)", reply_markup=skip_kb())


@router.message(CVForm.project_link)
async def process_project_link(message: Message, state: FSMContext) -> None:
    link = None if message.text.strip() == "تخطي" else message.text.strip()
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
        "تم إضافة المشروع بنجاح!\n"
        "هل تريد إضافة مشروع آخر؟",
        reply_markup=add_more_kb(),
    )


@router.message(CVForm.project_add_more, F.text == "إضافة المزيد")
async def add_more_project(message: Message, state: FSMContext) -> None:
    await state.set_state(CVForm.project_name)
    await message.answer("ما هو اسم المشروع التالي؟")


@router.message(CVForm.project_add_more, F.text == "الانتقال للخطوة التالية")
async def next_after_projects(message: Message, state: FSMContext) -> None:
    await _finish_collection(message, state)


async def _finish_collection(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "تم إدخال جميع البيانات بنجاح! 🎉\n\n"
        "يمكنك الآن:\n"
        "- معاينة البيانات للتأكد من صحتها\n"
        "- تعديل البيانات إذا أردت تغيير أي شيء\n"
        "- إنشاء PDF لإنشاء سيرتك الذاتية",
        reply_markup=main_menu_kb(),
    )
