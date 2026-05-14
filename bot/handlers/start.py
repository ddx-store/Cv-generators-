from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards.reply_kb import main_menu_kb

router = Router()

WELCOME_TEXT = (
    "مرحباً بك في بوت إنشاء السيرة الذاتية الاحترافية! 📄\n\n"
    "يساعدك هذا البوت في إنشاء سيرة ذاتية متوافقة مع أنظمة تتبع المتقدمين (ATS) "
    "وإرسالها لك كملف PDF جاهز.\n\n"
    "يدعم البوت اللغة العربية والإنجليزية — يمكنك كتابة بياناتك بأي لغة.\n\n"
    "يمكنك تخطي أي خطوة بالضغط على 'تخطي'.\n\n"
    "اختر من القائمة أدناه للبدء:"
)

HELP_TEXT = (
    "دليل استخدام البوت:\n\n"
    "1. إنشاء سيرة ذاتية - لبدء إدخال بياناتك خطوة بخطوة\n"
    "2. تعديل البيانات - لتعديل أي قسم من بياناتك\n"
    "3. معاينة البيانات - لعرض جميع البيانات المدخلة\n"
    "4. إنشاء PDF - لإنشاء ملف PDF من بياناتك\n"
    "5. المساعدة - لعرض هذا الدليل\n\n"
    "ملاحظات:\n"
    "- يدعم البوت العربي والإنجليزي — اكتب بأي لغة تناسبك\n"
    "- يمكنك تخطي أي خطوة بالضغط على 'تخطي'\n"
    "- يمكنك إضافة أكثر من خبرة عمل أو شهادة\n"
    "- راجع بياناتك قبل إنشاء الملف النهائي\n"
    "- للبدء من جديد، اضغط /start"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu_kb())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_kb())


@router.message(F.text == "المساعدة")
async def btn_help(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_menu_kb())
