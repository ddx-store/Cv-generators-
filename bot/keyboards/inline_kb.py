from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def edit_sections_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="الاسم الكامل", callback_data="edit_full_name")],
        [InlineKeyboardButton(text="المسمى الوظيفي", callback_data="edit_job_title")],
        [InlineKeyboardButton(text="رقم الهاتف", callback_data="edit_phone")],
        [InlineKeyboardButton(text="البريد الإلكتروني", callback_data="edit_email")],
        [InlineKeyboardButton(text="المدينة / الدولة", callback_data="edit_city_country")],
        [InlineKeyboardButton(text="لينكد إن", callback_data="edit_linkedin")],
        [InlineKeyboardButton(text="الموقع / GitHub", callback_data="edit_portfolio")],
        [InlineKeyboardButton(text="الملخص المهني", callback_data="edit_summary")],
        [InlineKeyboardButton(text="المهارات", callback_data="edit_skills")],
        [InlineKeyboardButton(text="اللغات", callback_data="edit_languages")],
        [InlineKeyboardButton(text="الخبرات العملية (إعادة إدخال)", callback_data="edit_experiences")],
        [InlineKeyboardButton(text="التعليم (إعادة إدخال)", callback_data="edit_educations")],
        [InlineKeyboardButton(text="الدورات (إعادة إدخال)", callback_data="edit_courses")],
        [InlineKeyboardButton(text="المشاريع (إعادة إدخال)", callback_data="edit_projects")],
        [InlineKeyboardButton(text="رجوع للقائمة الرئيسية", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_generate_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="إنشاء PDF", callback_data="confirm_pdf"),
                InlineKeyboardButton(text="تعديل البيانات", callback_data="go_edit"),
            ],
            [InlineKeyboardButton(text="رجوع", callback_data="back_to_menu")],
        ]
    )
