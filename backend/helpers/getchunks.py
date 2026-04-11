import re
import fitz

from helpers.constants import SEASONS, AVOIDED_CLASSES, TRANSFER_FORMARTS, TERMINATING_WORDS, GRADES_VALUE_MAPPING, MATH_PLACEMENT_MAPPING

def parse_pdf(file_bytes) -> list[str]:

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    pdf_pages_list = []
    for page in doc:
        text = page.get_text("text").strip("").split("\n")
        pdf_pages_list.extend(text)
    pdf_pages_list = [sanitize_text(" ".join(line.split())) for line in pdf_pages_list if line.strip()]
    
    all_chunks =  [
        *get_sem_level_chunks(pdf_pages_list),
        *get_course_level_chunks(pdf_pages_list),
        *get_student_info_chunks(pdf_pages_list),
    ]

    return all_chunks


def sanitize_text(text: str) -> str: 

    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'(rm -rf|sudo|chmod|curl|wget|bash|sh -c).*', '', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^\w\s.,;:!?\-\'\"()/]', '', text)
    return text.strip()



def get_sem_level_chunks(pdf_pages_list: list[str]) -> list[tuple[str, dict]]:

    semester_indices = _get_semester_indices(pdf_pages_list)

    semester_chunks = []
    for i in range(len(semester_indices)):
        label, start = semester_indices[i]
        end = semester_indices[i + 1][1] if i + 1 < len(semester_indices) else len(pdf_pages_list)
        data = pdf_pages_list[start:end]

        courses = _get_sem_courses(data)
        num_courses = len(courses)
        term_gpa = _get_gpa_after_keyword(data, "Term")
        cum_gpa = _get_gpa_after_keyword(data, "Cum")
        if cum_gpa == 0.0:
            cum_gpa = term_gpa
        duration = _get_sem_duration(data)

        chunk = (
            f"During {label}{f' ({duration})' if duration else ''}, the student took {num_courses} courses: {', '.join(courses)}, "
            f"Term GPA: {term_gpa}, Cumulative GPA: {cum_gpa}"
        )
        metadata = {
            "type": "semester",
            "semester": label,
            "duration": duration,
            "term_gpa": term_gpa,
            "cum_gpa": cum_gpa,
            "num_courses": num_courses,
            "courses": courses,
        }
        semester_chunks.append((chunk, metadata))

    chunk = (
        f"The student took {len(semester_chunks)} semesters in total"
    )

    metadata = {
        "num_semesters": len(semester_chunks)
    }

    semester_chunks.append((chunk, metadata))
    
    return semester_chunks


def _is_valid_course_format(value: str) -> bool:

    if len(value) < 3:
        return False
    return all(char.isdigit() for char in value[0:3]) or any(word in value for word in TRANSFER_FORMARTS)


def _get_sem_courses(data: list[str]) -> list[str]:

    courses = []
    i = 0
    while i < len(data):
        value = data[i].strip()
        if len(value) >= 3 and all(c.isupper() for c in value) and value not in AVOIDED_CLASSES:
            if i + 1 < len(data) and _is_valid_course_format(data[i + 1].strip()):
                courses.append(f"{value} {data[i + 1].strip()}")
                i += 2
                continue
        i += 1
    return courses


def _get_sem_duration(data: list[str]) -> str:

    date_pattern = re.compile(r'\d{2}/\d{2}/\d{4}')
    date_range_pattern = re.compile(r'\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4}')

    for line in data:
        match = date_range_pattern.search(line)
        if match:
            return match.group().replace(" ", "")

    for i in range(len(data) - 1):
        m1 = date_pattern.fullmatch(data[i].strip())
        m2 = date_pattern.fullmatch(data[i + 1].strip())
        if m1 and m2:
            return f"{m1.group()}-{m2.group()}"

    return ""


def _get_gpa_after_keyword(data: list[str], keyword: str) -> float:
    other_keyword = "Cum" if keyword == "Term" else "Term"

    for i, value in enumerate(data):
        if value.strip().startswith(keyword):
            decimals = []
            for j in range(i, min(i + 11, len(data))):
                line = data[j].strip()
                if j > i and line.startswith(other_keyword):
                    break
                for token in line.split():
                    if token.count('.') == 1:
                        parts = token.split('.')
                        if parts[0].isdigit() and parts[1].isdigit():
                            decimals.append(float(token))
            gpa_candidates = [d for d in decimals if d <= 4.0]
            return gpa_candidates[-1] if gpa_candidates else 0.0
    return 0.0



def get_course_level_chunks(pdf_pages_list: list[str]) -> list[tuple[str, dict]]:

    semester_indices = _get_semester_indices(pdf_pages_list)

    course_chunks = []
    for i in range(len(semester_indices)):
        label, start = semester_indices[i]
        end = semester_indices[i + 1][1] if i + 1 < len(semester_indices) else len(pdf_pages_list)
        data = pdf_pages_list[start:end]
        course_chunks.extend(_extract_course_chunks(data, label))

    return course_chunks


def _get_semester_indices(pdf_pages_list: list[str]) -> list[tuple]:

    semester_indices = []
    seen_labels = {}

    for index, value in enumerate(pdf_pages_list):
        value = value.strip()
        for season in SEASONS:
            if value.startswith(season):
                remainder = value[len(season):].strip()
                if remainder.isdigit() and len(remainder) == 4:
                    if value in seen_labels:
                        first_index = seen_labels[value]
                        semester_indices[first_index] = ("Transfer Credits", semester_indices[first_index][1])
                        semester_indices.append((value, index))
                    else:
                        seen_labels[value] = len(semester_indices)
                        semester_indices.append((value, index))
                break

    return semester_indices


def _is_course_name(value: str) -> bool:
    return len(value) >= 3 and all(c.isupper() for c in value) and value not in AVOIDED_CLASSES


def _is_decimal(value: str) -> bool:
    return value.count('.') == 1 and all(p.isdigit() for p in value.split('.'))


def _is_grade(value: str) -> bool:
    return value in GRADES_VALUE_MAPPING or value in MATH_PLACEMENT_MAPPING


def _is_terminator(value: str) -> bool:
    return any(term in value for term in TERMINATING_WORDS)


def _extract_course_chunks(data: list[str], semester_label: str) -> list[tuple[str, dict]]:

    chunks = []
    i = 0

    while i < len(data):
        value = data[i].strip()

        if _is_course_name(value) and i + 1 < len(data) and _is_valid_course_format(data[i + 1].strip()):
            course = f"{value} {data[i + 1].strip()}"
            j = i + 2

            description = data[j].strip() if j < len(data) else "N/A"
            j += 1

            attempted = 0.0
            earned = 0.0
            grade = "N/A"

            while j < len(data):
                v = data[j].strip()

                if _is_terminator(v):
                    break
                if _is_course_name(v) and j + 1 < len(data) and _is_valid_course_format(data[j + 1].strip()):
                    break

                if _is_decimal(v):
                    if attempted == 0.0:
                        attempted = float(v)
                    elif earned == 0.0:
                        earned = float(v)
                elif _is_grade(v):
                    grade = v

                j += 1

            grade_value = GRADES_VALUE_MAPPING.get(grade, MATH_PLACEMENT_MAPPING.get(grade, 0.0))
            points = round(grade_value * earned, 2)

            chunk = (
                f"The student took {course} in {semester_label}. "
                f"Description: {description}. "
                f"Attempted: {attempted}. Earned: {earned}. "
                f"Grade: {grade}. Points: {points}."
            )
            metadata = {
                "type": "course",
                "course": course,
                "semester": semester_label,
                "description": description,
                "attempted": attempted,
                "earned": earned,
                "grade": grade,
                "points": points,
            }
            chunks.append((chunk, metadata))
            i = j
            continue

        i += 1

    return chunks


def get_student_info_chunks(pdf_pages_list: list[str]) -> list[tuple[str, dict]]:

    name = _get_field_after_keyword(pdf_pages_list, "Name:")
    student_id = _get_field_after_keyword(pdf_pages_list, "Student ID:")
    major = _get_field_after_keyword(pdf_pages_list, "Plan:")

    semester_indices = _get_semester_indices(pdf_pages_list)
    real_semesters = [(label, start) for label, start in semester_indices if label != "Transfer Credits"]
    total_semesters = len(real_semesters)


    seen_courses = set()
    for i, (_, start) in enumerate(real_semesters):
        end = real_semesters[i + 1][1] if i + 1 < len(real_semesters) else len(pdf_pages_list)
        data = pdf_pages_list[start:end]
        seen_courses.update(_get_sem_courses(data))
    total_courses = len(seen_courses)

  
    final_cum_gpa = 0.0
    for i in range(len(pdf_pages_list) - 1, -1, -1):
        if pdf_pages_list[i].strip().startswith("Cum"):
            final_cum_gpa = _get_gpa_after_keyword(pdf_pages_list[i:i + 11], "Cum")
            if final_cum_gpa > 0.0:
                break

    chunks = []

    chunk_student = (
        f"Student Name: {name},"
        f"Student ID: {student_id},"
        f"University: Stony Brook University,"
        f"Major: {major},"
        f"Final Cumulative GPA: {final_cum_gpa if final_cum_gpa > 0.0 else 'N/A'},"
    )


    metadata_student = {
        "type": "student",
        "name": name,
        "student_id": student_id,
        "university": "Stony Brook University",
        "major": major,
        "final_cum_gpa": final_cum_gpa if final_cum_gpa > 0.0 else None,
    }

    chunk_total = (
        f"Total Semesters: {total_semesters},"
        f"Total Courses: {total_courses}"
    )

    metadata_total = {
        "type": "total",
        "total_semesters": total_semesters,
        "total_courses": total_courses
    }

    chunks.append((chunk_student, metadata_student))
    chunks.append((chunk_total, metadata_total))
    return chunks


def _get_field_after_keyword(pdf_pages_list: list[str], keyword: str) -> str:

    for i, line in enumerate(pdf_pages_list):
        if keyword in line:
            after = line.split(keyword, 1)[-1].strip()
            if after:
                return after
            if i + 1 < len(pdf_pages_list):
                return pdf_pages_list[i + 1].strip()
    return "N/A"