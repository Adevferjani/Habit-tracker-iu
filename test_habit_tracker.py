import pytest
from habit_class import Habit
from analytics import (
    compute_current_streak,
    compute_longest_streak,
    count_missed_periods,
    determine_most_struggled_habit,
    get_longest_streaks_by_periodicity
)
from create_predefined_data import create_predefined_data
from datetime import datetime
from freezegun import freeze_time
import os
import sqlite3



# Pytest fixture to set up data, the data is not deleted after the tests
@pytest.fixture(scope="module")
def test_data():
    """Fixture to clean up and create test data"""
    # Freeze time to 28-04-2025 for all tests
    with freeze_time("2025-04-28"):
        create_predefined_data()


@pytest.fixture(autouse=True)
def set_fixed_date():
    """Automatically mock datetime to 28-04-2025 for all tests"""
    with freeze_time("2025-04-28"):
        yield


def test_habit_creation(test_data):
    """Test that habits are created correctly"""
    habits = Habit.load_habits()
    assert len(habits) == 5
    assert "Weekly_Workout" in habits
    assert "Daily_Reading" in habits

    # Verify one habit's details
    conn = sqlite3.connect('habits.db')
    cur = conn.cursor()
    cur.execute("SELECT description, periodicity FROM habits_table WHERE name='Daily_Reading'")
    result = cur.fetchone()
    conn.close()
    assert result[0] == "Read 30 minutes"
    assert result[1].lower() == "daily"


def test_mark_as_completed(test_data):
    """Test marking habits as completed"""
    # Check completion dates for Weekly_Workout (should be all Mondays in April 2025)
    dates = Habit.load_completion_dates("Weekly_Workout")
    assert len(dates) == 4  # 4 Mondays in April 1-28
    assert all(date_str.startswith("2025-04-") for date_str in dates)

    # Check Daily_Reading was marked every day
    dates = Habit.load_completion_dates("Daily_Reading")
    assert len(dates) == 28  # April 1-28


def test_current_streak_calculation(test_data):
    """Test current streak calculation with fixed date (April 28, 2025)"""
    # Weekly_Workout was last completed on April 28 (Monday)
    streak = compute_current_streak("Weekly_Workout")
    assert streak == 4  # 4 consecutive Mondays in April

    # Daily_Reading was completed every day - streak should be 28 days
    streak = compute_current_streak("Daily_Reading")
    assert streak == 28

    # Meditation was completed only on weekdays - last completion was April 25 (Friday)
    # On April 28 (Monday), streak should be 1 (just the Monday)
    streak = compute_current_streak("Meditation")
    assert streak == 1



def test_longest_streak_calculation(test_data):
    """Test longest streak calculation"""
    # Daily_Reading was completed every day - longest streak is 28 days
    length, start, end = compute_longest_streak("Daily_Reading")
    assert length == 28
    assert start == "2025-04-01"
    assert end == "2025-04-28"

    # Weekly_Workout was completed every Monday - longest streak is 4 weeks
    length, start, end = compute_longest_streak("Weekly_Workout")
    assert length == 4
    assert start == "2025-04-07"  # First Monday
    assert end == "2025-04-28"  # Last Monday

    # Meditation - longest streak is 5 days (Mon-Fri weekdays)-> first 5 days streak
    length, start, end = compute_longest_streak("Meditation")
    assert length == 5
    assert start == "2025-04-07"  # Monday
    assert end == "2025-04-11"  # Friday


def test_missed_periods(test_data):
    """Test missed periods calculation with fixed date"""
    # Daily_Reading has no missed days
    missed = count_missed_periods("Daily_Reading")
    assert missed == 0

    # Meditation was only completed on weekdays (20 weekdays in April 1-28)
    missed = count_missed_periods("Meditation")
    assert missed == 8  # 8 weekend days

    # Weekly_Workout was completed every Monday - missed first week of april because it has no mondays
    missed = count_missed_periods("Weekly_Workout")
    assert missed == 1

    # Water_Intake - completed every other day (14 days)
    missed = count_missed_periods("Water_Intake")
    assert missed == 14  # 14 days missed

    # Evening_Walk - completed only on weekends (8 days)
    missed = count_missed_periods("Evening_Walk")
    assert missed == 20  # 20 weekdays missed


def test_most_struggled_habit(test_data):
    """Test determination of most struggled habit"""
    result = determine_most_struggled_habit()
    # Evening_Walk should be the most struggled (only completed on 8/28 days)
    assert "Evening_Walk" in result
    assert "8 out of 28" in result  # 8 weekend days in April 1-28
    assert "28.6%" in result  # Completion ratio


def test_longest_streaks_by_periodicity(test_data):
    """Test getting the longest streaks by periodicity"""
    daily, weekly = get_longest_streaks_by_periodicity(formatted=False)

    # Daily_Reading has the longest daily streak (28 days)
    assert daily[0] == "Daily_Reading"
    assert daily[1] == 28

    # Weekly_Workout has the longest weekly streak (4 weeks)
    assert weekly[0] == "Weekly_Workout"
    assert weekly[1] == 4


def test_habit_deletion(test_data):
    """Test habit deletion functionality"""
    # Create a temporary habit to delete
    temp_habit = Habit("Temp_Habit", "Test deletion", "daily")
    temp_habit.save_habit()
    Habit.mark_as_completed("Temp_Habit")

    # Verify it exists
    assert "Temp_Habit" in Habit.load_habits()
    assert len(Habit.load_completion_dates("Temp_Habit")) == 1

    # Delete it
    Habit.delete_habit("Temp_Habit")

    # Verify deletion
    assert "Temp_Habit" not in Habit.load_habits()
    assert not os.path.exists("Temp_Habit_track_data.db")


def test_clear_habit_history(test_data):
    """Test clearing habit history"""
    # Verify Water_Intake has completion dates
    dates = Habit.load_completion_dates("Water_Intake")
    assert len(dates) > 0

    # Clear history
    Habit.clear_habit_history("Water_Intake")

    # Verify cleared
    dates = Habit.load_completion_dates("Water_Intake")
    assert len(dates) == 0


def test_habit_periodicity_check(test_data):
    """Test periodicity check"""
    assert Habit.periodicity_check("Weekly_Workout") == "weekly"
    assert Habit.periodicity_check("Daily_Reading") == "daily"


def test_habit_creation_date(test_data):
    """Test getting habit creation date"""
    creation_date = Habit.get_creation_date("Weekly_Workout")
    assert creation_date == datetime.strptime("2025-04-01", "%Y-%m-%d").date()


def test_habit_exists(test_data):
    """Test habit existence check"""
    assert Habit.habit_exists("Weekly_Workout")
    assert not Habit.habit_exists("Non_Existent_Habit")


