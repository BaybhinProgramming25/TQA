def create_course_string(student_id, semester, course_names, course_numbers, course_descriptions, course_attempted_points, course_earned_points, course_letter_grades, course_total_points):

    tmp_holder_arr = []

    for name, number, description, attempted, earned, grade, total in zip(
        course_names,
        course_numbers,
        course_descriptions,
        course_attempted_points,
        course_earned_points,
        course_letter_grades,
        course_total_points
    ):

        tmp_string = f"""
            Student with ID {student_id} took this course {name} {number} during semester {semester}
            This course is about {description}
            They earned {earned} points out of the attempted {attempted} points.
            They received a letter grade of {grade} in this course
            They received a total of {total} points for this course.
        """

        metadata = {
            "studentId": student_id,
            "class": f"{name} {number}",
            "semester": semester,
            "description": description,
            "earned": earned,
            "attempted": attempted,
            "grade": grade,
            "total": total
        }

        course_tup = (tmp_string, metadata)
        tmp_holder_arr.append(course_tup)
    
    return tmp_holder_arr 
        