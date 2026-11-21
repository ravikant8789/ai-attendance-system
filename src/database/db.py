from src.database.config import supabase
import bcrypt
import time



def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())


def check_teacher_exists(username):
    # Check for unique username, returns false when username is already taken
    response = supabase.table("teachers").select("username").eq("username", username).execute()
    return len(response.data) > 0 

check_hr_exists = check_teacher_exists


def create_teacher(username, password, name):
    data = { "username" : username, "password": hash_pass(password), "name": name}
    response = supabase.table("teachers").insert(data).execute()
    return response.data

create_hr = create_teacher


def teacher_login(username, password):
    response = supabase.table("teachers").select("*").eq("username", username).execute()
    if response.data:
        teacher = response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None

hr_login = teacher_login


def reset_teacher_password(username, name, new_password):
    try:
        response = supabase.table("teachers").select("*").eq("username", username).execute()
        if not response.data:
            return False, "Username not found!"
        
        teacher = response.data[0]
        if name.strip().lower() != teacher.get("name", "").strip().lower():
            return False, "Registered name does not match this username!"
        
        hashed = hash_pass(new_password)
        res = supabase.table("teachers").update({"password": hashed}).eq("username", username).execute()
        if res.data:
            return True, "Password updated successfully!"
        return False, "Could not update password. Please try again."
    except Exception as e:
        return False, f"Database error: {str(e)}"

reset_hr_password = reset_teacher_password


def get_all_students(retries=3, delay=0.5):
    for attempt in range(retries):
        try:
            response = supabase.table('students').select("*").execute()
            return response.data or []
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"Warning: Failed to fetch students from database: {e}")
                return []

get_all_employees = get_all_students


def create_student(new_name, face_embedding=None, voice_embedding=None):
    data = {'name': new_name, 'face_embedding':face_embedding, "voice_embedding": voice_embedding}
    response = supabase.table('students').insert(data).execute()
    return response.data

create_employee = create_student


def create_subject(subject_code, name, section, teacher_id):
    data = {"subject_code": subject_code, "name": name, "section": section, "teacher_id": teacher_id}
    response = supabase.table("subjects").insert(data).execute()
    return response.data

create_department = create_subject


def get_teacher_subjects(teacher_id, retries=3, delay=0.5):
    for attempt in range(retries):
        try:
            response = supabase.table('subjects').select("*, subject_students(count), attendance_logs(timestamp)").eq("teacher_id", teacher_id).execute()
            subjects = response.data or []

            for sub in subjects:
                sub['total_students'] = sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
                attendance = sub.get('attendance_logs', [])
                unique_sessions = len(set(log['timestamp'] for log in attendance))
                sub['total_classes'] = unique_sessions

                sub.pop('subject_student', None)
                sub.pop('attendance_logs', None)

            return subjects
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print(f"Warning: Failed to fetch teacher departments: {e}")
                return []

get_hr_departments = get_teacher_subjects


def enroll_student_to_subject(student_id, subject_id):
    data = {'student_id': student_id, "subject_id": subject_id}
    response = supabase.table('subject_students').insert(data).execute()
    return response.data

assign_employee_to_department = enroll_student_to_subject


def unenroll_student_to_subject(student_id, subject_id):
    response = supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data

remove_employee_from_department = unenroll_student_to_subject


def get_student_subjects(student_id, retries=3, delay=0.5):
    for attempt in range(retries):
        try:
            response = supabase.table('subject_students').select('*, subjects(*)').eq('student_id', student_id).execute()
            return response.data or []
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return []

get_employee_departments = get_student_subjects


def get_student_attendance(student_id, retries=3, delay=0.5):
    for attempt in range(retries):
        try:
            response = supabase.table('attendance_logs').select('*, subjects(*)').eq('student_id', student_id).execute()
            return response.data or []
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                return []

get_employee_attendance = get_student_attendance


def record_clock_out(student_id):
    """
    Records clock-out timestamp for today's active session.
    Persists to `clock_out` column in `attendance_logs` table.
    """
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    try:
        res = supabase.table('attendance_logs') \
            .select('id') \
            .eq('student_id', student_id) \
            .gte('timestamp', f"{today_str}T00:00:00") \
            .lte('timestamp', f"{today_str}T23:59:59") \
            .execute()

        log_ids = [row['id'] for row in (res.data or [])]
        if log_ids:
            for lid in log_ids:
                supabase.table('attendance_logs') \
                    .update({'clock_out': current_ts}) \
                    .eq('id', lid) \
                    .execute()
            return True, current_ts
        return False, "No clock-in record found for today."
    except Exception as e:
        return False, str(e)


def create_attendance(logs):
    """
    Idempotent attendance logging. Prevents duplicate attendance rows for the same
    employee, department, and calendar date. If an attendance row already exists today:
    - If new log is present (True) and existing was absent (False), updates it to present.
    - If already recorded as present, ignores duplicate insertion.
    - Otherwise inserts new log.
    """
    if not logs:
        return []

    try:
        dates = set(l.get('timestamp', '')[:10] for l in logs if l.get('timestamp'))
        subject_ids = set(l.get('subject_id') for l in logs if l.get('subject_id'))

        existing_logs = []
        for sid in subject_ids:
            for d in dates:
                res = supabase.table('attendance_logs') \
                    .select('*') \
                    .eq('subject_id', sid) \
                    .gte('timestamp', f"{d}T00:00:00") \
                    .lte('timestamp', f"{d}T23:59:59") \
                    .execute()
                if res.data:
                    existing_logs.extend(res.data)

        # Map: (student_id, subject_id, date) -> existing record
        existing_map = {}
        for el in existing_logs:
            ts = el.get('timestamp', '')
            if ts:
                existing_map[(el['student_id'], el['subject_id'], ts[:10])] = el

        to_insert = []
        for l in logs:
            ts = l.get('timestamp', '')
            date_str = ts[:10] if ts else ''
            key = (l.get('student_id'), l.get('subject_id'), date_str)

            if key in existing_map:
                existing = existing_map[key]
                # If existing was absent but new scan shows present, upgrade to present
                if l.get('is_present') and not existing.get('is_present'):
                    supabase.table('attendance_logs') \
                        .update({'is_present': True, 'timestamp': ts}) \
                        .eq('id', existing['id']) \
                        .execute()
                # If already marked present, skip duplicate insertion
                continue
            else:
                to_insert.append(l)

        if to_insert:
            response = supabase.table('attendance_logs').insert(to_insert).execute()
            return response.data
        return existing_logs
    except Exception as e:
        # Fallback to direct insertion if query fails
        response = supabase.table('attendance_logs').insert(logs).execute()
        return response.data


def get_attendance_for_teacher(teacher_id):
    try:
        response = supabase.table('attendance_logs').select("*, subjects!inner(*), students(*)").eq('subjects.teacher_id', teacher_id).execute()
        return response.data or []
    except Exception as e:
        return []

get_attendance_for_hr = get_attendance_for_teacher


def delete_subject(subject_id):
    """
    Deletes a department and cascades deletion to associated attendance_logs
    and subject_students to prevent foreign key constraint violations.
    """
    try:
        # 1. Delete all attendance logs for this department
        supabase.table('attendance_logs').delete().eq('subject_id', subject_id).execute()
        # 2. Delete all student enrollments for this department
        supabase.table('subject_students').delete().eq('subject_id', subject_id).execute()
        # 3. Delete the department itself
        response = supabase.table('subjects').delete().eq('subject_id', subject_id).execute()
        return response.data
    except Exception as e:
        print(f"Failed to delete subject: {e}")
        return None

delete_department = delete_subject


def get_subject_students_with_records(subject_id):
    try:
        enrolled_res = supabase.table('subject_students').select("student_id, students(student_id, name)").eq('subject_id', subject_id).execute()
        enrolled = enrolled_res.data or []

        logs_res = supabase.table('attendance_logs').select("student_id, timestamp, is_present").eq('subject_id', subject_id).execute()
        logs = logs_res.data or []

        # Unique work dates (YYYY-MM-DD)
        unique_dates = sorted(list(set(l['timestamp'][:10] for l in logs if l.get('timestamp'))))
        total_work_days = len(unique_dates)

        # Attended dates per student
        attended_dates_by_student = {}
        for l in logs:
            sid = l['student_id']
            if l.get('is_present') and l.get('timestamp'):
                attended_dates_by_student.setdefault(sid, set()).add(l['timestamp'][:10])

        student_stats = {}
        for item in enrolled:
            st_info = item.get('students') or {}
            sid = item['student_id']
            attended_count = len(attended_dates_by_student.get(sid, set()))
            pct_str = f"{(attended_count / total_work_days * 100):.1f}%" if total_work_days > 0 else "N/A"

            student_stats[sid] = {
                "student_id": sid,
                "name": st_info.get('name', 'Unknown'),
                "total_classes": total_work_days,
                "attended": attended_count,
                "percentage": pct_str
            }

        return list(student_stats.values()), total_work_days
    except Exception as e:
        return [], 0

get_department_employees_with_records = get_subject_students_with_records

