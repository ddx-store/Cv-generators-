from aiogram import Router, F
from aiogram.types import Message

from bot.database.engine import get_session
from bot.database.crud import get_user_full
from bot.utils.text_helpers import format_preview
from bot.keyboards.reply_kb import main_menu_kb
from bot.keyboards.inline_kb import confirm_generate_kb

router = Router()


@router.message(F.text == "معاينة البيانات")
async def preview_data(message: Message) -> None:
    async with await get_session() as session:
        user = await get_user_full(session, message.from_user.id)

    if not user or not user.full_name:
        await message.answer(
            "لم يتم إدخال أي بيانات بعد.\n"
            "اضغط 'إنشاء سيرة ذاتية' للبدء.",
            reply_markup=main_menu_kb(),
        )
        return

    preview_text = format_preview(user)
    await message.answer(preview_text, reply_markup=confirm_generate_kb())
