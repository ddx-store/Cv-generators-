from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="إنشاء سيرة ذاتية")],
            [KeyboardButton(text="تعديل البيانات"), KeyboardButton(text="معاينة البيانات")],
            [KeyboardButton(text="إنشاء PDF"), KeyboardButton(text="المساعدة")],
        ],
        resize_keyboard=True,
    )


def skip_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="تخطي")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def add_more_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="إضافة المزيد")],
            [KeyboardButton(text="الانتقال للخطوة التالية")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def yes_no_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="نعم"), KeyboardButton(text="لا")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="إلغاء")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
