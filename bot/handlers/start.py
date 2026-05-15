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
    "مميزات البوت:\n"
    "• يدعم العربية والإنجليزية\n"
    "• قوالب مهارات جاهزة حسب المجال\n"
    "• حفظ أكثر من سيرة ذاتية\n"
    "• تخطي أي خطوة + إلغاء في أي وقت\n"
    "• شريط تقدم يوضح الخطوات المتبقية\n\n"
    "اختر من القائمة أدناه للبدء:"
)

HELP_TEXT = (
    "دليل استخدام البوت:\n\n"
    "1. إنشاء سيرة ذاتية - لبدء إدخال بياناتك خطوة بخطوة\n"
    "2. تعديل البيانات - لتعديل أي قسم من بياناتك\n"
    "3. معاينة البيانات - لعرض جميع البيانات المدخلة\n"
    "4. إنشاء PDF - لإنشاء ملف PDF من بياناتك\n"
    "5. سيرتي المحفوظة - لحفظ وتحميل نسخ مختلفة\n"
    "6. المساعدة - لعرض هذا الدليل\n\n"
    "ملاحظات:\n"
    "- اختر لغة السيرة (عربي/إنجليزي) في بداية الإنشاء\n"
    "- قوالب مهارات مقترحة حسب المسمى الوظيفي\n"
    "- يمكنك تخطي أي خطوة بالضغط على 'تخطي'\n"
    "- اضغط 'إلغاء' للعودة للقائمة الرئيسية في أي وقت\n"
    "- احفظ أكثر من نسخة (عربي، إنجليزي، حسب المجال)\n"
    "- شريط تقدم يوضح الخطوات المتبقية\n"
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
