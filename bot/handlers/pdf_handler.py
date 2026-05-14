import os

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile

from bot.database.engine import get_session
from bot.database.crud import get_user_full
from bot.services.pdf_generator import generate_cv_pdf
from bot.keyboards.reply_kb import main_menu_kb
from bot.config import logger

router = Router()


@router.message(F.text == "إنشاء PDF")
async def generate_pdf_btn(message: Message) -> None:
    await _do_generate_pdf(message)


@router.callback_query(F.data == "confirm_pdf")
async def generate_pdf_callback(callback: CallbackQuery) -> None:
    await callback.answer("جاري إنشاء ملف PDF...")
    await _do_generate_pdf(callback.message, user_id=callback.from_user.id)


async def _do_generate_pdf(message: Message, user_id: int | None = None) -> None:
    tid = user_id or message.from_user.id

    async with await get_session() as session:
        user = await get_user_full(session, tid)

    if not user or not user.full_name:
        await message.answer(
            "لم يتم إدخال أي بيانات بعد.\n"
            "اضغط 'إنشاء سيرة ذاتية' للبدء.",
            reply_markup=main_menu_kb(),
        )
        return

    await message.answer("جاري إنشاء ملف PDF... يرجى الانتظار.")

    filepath = await generate_cv_pdf(user)
    if not filepath:
        await message.answer(
            "حدث خطأ أثناء إنشاء ملف PDF. يرجى المحاولة مرة أخرى.",
            reply_markup=main_menu_kb(),
        )
        return

    try:
        doc = FSInputFile(filepath)
        await message.answer_document(
            doc,
            caption="سيرتك الذاتية جاهزة! 📄\nنتمنى لك التوفيق في مسيرتك المهنية.",
        )
    except Exception:
        logger.exception("Failed to send PDF")
        await message.answer(
            "حدث خطأ أثناء إرسال الملف. يرجى المحاولة مرة أخرى.",
            reply_markup=main_menu_kb(),
        )
    finally:
        try:
            os.unlink(filepath)
            os.rmdir(os.path.dirname(filepath))
        except OSError:
            pass

    await message.answer("هل تريد شيئاً آخر؟", reply_markup=main_menu_kb())
