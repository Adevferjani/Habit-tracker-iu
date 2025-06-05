import datetime
import sqlite3
import os
import json
from typing import List, Optional

# Create data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


class Habit:
    def __init__(self, name: str, description: str, periodicity: str,
                 creation_date=datetime.datetime.today().strftime("%Y-%m-%d %H:%M")):
        self.name = name
        self.description = description
        self.periodicity = periodicity.lower()
        self.creation_date = str(creation_date)

    def save_habit(self) -> None:
        """Save habit to database and update habits list"""
        # Define file paths
        habits_db = os.path.join(DATA_DIR, 'habits.db')
        track_db = os.path.join(DATA_DIR, f'{self.name}_track_data.db')
        habits_list = os.path.join(DATA_DIR, 'habits_list.json')

        # Save to SQLite database
        conn = sqlite3.connect(habits_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits_table (
                name TEXT UNIQUE, 
                description TEXT, 
                periodicity TEXT, 
                creation_date TEXT
            )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO habits_table VALUES (?,?,?,?)",
            (self.name, self.description, self.periodicity, self.creation_date)
        )
        conn.commit()
        conn.close()

        # Create tracking database
        con = sqlite3.connect(track_db)
        cursor = con.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_completion_dates (
                date TEXT UNIQUE, 
                time TEXT
            )
        """)
        con.close()

        # Update JSON habits list
        habit_names = []
        if os.path.exists(habits_list):
            with open(habits_list, 'r') as f:
                try:
                    habit_names = json.load(f)
                except json.JSONDecodeError:
                    habit_names = []

        if self.name not in habit_names:
            habit_names.append(self.name)
            with open(habits_list, 'w') as f:
                json.dump(habit_names, f, indent=2)

        print(f"Habit {self.name} saved successfully.")

    @staticmethod
    def mark_as_completed(habit_name: str, date_time: datetime.datetime = None) -> None:
        """
        Marks the habit as completed at the specified date and time.

        Adds the completion date to the tracking data only once per defined periodicity (e.g., daily, weekly).
        Subsequent completions within the same period are ignored.
        """

        if date_time is None:
            date_time = datetime.datetime.now()

        track_db = os.path.join(DATA_DIR, f'{habit_name}_track_data.db')
        con = sqlite3.connect(track_db)
        cursor = con.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habit_completion_dates (
                date TEXT UNIQUE, 
                time TEXT
            )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO habit_completion_dates VALUES (?,?)",
            (str(date_time.date()), str(date_time.time().strftime("%H:%M"))))
        con.commit()
        print(f"Habit {habit_name} marked as completed on {date_time.date()} at {date_time.time().strftime('%H:%M')}.")
        con.close()


    @staticmethod
    def periodicity_check(habit_name: str) -> Optional[str]:
        """Get periodicity of a habit"""
        try:
            habits_db = os.path.join(DATA_DIR, 'habits.db')
            con = sqlite3.connect(habits_db)
            cur = con.cursor()
            cur.execute("SELECT periodicity FROM habits_table WHERE name=?", (habit_name,))
            result = cur.fetchone()
            con.close()
            return result[0].lower() if result else None
        except sqlite3.OperationalError:
            return None

    @staticmethod
    def delete_habit(habit_name: str) -> None:
        """Delete a habit and its tracking data"""
        # Define file paths
        habits_db = os.path.join(DATA_DIR, 'habits.db')
        track_db = os.path.join(DATA_DIR, f'{habit_name}_track_data.db')
        habits_list = os.path.join(DATA_DIR, 'habits_list.json')

        # Delete from main database
        con = sqlite3.connect(habits_db)
        cur = con.cursor()
        cur.execute("DELETE FROM habits_table WHERE name=?", (habit_name,))
        con.commit()
        con.close()

        # Delete tracking database
        if os.path.exists(track_db):
            os.remove(track_db)

        # Update JSON habits list
        if os.path.exists(habits_list):
            with open(habits_list, 'r') as f:
                try:
                    habit_names = json.load(f)
                except json.JSONDecodeError:
                    habit_names = []

            if habit_name in habit_names:
                habit_names.remove(habit_name)
                with open(habits_list, 'w') as f:
                    json.dump(habit_names, f, indent=2)

        print("Habit deleted successfully.")

    @staticmethod
    def get_creation_date(habit_name: str) -> Optional[datetime.date]:
        """Get creation date of a habit"""
        try:
            habits_db = os.path.join(DATA_DIR, 'habits.db')
            conn = sqlite3.connect(habits_db)
            cur = conn.cursor()
            cur.execute("SELECT creation_date FROM habits_table WHERE name=?", (habit_name,))
            result = cur.fetchone()
            conn.close()
            if result:
                return datetime.datetime.strptime(result[0], "%Y-%m-%d %H:%M").date()
            return None
        except sqlite3.OperationalError:
            return None

    @staticmethod
    def clear_habit_history(habit_name: str) -> None:
        """Clear completion history for a habit"""
        try:
            track_db = os.path.join(DATA_DIR, f'{habit_name}_track_data.db')
            con = sqlite3.connect(track_db)
            cur = con.cursor()
            cur.execute("DELETE FROM habit_completion_dates")
            con.commit()
            print("Habit history cleared successfully.")
            con.close()
        except sqlite3.OperationalError:
            print("No tracking data found for this habit.")

    @staticmethod
    def load_habits() -> List[str]:
        """Load all habits names from the habits_list json file"""
        habits_list = os.path.join(DATA_DIR, 'habits_list.json')
        try:
            with open(habits_list, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    @staticmethod
    def load_completion_dates_and_times(habit_name: str, time: bool = False) -> List[str]:
        """Load all completion dates and times or only dates for a habit"""
        try:
            track_db = os.path.join(DATA_DIR, f'{habit_name}_track_data.db')
            con = sqlite3.connect(track_db)
            cur = con.cursor()
            cur.execute("SELECT date, time FROM habit_completion_dates ORDER BY date ASC")
            if time:  # return the dates and times
                dates = [row[0] + " " + row[1] for row in cur.fetchall()]
            else:  # return only the dates
                dates = [row[0] for row in cur.fetchall()]
            con.close()
            return dates
        except sqlite3.OperationalError:
            return []

    @staticmethod
    def habit_exists(habit_name: str) -> bool:
        """Check if habit exists in database"""
        try:
            habits_db = os.path.join(DATA_DIR, 'habits.db')
            conn = sqlite3.connect(habits_db)
            cur = conn.cursor()

            # Check if table exists
            cur.execute("""
                SELECT name 
                FROM sqlite_master 
                WHERE type='table' AND name='habits_table';
            """)
            if not cur.fetchone():
                conn.close()
                return False

            # Check if habit exists
            cur.execute("SELECT name FROM habits_table WHERE LOWER(name)=LOWER(?)", (habit_name,))
            result = cur.fetchone()
            conn.close()
            return result is not None
        except sqlite3.OperationalError:
            return False

    @classmethod
    def cleanup_data(cls) -> None:
        """Clean up all existing habits and their tracking data"""
        try:
            habits_list = os.path.join(DATA_DIR, 'habits_list.json')
            if os.path.exists(habits_list):
                with open(habits_list, "r") as f:
                    habits = json.load(f)

                # Delete each habit using the Habit class
                for habit in habits:
                    if cls.habit_exists(habit):
                        cls.delete_habit(habit)

                # Clear the JSON file by writing an empty list
                with open(habits_list, "w") as f:
                    json.dump([], f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass