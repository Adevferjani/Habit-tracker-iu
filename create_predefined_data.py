from datetime import datetime, date
from habit_class import Habit
def create_predefined_data():
    """Create predefined test data with 5 habits (1 weekly, 4 daily) and fixed completion patterns
    All habits are created on 1 April 2025."""

    # Clean up all existent data (Mandatory for tests pass)
    Habit.cleanup_data()
    # Create habits
    habits = [
        # Weekly habit (completed every Monday in April 2025)
        {"name": "Weekly_Workout", "description": "Gym session", "periodicity": "weekly","creation_date":"2025-04-01 00:00"},

        # Daily habits with fixed completion patterns
        {"name": "Daily_Reading", "description": "Read 30 minutes", "periodicity": "daily","creation_date":"2025-04-01 09:10"},
        {"name": "Meditation", "description": "Morning meditation", "periodicity": "daily","creation_date":"2025-04-01 10:00"},
        {"name": "Water_Intake", "description": "Drink 2L water", "periodicity": "daily","creation_date":"2025-04-01 11:35"},
        {"name": "Evening_Walk", "description": "30 minute walk", "periodicity": "daily","creation_date":"2025-04-01 12:30"}
    ]

    # Create all habits
    for habit_data in habits:
        habit = Habit(habit_data["name"], habit_data["description"], habit_data["periodicity"],habit_data["creation_date"])
        habit.save_habit()

    # Generate completion dates for April 2025 (1st to 28th)
    april_2025_dates = [date(2025, 4, d) for d in range(1, 29)]
    mondays_april_2025 = [d for d in april_2025_dates if d.weekday() == 0]  # All Mondays

    # Mark weekly habit completions (every Monday at 8:30 AM)
    for monday in mondays_april_2025:
        completion_time = datetime.combine(monday, datetime.strptime("08:30", "%H:%M").time())
        Habit.mark_as_completed("Weekly_Workout", completion_time)

    # Fixed completion patterns for daily habits
    mark_daily_habit_completions("Daily_Reading", april_2025_dates,
                                 pattern="every_day")  # Completed every day
    mark_daily_habit_completions("Meditation", april_2025_dates,
                                 pattern="weekdays_only")  # Only weekdays
    mark_daily_habit_completions("Water_Intake", april_2025_dates,
                                 pattern="every_other_day")  # Every other day starting April 1
    mark_daily_habit_completions("Evening_Walk", april_2025_dates,
                                 pattern="weekends_only")  # Only Saturdays and Sundays

    print("Created predefined test data with:")
    print("- 1 weekly habit (Weekly_Workout) completed every Monday at 8:30 AM")
    print("- 4 daily habits with fixed completion patterns:")
    print("  * Daily_Reading: Completed every day at 9 AM")
    print("  * Meditation: Completed on weekdays at 7:10 AM")
    print("  * Water_Intake: Completed every other day at 12 PM")
    print("  * Evening_Walk: Completed on weekends at 6 PM")
    print("- Data for April 1-28, 2025 (4 weeks)")


def mark_daily_habit_completions(habit_name, date_range, pattern="every_day"):
    """Mark a daily habit as completed with fixed patterns"""
    for i, day in enumerate(date_range):
        if pattern == "every_day":
            mark = True
            time_str = "09:00"
        elif pattern == "weekdays_only":
            mark = day.weekday() < 5  # Monday-Friday
            time_str = "07:10"
        elif pattern == "every_other_day":
            mark = i % 2 == 0  # Even indexes (April 1, 3, 5...)
            time_str = "12:00"
        elif pattern == "weekends_only":
            mark = day.weekday() >= 5  # Saturday-Sunday
            time_str = "18:00"
        else:
            mark = False

        if mark:
            completion_time = datetime.combine(day, datetime.strptime(time_str, "%H:%M").time())
            Habit.mark_as_completed(habit_name, completion_time)





def get_test_habits_info():
    """Return information about the test habits for verification"""
    return {
        "weekly": ["Weekly_Workout"],
        "daily": ["Daily_Reading", "Meditation", "Water_Intake", "Evening_Walk"],
        "patterns": {
            "Weekly_Workout": "every_monday",
            "Daily_Reading": "every_day",
            "Meditation": "weekdays_only",
            "Water_Intake": "every_other_day",
            "Evening_Walk": "weekends_only"
        }
    }


if __name__ == "__main__":
    create_predefined_data()