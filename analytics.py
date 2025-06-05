from collections import defaultdict
from habit_class import Habit
from typing import Tuple, Union, List, Optional
from datetime import date, datetime, timedelta

def compute_current_streak(habit_name: str) -> int:
    """
    Computes the current streak based on completion dates and periodicity
    ->Streak is calculated in days or weeks depending on the habit periodicity.
    Returns:
        int: Current streak length (0 if no active streak)
    """
    completion_dates = Habit.load_completion_dates_and_times(habit_name)
    periodicity = Habit.periodicity_check(habit_name)

    if not completion_dates or not periodicity:
        return 0

    try:
        # Convert to date objects, deduplicate and sort
        unique_dates = sorted({datetime.strptime(d, "%Y-%m-%d").date() for d in completion_dates})
    except (ValueError, TypeError):
        return 0

    if not unique_dates:
        return 0

    periodicity = periodicity.lower()
    today = date.today()
    last_completion = unique_dates[-1]

    if periodicity == 'daily':
        # Check if streak is still active (completed today or yesterday)
        delta = today - last_completion
        if delta.days > 1:  # Streak broken if last completion was more than 1 day ago
            return 0

        # Count backwards through consecutive days
        current_streak = 1
        for i in range(len(unique_dates) - 2, -1, -1):
            if (unique_dates[i + 1] - unique_dates[i]) == timedelta(days=1):
                current_streak += 1
            else:
                break
        return current_streak

    elif periodicity == 'weekly':
        current_year, current_week, _ = today.isocalendar()
        last_year, last_week, _ = last_completion.isocalendar()

        # Check if streak is still active (completed this week or last week)
        if not ((last_year == current_year and last_week >= current_week - 1) or
                (last_year == current_year - 1 and last_week == 52 and current_week == 1)):
            return 0

        # Group dates by ISO week
        weeks = {(d.isocalendar()[0], d.isocalendar()[1]) for d in unique_dates}
        sorted_weeks = sorted(weeks)

        # Count consecutive weeks.
        current_streak = 1
        for i in range(len(sorted_weeks) - 2, -1, -1):
            prev_year, prev_week = sorted_weeks[i]
            next_year, next_week = sorted_weeks[i + 1]

            if ((next_year == prev_year and next_week == prev_week + 1) or
                    (next_year == prev_year + 1 and next_week == 1 and prev_week == 52)):
                current_streak += 1
            else:
                break
        return current_streak

    else:
        raise ValueError("Periodicity must be 'daily' or 'weekly'.")


def compute_longest_streak(habit_name: str) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Computes the longest consecutive streak with start/end dates.
    if many streaks are equal and are the longest it picks the first
    Returns:
        Tuple: (streak_length, start_date, end_date)
    """
    completion_dates = Habit.load_completion_dates_and_times(habit_name)
    periodicity = Habit.periodicity_check(habit_name)

    if not completion_dates or not periodicity:
        return 0, None, None

    try:
        unique_dates = sorted({datetime.strptime(d, "%Y-%m-%d").date() for d in completion_dates})
    except (ValueError, TypeError):
        return 0, None, None

    if not unique_dates:
        return 0, None, None

    periodicity = periodicity.lower()

    if periodicity == 'daily':
        length, start, end = _daily_longest_streak(unique_dates)
    elif periodicity == 'weekly':
        length, start, end = _weekly_longest_streak(unique_dates)
    else:
        raise ValueError("Invalid periodicity")

    return (
        length,
        start.isoformat() if start else None,
        end.isoformat() if end else None
    )


def _daily_longest_streak(dates: List[date]) -> Tuple[int, Optional[date], Optional[date]]:

    if not dates:
        return 0, None, None

    max_length = 1
    current_length = 1
    max_start = dates[0]
    max_end = dates[0]

    for i in range(1, len(dates)):
        if dates[i] - dates[i - 1] == timedelta(days=1):
            current_length += 1
            if current_length > max_length:
                max_length = current_length
                max_start = dates[i - current_length + 1]
                max_end = dates[i]
        else:
            current_length = 1

    return max_length, max_start, max_end


def _weekly_longest_streak(dates: List[date]) -> Tuple[int, Optional[date], Optional[date]]:
    # Group dates by ISO week
    dates_by_week = defaultdict(list)
    for d in dates:
        year, week, _ = d.isocalendar()
        dates_by_week[(year, week)].append(d)

    sorted_weeks = sorted(dates_by_week.keys())
    if not sorted_weeks:
        return 0, None, None

    # Find longest consecutive week streak
    max_length = 1
    current_length = 1
    max_start_idx = 0
    max_end_idx = 0

    for i in range(1, len(sorted_weeks)):
        prev_year, prev_week = sorted_weeks[i-1]
        curr_year, curr_week = sorted_weeks[i]

        # Check if weeks are consecutive (including year transitions)
        if ((curr_year == prev_year and curr_week == prev_week + 1) or
                (curr_year == prev_year + 1 and curr_week == 1 and prev_week == 52)):
            current_length += 1
            if current_length > max_length:
                max_length = current_length
                max_start_idx = i - current_length + 1
                max_end_idx = i
        else:
            current_length = 1

    # Get all dates in the streak weeks
    all_streak_dates = []
    for i in range(max_start_idx, max_end_idx + 1):
        week = sorted_weeks[i]
        all_streak_dates.extend(dates_by_week.get(week, []))

    if not all_streak_dates:
        return 0, None, None

    return (
        max_length,
        min(all_streak_dates),
        max(all_streak_dates)
    )


def count_missed_periods(habit_name: str) -> int:
    """Returns the total number of missed periods (days/weeks) for a habit."""
    return len(get_missed_periods(habit_name))


def get_missed_periods(habit_name: str) -> List[Union[str, Tuple[str, str]]]:
    """
    Returns missed periods (days or weeks) for a habit.

    Returns:
        For daily habits: List of dates in 'YYYY-MM-DD' format
        For weekly habits: List of tuples (week_start, week_end) in 'YYYY-MM-DD' format
    """
    periodicity = Habit.periodicity_check(habit_name)
    creation_date = Habit.get_creation_date(habit_name)
    completion_dates = Habit.load_completion_dates_and_times(habit_name)

    if not periodicity or not creation_date:
        return []

    today = date.today()
    if creation_date > today:
        return []

    try:
        unique_dates = {datetime.strptime(d, "%Y-%m-%d").date() for d in completion_dates}
    except (ValueError, TypeError):
        unique_dates = set()

    missed = []
    periodicity = periodicity.lower()

    if periodicity == 'daily':
        current_date = creation_date
        while current_date <= today:
            if current_date not in unique_dates:
                missed.append(current_date.isoformat())
            current_date += timedelta(days=1)

    elif periodicity == 'weekly':
        # Get all completed weeks
        completed_weeks = {(d.isocalendar()[0], d.isocalendar()[1]) for d in unique_dates}

        # Start from the beginning of the creation week
        creation_year, creation_week, _ = creation_date.isocalendar()
        current_week_start = date.fromisocalendar(creation_year, creation_week, 1)

        while current_week_start <= today:
            year, week, _ = current_week_start.isocalendar()
            week_end = current_week_start + timedelta(days=6)

            if (year, week) not in completed_weeks:
                missed.append((current_week_start.isoformat(), week_end.isoformat()))

            current_week_start += timedelta(weeks=1)

    else:
        raise ValueError("Periodicity must be 'daily' or 'weekly'.")

    return missed


def determine_most_challenging_habit() -> str:
    """
    Determines the habit with the lowest completion ratio:
    (number of completion periods / total periods since creation).

    Returns:
        str: Description of the most challenging habit.
    """
    habits = Habit.load_habits()
    if not habits:
        return "No Habits Found."


    today = date.today()
    habit_stats = []

    for habit in habits:
        if not Habit.habit_exists(habit):
            continue

        periodicity = Habit.periodicity_check(habit)
        if not periodicity:
            continue

        creation_date = Habit.get_creation_date(habit)
        if not creation_date or creation_date > today:
            continue

        try:
            completion_dates = {
                datetime.strptime(d, "%Y-%m-%d").date()
                for d in Habit.load_completion_dates_and_times(habit)
            }
        except Exception:
            completion_dates = set()

        if periodicity.lower() == 'daily':
            total_periods = (today - creation_date).days + 1
            completed = len([d for d in completion_dates if creation_date <= d <= today])

        elif periodicity.lower() == 'weekly':
            # Start from start of the creation week
            start_week = creation_date - timedelta(days=creation_date.weekday())
            total_periods = ((today - start_week).days // 7) + 1

            week_starts = [start_week + timedelta(weeks=i) for i in range(total_periods)]
            completed = sum(
                1 for ws in week_starts
                if any(ws <= d <= ws + timedelta(days=6) for d in completion_dates)
            )
        else:
            continue

        ratio = completed / total_periods if total_periods > 0 else 0

        habit_stats.append({
            'name': habit,
            'periodicity': periodicity.lower(),
            'total': total_periods,
            'completed': completed,
            'ratio': ratio
        })

    if not habit_stats:
        return "No valid habits to analyze."

    # Find habit with the lowest completion ratio
    habit_stats.sort(key=lambda h: h['ratio'])
    worst = habit_stats[0]

    # if all habits have been completed every day since creation
    if worst['ratio'] == 1:
        return "You didn't struggle with any habit, all habits have 100% completion ratio."

    unit = 'day' if worst['periodicity'] == 'daily' else 'week'
    return (
        f"Most challenging habit: '{worst['name']}'\n"
        f"- Periodicity: {worst['periodicity']}\n"
        f"- Completed: {worst['completed']} out of {worst['total']} {unit}s since habit creation\n"
        f"- Completion ratio: {worst['ratio']:.1%}"
    )


def get_longest_streaks_by_periodicity(formatted: bool = False) -> Union[
    Tuple[Optional[Tuple[str, int, str, str]], Optional[Tuple[str, int, str, str]]],
    str
]:
    """
    Returns the longest streaks among all daily habits and all weekly habits.
    """
    habits = Habit.load_habits()
    if not habits:
        return "No Habits Found." if formatted else (None, None)

    longest_daily = (None, 0, None, None)
    longest_weekly = (None, 0, None, None)

    for habit in habits:
        if not Habit.habit_exists(habit):
            continue

        periodicity = Habit.periodicity_check(habit)
        if not periodicity:
            continue

        try:
            streak_length, start_date, end_date = compute_longest_streak(habit)
            if not streak_length:
                continue

            if periodicity.lower() == 'daily':
                if streak_length > longest_daily[1]:
                    longest_daily = (habit, streak_length, start_date, end_date)
            elif periodicity.lower() == 'weekly':
                if streak_length > longest_weekly[1]:
                    longest_weekly = (habit, streak_length, start_date, end_date)
        except Exception as e:
            print(f"Error processing habit {habit}: {str(e)}")
            continue

    if not formatted:
        return (
            longest_daily if longest_daily[0] else None,
            longest_weekly if longest_weekly[0] else None
        )
    else:
        output = []

        if longest_daily[0]:
            habit, length, start, end = longest_daily
            output.append(
                f"Longest daily streak: '{habit}' with {length} days "
                f"({start} to {end})"
            )
        else:
            output.append("No daily habits with streaks found.")

        if longest_weekly[0]:
            habit, length, start, end = longest_weekly
            output.append(
                f"Longest weekly streak: '{habit}' with {length} weeks "
                f"({start} to {end})"
            )
        else:
            output.append("No weekly habits with streaks found.")

        return "\n".join(output)