from .Constants import AVOIDED_CLASSES, GRADES_VALUE_MAPPING, TRANSFER_FORMARTS, MATH_PLACEMENT_MAPPING, TERMINATING_WORDS
from .BuildCourse import create_course_string

def get_content_from_each_sem(sm_ll, pdf_pages_list):

    if sm_ll is None or sm_ll.head.next is None:
        return 
    
    slow_ptr = sm_ll.head
    fast_ptr = slow_ptr.next

    student_id = get_student_id(pdf_pages_list[slow_ptr.data[1]])
    
    tup_holder = []
    classes_holder = []
    metadata_holder = []

    while fast_ptr:
        sub_arr = pdf_pages_list[slow_ptr.data[1]:fast_ptr.data[1]]

        course_names = get_course_name(sub_arr)
        course_numbers = get_course_number(sub_arr)
        course_descriptions = get_course_description(sub_arr)
        course_attempted_points = get_course_points_attempted(sub_arr)
        course_earned_points = get_course_points_earned(sub_arr)
        course_letter_grades = get_course_letter(sub_arr)
        course_total_points = get_course_total_points(sub_arr)

        course_tup_arr = create_course_string(student_id, slow_ptr.data[0], course_names, course_numbers, course_descriptions, course_attempted_points, course_earned_points, course_letter_grades, course_total_points)
        tup_holder.extend(course_tup_arr)

        slow_ptr = fast_ptr
        fast_ptr = fast_ptr.next
    
    # Divide them into tuples 
    for value1, value2 in tup_holder:
        classes_holder.append(value1)
        metadata_holder.append(value2)
    
    return (classes_holder, metadata_holder)

def get_student_id(text):

    student_id = text.split(":")[-1].strip()
    return student_id

def get_course_name(sub_arr):

    courses_letters = []
    for value in sub_arr:
        value = value.strip()
        if len(value) >= 3 and all(char.isupper() for char in value) and value not in AVOIDED_CLASSES:
            courses_letters.append(value)
    return courses_letters


def get_course_number(sub_arr):

    course_numbers = []
    for value in sub_arr:
        value = value.strip()
        if is_terminate(value):
            break
        if is_valid_course_format(value):
            course_numbers.append(value)
    return course_numbers


def get_course_description(sub_arr):

    description_container = []
    description_toggle = False 
    for value in sub_arr:
        value = value.strip()
        if is_terminate(value):
            break
        if description_toggle:
            description_container.append(value)
            description_toggle = False 
        if is_valid_course_format(value):
            description_toggle = True 
    
    return description_container

def get_course_points_attempted(sub_arr):
    
    points_attempted_container = []
    parse_points_toggle = True  
    for value in sub_arr:
        value = value.strip()
        if is_terminate(value):
            break
        if is_valid_course_format(value):
            parse_points_toggle = True 
        if parse_points_toggle and value.count('.') == 1:
            parts = value.split('.')
            left = parts[0]
            right = parts[1]
            if left.isdigit() and right.isdigit():
                points_attempted_container.append(value)
                parse_points_toggle = False   
    
    return points_attempted_container

def get_course_points_earned(sub_arr):

    points_earned_container = []
    points_earned_found = False 

    for i in range(len(sub_arr)):
        value = sub_arr[i].strip()
        if is_terminate(value):
            break 
        if is_valid_course_format(value) and points_earned_found:
            points_earned_found = False 
        if not points_earned_found and value.count('.') == 1:
            parts = value.split('.')
            if parts[0].isdigit() and parts[1].isdigit():
                if i + 1 < len(sub_arr):
                    next_value = sub_arr[i+1].strip().split('.')
                    if len(next_value) > 1 and next_value[0].isdigit() and next_value[1].isdigit():
                        points_earned_found = True 
                        points_earned_container.append(sub_arr[i+1])
                    else:
                        points_earned_container.append("") # Empty s tring as placeholder 

    return points_earned_container

def get_course_letter(sub_arr):

    letter_container = []
    letter_found = False 
    
    for i in range(len(sub_arr)):
        value = sub_arr[i].strip()
        if is_terminate(value):
            break 
        if is_valid_course_format(value) and letter_found:
            letter_found = False 
        if not letter_found and value.count('.') == 1:
            parts = value.split('.')
            if parts[0].isdigit() and parts[1].isdigit():                
                if i + 2 < len(sub_arr):
                    next_value = sub_arr[i+2].strip()
                    if (next_value in GRADES_VALUE_MAPPING.keys()) or (next_value in MATH_PLACEMENT_MAPPING.keys()):
                        letter_found = True 
                        letter_container.append(next_value)
                    else:
                        letter_container.append("") # Empty string as placeholder

    return letter_container

def get_course_total_points(sub_arr):
    
    total_points_container = []
    total_points_found = False 
    
    for i in range(len(sub_arr)):
        value = sub_arr[i].strip()
        if is_terminate(value):
            break 
        if  is_valid_course_format(value) and total_points_found:
            total_points_found = False 
        if not total_points_found and value.count('.') == 1:
            parts = value.split('.')
            if parts[0].isdigit() and parts[1].isdigit():                
                if i + 3 < len(sub_arr):
                    next_value = sub_arr[i+3].strip().split('.')
                    if len(next_value) > 1 and next_value[0].isdigit() and next_value[1].isdigit():
                        total_points_found = True 
                        total_points_container.append(sub_arr[i+3])
                    else:
                        total_points_container.append("") # Empty string as placeholder 

    return total_points_container


def is_valid_course_format(value):
    if len(value) < 3:
        return False 
    return all(char.isdigit() for char in value[0:3]) or any(word in value for word in TRANSFER_FORMARTS)

def is_terminate(value):
    return any(word in value for word in TERMINATING_WORDS)
