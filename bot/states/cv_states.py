from aiogram.fsm.state import State, StatesGroup


class CVForm(StatesGroup):
    full_name = State()
    job_title = State()
    phone = State()
    email = State()
    city_country = State()
    linkedin = State()
    portfolio = State()
    summary = State()
    skills = State()
    languages = State()

    # Experience sub-flow
    exp_company = State()
    exp_title = State()
    exp_start = State()
    exp_end = State()
    exp_responsibilities = State()
    exp_add_more = State()

    # Education sub-flow
    edu_degree = State()
    edu_institution = State()
    edu_year = State()
    edu_add_more = State()

    # Courses sub-flow
    course_name = State()
    course_provider = State()
    course_year = State()
    course_add_more = State()

    # Projects sub-flow
    project_name = State()
    project_description = State()
    project_link = State()
    project_add_more = State()


class EditForm(StatesGroup):
    choosing_section = State()
    editing_field = State()
    editing_value = State()
