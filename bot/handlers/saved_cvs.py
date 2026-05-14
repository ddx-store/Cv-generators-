from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.engine import get_session
from bot.database.crud import (
    get_user_full,
    save_cv_profile,
    list_cv_profiles,
    load_cv_profile,
    delete_cv_profile,
)
from bot.keyboards.reply_kb import main_menu_kb, cancel_kb

router = Router()


class SaveCVForm(StatesGroup):
    profile_name = State()


@router.message(F.text == "سيرتي المحفوظة")
async def my_saved_cvs(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with await get_session() as session:
        profiles = await list_cv_profiles(session, message.from_user.id)

    if not profiles:
        await message.answer(
            "لا توجد سير ذاتية محفوظة بعد.\n\n"
            "لحفظ سيرتك الذاتية الحالية، أدخل بياناتك أولاً ثم اضغط هنا لحفظ نسخة.",
            reply_markup=_saved_cv_actions_kb(has_data=True),
        )
        return

    lines = ["📂 سيرتي المحفوظة:\n"]
    for i, p in enumerate(profiles, 1):
        date_str = p.created_at.strftime("%Y-%m-%d") if p.created_at else ""
        lines.append(f"{i}. {p.profile_name}  ({date_str})")

    lines.append("\nاختر إجراء:")
    await message.answer(
        "\n".join(lines),
        reply_markup=_saved_cv_list_kb(profiles),
    )


def _saved_cv_actions_kb(has_data: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if has_data:
        buttons.append([InlineKeyboardButton(text="حفظ السيرة الحالية كنسخة جديدة", callback_data="save_current_cv")])
    buttons.append([InlineKeyboardButton(text="رجوع للقائمة الرئيسية", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _saved_cv_list_kb(profiles: list) -> InlineKeyboardMarkup:
    buttons = []
    for p in profiles:
        buttons.append([
            InlineKeyboardButton(text=f"📄 تحميل: {p.profile_name}", callback_data=f"load_cv_{p.id}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"del_cv_{p.id}"),
        ])
    buttons.append([InlineKeyboardButton(text="حفظ السيرة الحالية كنسخة جديدة", callback_data="save_current_cv")])
    buttons.append([InlineKeyboardButton(text="رجوع للقائمة الرئيسية", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data == "save_current_cv")
async def save_current_cv(callback: CallbackQuery, state: FSMContext) -> None:
    async with await get_session() as session:
        user = await get_user_full(session, callback.from_user.id)
    if not user or not user.full_name:
        await callback.message.answer(
            "لم يتم إدخال بيانات بعد. اضغط 'إنشاء سيرة ذاتية' للبدء.",
            reply_markup=main_menu_kb(),
        )
        await callback.answer()
        return

    await state.set_state(SaveCVForm.profile_name)
    await callback.message.answer(
        "اكتب اسماً لهذه النسخة:\n"
        "(مثال: سيرتي العربية، CV للتقنية، نسخة التسويق)",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(SaveCVForm.profile_name, F.text == "إلغاء")
async def cancel_save(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("تم الإلغاء.", reply_markup=main_menu_kb())


@router.message(SaveCVForm.profile_name)
async def do_save_profile(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    async with await get_session() as session:
        await save_cv_profile(session, message.from_user.id, name)
    await state.clear()
    await message.answer(
        f"تم حفظ السيرة الذاتية باسم \"{name}\" بنجاح!\n"
        "يمكنك تحميلها لاحقاً من 'سيرتي المحفوظة'.",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data.startswith("load_cv_"))
async def load_saved_cv(callback: CallbackQuery) -> None:
    profile_id = int(callback.data.replace("load_cv_", ""))
    async with await get_session() as session:
        success = await load_cv_profile(session, callback.from_user.id, profile_id)
    if success:
        await callback.message.answer(
            "تم تحميل السيرة الذاتية بنجاح!\n"
            "بياناتك الحالية تم تحديثها. يمكنك معاينتها أو إنشاء PDF.",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.message.answer("لم يتم العثور على هذه النسخة.", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("del_cv_"))
async def delete_saved_cv(callback: CallbackQuery) -> None:
    profile_id = int(callback.data.replace("del_cv_", ""))
    async with await get_session() as session:
        success = await delete_cv_profile(session, callback.from_user.id, profile_id)
    if success:
        await callback.message.answer("تم حذف النسخة المحفوظة.", reply_markup=main_menu_kb())
    else:
        await callback.message.answer("لم يتم العثور على هذه النسخة.", reply_markup=main_menu_kb())
    await callback.answer()
