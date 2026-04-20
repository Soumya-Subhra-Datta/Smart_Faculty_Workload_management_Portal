"""
AI-Based Substitution Engine
==============================
Implements intelligent faculty substitution assignment using a scoring system:
  1. Subject Expertise:   +10 points (faculty can teach the same subject)
  2. Availability:        Required (no timetable/duty/substitution clashes)
  3. Workload Balancing:  +5 points (inversely weighted by current assignments)
  4. Department Match:    +3 points (same department as original faculty)
  5. Fallback:            +1 point  (any available faculty)
"""
import json
from datetime import datetime
from models.db import execute_query
from models import timetable as timetable_model
from models import event as event_model
from models import substitution as sub_model


def find_substitute(original_faculty_id, subject, date, start_time, end_time, classroom):
    """
    Find the best substitute faculty member using AI priority logic.
    
    Args:
        original_faculty_id: ID of the faculty being replaced
        subject: Subject that needs substitution
        date: Date of the duty (YYYY-MM-DD string)
        start_time: Start time string (HH:MM:SS)
        end_time: End time string (HH:MM:SS)
        classroom: Classroom for the substitution
    
    Returns:
        dict with 'substitute' (best candidate) and 'candidates' (ranked list)
        or None if no candidate found
    """
    # Get the original faculty's department
    original = execute_query(
        "SELECT department FROM users WHERE id = %s", (original_faculty_id,), fetch_one=True
    )
    original_dept = original['department'] if original else None

    # Get the day of week from the date
    date_obj = datetime.strptime(str(date), '%Y-%m-%d')
    day_of_week = date_obj.strftime('%A')

    # Get all faculty except the original one and admins
    all_faculty = execute_query(
        "SELECT id, full_name, department, subjects FROM users WHERE role = 'faculty' AND id != %s",
        (original_faculty_id,), fetch_all=True
    )

    candidates = []
    rejected_faculty = []

    for faculty in all_faculty:
        rejection_reason = None

        # Parse subjects
        subjects = faculty.get('subjects', '[]')
        if isinstance(subjects, str):
            subjects = json.loads(subjects)

        # ── Check 1: Availability (REQUIRED) ──
        # Check timetable clash
        has_timetable_clash = timetable_model.check_timetable_clash(
            faculty['id'], day_of_week, start_time, end_time
        )
        if has_timetable_clash:
            rejection_reason = 'Timetable clash (has lecture)'
        else:
            # Check existing duty clash
            has_duty_clash = event_model.check_duty_clash(
                faculty['id'], date, start_time, end_time
            )
            if has_duty_clash:
                rejection_reason = 'Existing duty clash'
            else:
                # Check existing substitution clash
                has_sub_clash = sub_model.check_substitution_clash(
                    faculty['id'], date, start_time, end_time
                )
                if has_sub_clash:
                    rejection_reason = 'Existing substitution clash'
                else:
                    # Check if the time slot overlaps with break or lunch
                    if _is_time_restricted(start_time, end_time):
                        rejection_reason = 'Time restricted (break/lunch)'

        if rejection_reason:
            rejected_faculty.append({
                'faculty_id': faculty['id'],
                'full_name': faculty['full_name'],
                'department': faculty['department'],
                'reason': rejection_reason
            })
            continue

        # Faculty is available! Calculate score.
        score = 0
        reasons = []
        score += 1  # Base fallback score
        reasons.append('Available')

        # ── Check 2: Subject Expertise (+10) ──
        if subject in subjects:
            score += 10
            reasons.append(f'Subject expert: {subject}')

        # ── Check 3: Department Match (+3) ──
        if original_dept and faculty['department'] == original_dept:
            score += 3
            reasons.append(f'Same department: {faculty["department"]}')

        # ── Check 4: Workload Balancing (+5 inversely weighted) ──
        sub_count = sub_model.get_substitution_count(faculty['id'])
        # Less substitutions = higher score (max 5 for 0 subs, min 0 for 5+ subs)
        workload_score = max(0, 5 - sub_count)
        score += workload_score
        reasons.append(f'Workload score: {workload_score} (current subs: {sub_count})')

        candidates.append({
            'faculty_id': faculty['id'],
            'full_name': faculty['full_name'],
            'department': faculty['department'],
            'subjects': subjects,
            'score': score,
            'reasons': reasons,
            'current_substitutions': sub_count
        })

    # Sort by score (descending), then by substitution count (ascending)
    candidates.sort(key=lambda x: (-x['score'], x['current_substitutions']))

    if not candidates:
        print(f"[Substitution] No substitute found for faculty {original_faculty_id}, subject {subject}, date {date}, time {start_time}-{end_time}. Total faculty: {len(all_faculty)}, rejected: {len(rejected_faculty)}")
        return {
            'substitute': None,
            'candidates': [],
            'total_available': 0,
            'total_faculty': len(all_faculty),
            'rejected_faculty': rejected_faculty
        }

    return {
        'substitute': candidates[0],
        'candidates': candidates[:5],  # Return top 5 candidates
        'total_available': len(candidates),
        'total_faculty': len(all_faculty),
        'rejected_faculty': rejected_faculty
    }


def auto_assign_substitute(event_id, original_faculty_id, date, start_time, end_time):
    """
    Automatically find and assign a substitute for a duty assignment.
    
    Looks at the original faculty's timetable to find classes that need coverage
    during the duty period, then finds substitutes for each class.
    
    Returns list of created substitution records.
    """
    # Get the day of week
    date_obj = datetime.strptime(str(date), '%Y-%m-%d')
    day_of_week = date_obj.strftime('%A')

    # Find the original faculty's classes during the duty time
    classes = timetable_model.get_faculty_classes_at_time(
        original_faculty_id, day_of_week, start_time, end_time
    )
    print(f"[Substitution] Found {len(classes)} classes for faculty {original_faculty_id} at {start_time}-{end_time} on {day_of_week}")

    substitutions_created = []

    if not classes:
        print("[Substitution] No classes to substitute - faculty was free during this slot")
        return substitutions_created

    for cls in classes:
        result = find_substitute(
            original_faculty_id=original_faculty_id,
            subject=cls['subject'],
            date=date,
            start_time=str(cls['start_time']),
            end_time=str(cls['end_time']),
            classroom=cls['classroom']
        )

        if result and result['substitute']:
            sub_data = {
                'event_id': event_id,
                'original_faculty_id': original_faculty_id,
                'substitute_faculty_id': result['substitute']['faculty_id'],
                'subject': cls['subject'],
                'classroom': cls['classroom'],
                'date': date,
                'start_time': str(cls['start_time']),
                'end_time': str(cls['end_time']),
                'reason': f"Duty assignment: Event #{event_id}"
            }
            sub_id = sub_model.create_substitution(sub_data)
            sub_data['id'] = sub_id
            sub_data['substitute_name'] = result['substitute']['full_name']
            sub_data['candidates'] = result['candidates']
            substitutions_created.append(sub_data)
        else:
            print(f"[Substitution] No substitute found for class {cls['subject']} in {cls['classroom']} at {cls['start_time']}-{cls['end_time']}")

    return substitutions_created


def _time_to_minutes(time_str):
    """Convert a time string (HH:MM:SS or HH:MM) to total minutes."""
    time_str = str(time_str)
    parts = time_str.split(':')
    return int(parts[0]) * 60 + int(parts[1])


def _is_time_restricted(start_time, end_time):
    """Check if the time slot overlaps with break or lunch periods."""
    start_minutes = _time_to_minutes(start_time)
    end_minutes = _time_to_minutes(end_time)
    
    # Break: 11:00 - 11:15 (official)
    break_start = 11 * 60
    break_end = 11 * 60 + 15
    if start_minutes < break_end and end_minutes > break_start:
        return True
    
    # Lunch: 11:15 - 12:15 (official)
    lunch_start = 11 * 60 + 15
    lunch_end = 12 * 60 + 15
    if start_minutes < lunch_end and end_minutes > lunch_start:
        return True
    
    return False
