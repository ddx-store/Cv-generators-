from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.cv_states import EditForm, CVForm
from bot.keyboards.inline_kb import edit_sections_kb
from bot.keyboards.reply_kb import main_menu_kb, cancel_kb
from bot.database.engine import get_session
from bot.database.crud import (
    update_user_field,
    get_user_full,
    delete_user_experiences,
    delete_user_educations,
    delete_user_courses,
    delete_user_projects,
)

router = Router()

FIELD_MAP = {
    "edit_full_name": ("full_name", "أدخل الاسم الكامل الجديد:"),
    "edit_job_title": ("job_title", "أدخل المسمى الوظيفي الجديد:"),
    "edit_phone": ("phone", "أدخل رقم الهاتف الجديد:"),
    "edit_email": ("email", "أدخل البريد الإلكتروني الجديد:"),
    "edit_city_country": ("city_country", "أدخل المدينة / الدولة:"),
    "edit_linkedin": ("linkedin", "أدخل رابط لينكد إن الجديد:"),
    "edit_portfolio": ("portfolio", "أدخل رابط الموقع / GitHub الجديد:"),
    "edit_summary": ("summary", "أدخل الملخص المهني الجديد:"),
    "edit_skills": ("skills", "أدخل المهارات الجديدة (مفصولة بفواصل):"),
    "edit_languages": ("languages", "أدخل اللغات الجديدة:"),
}


@router.message(F.text == "تعديل البيانات")
async def edit_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with await get_session() as session:
        user = await get_user_full(session, message.from_user.id)

    if not user or not user.full_name:
        await message.answer(
            "لم يتم إدخال أي بيانات بعد.\n"
            "اضغط 'إنشاء سيرة ذاتية' للبدء.",
            reply_markup=main_menu_kb(),
        )
        return

    await message.answer("اختر القسم الذي تريد تعديله:", reply_markup=edit_sections_kb())


@router.callback_query(F.data == "go_edit")
async def go_edit_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "اختر القسم الذي تريد تعديله:",
        reply_markup=edit_sections_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("القائمة الرئيسية:", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.in_(set(FIELD_MAP.keys())))
async def edit_simple_field(callback: CallbackQuery, state: FSMContext) -> None:
    field, prompt = FIELD_MAP[callback.data]
    await state.set_state(EditForm.editing_value)
    await state.update_data(edit_field=field)
    await callback.message.answer(prompt, reply_markup=cancel_kb())
    await callback.answer()


@router.message(EditForm.editing_value, F.text == "إلغاء")
async def cancel_edit(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("تم إلغاء التعديل.", reply_markup=main_menu_kb())


@router.message(EditForm.editing_value)
async def save_edited_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = data.get("edit_field", "")

    async with await get_session() as session:
        await update_user_field(session, message.from_user.id, field, message.text.strip())

    await state.clear()
    await message.answer("تم تحديث البيانات بنجاح!", reply_markup=main_menu_kb())


# Re-enter list sections
@router.callback_query(F.data == "edit_experiences")
async def edit_experiences(callback: CallbackQuery, state: FSMContext) -> None:
    async with await get_session() as session:
        await delete_user_experiences(session, callback.from_user.id)
    await state.set_state(CVForm.exp_company)
    await callback.message.answer("سيتم إعادة إدخال الخبرات العملية.\n\nما هو اسم الشركة؟")
    await callback.answer()


@router.callback_query(F.data == "edit_educations")
async def edit_educations(callback: CallbackQuery, state: FSMContext) -> None:
    async with await get_session() as session:
        await delete_user_educations(session, callback.from_user.id)
    await state.set_state(CVForm.edu_degree)
    await callback.message.answer("سيتم إعادة إدخال التعليم.\n\nما هي الدرجة العلمية؟")
    await callback.answer()


@router.callback_query(F.data == "edit_courses")
async def edit_courses(callback: CallbackQuery, state: FSMContext) -> None:
    async with await get_session() as session:
        await delete_user_courses(session, callback.from_user.id)
    await state.set_state(CVForm.course_name)
    await callback.message.answer(
        "سيتم إعادة إدخال الدورات.\n\nما هو اسم الدورة؟"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_projects")
async def edit_projects(callback: CallbackQuery, state: FSMContext) -> None:
    async with await get_session() as session:
        await delete_user_projects(session, callback.from_user.id)
    await state.set_state(CVForm.project_name)
    await callback.message.answer(
        "سيتم إعادة إدخال المشاريع.\n\nما هو اسم المشروع؟"
    )
    await callback.answer()
