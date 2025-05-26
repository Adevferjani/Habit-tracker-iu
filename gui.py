import tkinter as tk
from tkinter import messagebox, ttk
from habit_class import Habit
import analytics
from typing import List, Optional
import sqlite3
from quote_class import Quote


class HabitTrackerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Habit Tracker GUI")
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the main user interface"""
        # Header
        header = ttk.Label(
            self.root,
            text="Habit Tracker",
            font=("Arial", 16, "bold")
        )
        header.pack(pady=15)

        # Menu buttons
        menu_items = [
            ("Add New Habit", self.create_habit),
            ("Mark Habit as Completed", self.mark_completed),
            ("View All Habits", self.view_all_habits),
            ("View Daily Habits", lambda: self.view_habits_by_periodicity("daily")),
            ("View Weekly Habits", lambda: self.view_habits_by_periodicity("weekly")),
            ("View Habit Details (Data and Analytics)", self.analyse_habit),
            ("Delete a Habit", self.delete_habit),
            ("Delete all Habits",self.delete_all_habits),
            ("Clear Habit Tracking Data", self.clear_habit_data),
            ("View Longest Streak Across All Habits", self.view_longest_streaks),
            ("View Most Challenging Habit", self.view_most_struggled),
            ("Boost Zone", self.manage_quotes),
            ("Exit Application", self.root.destroy)
        ]

        for text, command in menu_items:
            tk.Button(
                self.root,
                text=text,
                command=command,
                width=40
            ).pack(pady=5)

    @staticmethod
    def refresh_habit_list() -> List[str]:
        """Load and return current habits"""
        try:
            return Habit.load_habits()
        except FileNotFoundError:
            return []

    def create_habit(self) -> None:
        """Create habit dialog"""
        window = tk.Toplevel(self.root)
        window.title("Create a New Habit")

        # Name entry
        tk.Label(window, text="Habit Name:").pack(pady=(10, 0))
        name_entry = tk.Entry(window)
        name_entry.pack(pady=5)

        # Description entry
        tk.Label(window, text="Description:").pack(pady=(10, 0))
        description_entry = tk.Entry(window)
        description_entry.pack(pady=5)

        # Periodicity selection
        tk.Label(window, text="Periodicity:").pack(pady=(10, 0))
        periodicity_var = tk.StringVar(value="daily")
        periodicity_menu = ttk.Combobox(
            window,
            textvariable=periodicity_var,
            values=["daily", "weekly"],
            state="readonly"
        )
        periodicity_menu.pack(pady=5)

        def submit() -> None:
            name = name_entry.get().strip()
            description = description_entry.get().strip()
            periodicity = periodicity_var.get()

            if not name or not description:
                messagebox.showerror("Error", "All fields are required.")
                return

            if Habit.habit_exists(name):
                messagebox.showerror("Error", f"A habit named '{name}' already exists.")
                return

            habit = Habit(name, description, periodicity)
            habit.save_habit()
            messagebox.showinfo("Success", f"Habit '{name}' created.")
            window.destroy()

        tk.Button(window, text="Create Habit", command=submit).pack(pady=10)

    def mark_completed(self) -> None:
        """Mark habit as completed"""
        habits = self.refresh_habit_list()
        if not habits:
            messagebox.showinfo("Info", "No Habits yet. Create a Habit first.")
            return

        habit = self.select_habit(habits)
        if habit:
            Habit.mark_as_completed(habit)
            messagebox.showinfo("Success", f"Habit '{habit}' marked as completed.")

    def view_all_habits(self) -> None:
        """Show all habits"""
        habits = self.refresh_habit_list()
        if not habits:
            messagebox.showinfo("Info", "No Habits Yet, Create One First.")
        else:
            messagebox.showinfo("Habits", "\n".join(habits))

    def view_habits_by_periodicity(self, target: str) -> None:
        """Show habits by periodicity"""
        habits = self.refresh_habit_list()
        filtered = [h for h in habits if Habit.periodicity_check(h) == target]

        if not filtered:
            messagebox.showinfo("Info", f"No {target} Habits.")
        else:
            messagebox.showinfo(f"{target.title()} Habits", "\n".join(filtered))

    def select_habit(self, habits: List[str]) -> Optional[str]:
        """Dialog to select a habit"""
        if not habits:
            return None

        selection = tk.Toplevel(self.root)
        selection.title("Select a Habit")

        var = tk.StringVar(value=habits[0])
        dropdown = ttk.Combobox(
            selection,
            textvariable=var,
            values=habits,
            state="readonly"
        )
        dropdown.pack(pady=10)

        def submit() -> None:
            selection.habit = var.get()
            selection.destroy()

        tk.Button(selection, text="OK", command=submit).pack(pady=10)
        selection.wait_window()
        return getattr(selection, 'habit', None)

    def delete_habit(self) -> None:
        """Delete habit dialog"""
        habits = self.refresh_habit_list()
        habit = self.select_habit(habits)
        if not habits:
            messagebox.showinfo("Info", "No Habits Found.")
        if habit:
            if messagebox.askyesno(
                    "Confirm",
                    f"Are you sure you want to delete '{habit}'?"
            ):
                Habit.delete_habit(habit)
                messagebox.showinfo("Deleted", f"Habit '{habit}' deleted.")

    def clear_habit_data(self) -> None:
        """Clear habit data dialog"""
        habits = self.refresh_habit_list()
        habit = self.select_habit(habits)
        if not habits:
            messagebox.showinfo("Info", "No Habits Found.")
        if habit:
            if messagebox.askyesno(
                    "Confirm",
                    f"Are you sure you want to clear all data for '{habit}'?"
            ):
                Habit.clear_habit_history(habit)
                messagebox.showinfo("Cleared", f"Data for '{habit}' cleared.")

    @staticmethod
    def view_most_struggled() -> None:
        """Show most struggled habit"""
        result = analytics.determine_most_challenging_habit()
        messagebox.showinfo("Most Struggled Habit", result)

    @staticmethod
    def view_longest_streaks() -> None:
        """Show the longest streaks"""

        result = analytics.get_longest_streaks_by_periodicity(formatted=True)
        messagebox.showinfo("Longest Streaks", result)

    def analyse_habit(self) -> None:
        """Analyze habit dialog"""
        habits = self.refresh_habit_list()
        habit = self.select_habit(habits)

        if not habits:
            messagebox.showinfo("Info", "No Habits Found.")

        if not habit:
            return

        periodicity = Habit.periodicity_check(habit)
        if not periodicity and habit is not None:
            messagebox.showerror("Error", "Could not determine habit periodicity.")


        period_block = "days" if periodicity == "daily" else "weeks"
        analysis_options = [
            "View Habit Info",
            "View Current Streak",
            "View Longest Streak",
            "View Current And Longest Streak",
            "View Completion Dates",
            "View Missed Periods"
        ]

        selected = self.select_analysis_option(analysis_options)
        if not selected:
            return

        if selected == "View Habit Info":
            self.view_habit_info(habit)
        elif selected == "View Current Streak":
            self.view_current_streak(habit, period_block)
        elif selected == "View Longest Streak":
            self.view_longest_streak(habit, period_block)
        elif selected ==  "View Current And Longest Streak":
            self.view_both_streaks(habit, period_block)
        elif selected ==  "View Completion Dates":
            self.view_completion_dates(habit)
        elif selected == "View Missed Periods":
            self.view_missed_periods(habit)

    def select_analysis_option(self, options: List[str]) -> Optional[str]:
        """Dialog to select analysis option"""
        selection = tk.Toplevel(self.root)
        selection.title("Select Analysis")

        var = tk.StringVar(value=options[0])
        dropdown = ttk.Combobox(
            selection,
            textvariable=var,
            values=options,
            state="readonly"
        )
        dropdown.pack(pady=10)

        def submit() -> None:
            selection.choice = var.get()
            selection.destroy()

        tk.Button(selection, text="OK", command=submit).pack(pady=10)
        selection.wait_window()
        return getattr(selection, 'choice', None)

    @staticmethod
    def view_habit_info(habit: str) -> None:
        """Show habit information(description, periodicity, creation date"""
        try:
            conn = sqlite3.connect('habits.db')
            cur = conn.cursor()
            cur.execute("""
                SELECT description, periodicity, creation_date 
                FROM habits_table 
                WHERE name=?
            """, (habit,))
            result = cur.fetchone()
            conn.close()

            if result:
                messagebox.showinfo(
                    "Habit info",
                    f"Description: {result[0]}\n"
                    f"Periodicity: {result[1]}\n"
                    f"Creation Date: {result[2]}"
                )
            else:
                messagebox.showerror("Error", "Habit not found.")
        except sqlite3.Error:
            messagebox.showerror("Error", "Could not access habit data.")

    @staticmethod
    def view_current_streak( habit: str, period_block: str) -> None:
        """Show current streak"""
        streak = analytics.compute_current_streak(habit)
        messagebox.showinfo(
            "Current Streak",
            f"The current streak is: {streak} {period_block}."
        )
    @staticmethod
    def view_longest_streak( habit: str, period_block: str) -> None:
        """Show the longest streak for a habit
        if many streaks are equal and are the longest it returns the first"""
        length, start, end = analytics.compute_longest_streak(habit)
        messagebox.showinfo(
            "Longest Streak",
            f"The longest streak is: {length} {period_block}.\n"
            f"Started: {start}\nEnded: {end}."
        )

    @staticmethod
    def view_both_streaks(habit: str, period_block: str) -> None:
        """Show both current and longest streaks"""
        current = analytics.compute_current_streak(habit)
        length, start, end = analytics.compute_longest_streak(habit)
        messagebox.showinfo(
            "Streaks",
            f"Current streak: {current} {period_block}.\n"
            f"Longest streak: {length} {period_block}.\n"
            f"Started: {start}\nEnded: {end}."
        )


    @staticmethod
    def view_completion_dates(habit: str) -> None:
        """Show completion dates for a habit"""
        dates = Habit.load_completion_dates_and_times(habit,time=True)
        if not dates:
            messagebox.showinfo("Completion Dates", "No completions recorded.")
        else:
            messagebox.showinfo("Completion Dates", "\n".join(dates))

    @staticmethod
    def view_missed_periods( habit: str) -> None:
        """Show missed periods for a habit"""
        missed = analytics.get_missed_periods(habit)
        if not missed:
            messagebox.showinfo("Missed Periods", "No missed periods.")
        else:
            if isinstance(missed[0], tuple):  # Weekly habit
                missed_str = "\n".join(f"{start} to {end}" for start, end in missed)
            else:  # Daily habit
                missed_str = "\n".join(missed)
            messagebox.showinfo("Missed Periods", missed_str)

    def delete_all_habits(self):
        """Delete all habits dialog"""
        habits = self.refresh_habit_list()
        if not habits:
            messagebox.showinfo("Info", "No Habits Found.")
        if habits:
            if messagebox.askyesno(
                    "Confirm",
                    f"Are you sure you want to delete all existing habits?"
            ):
                Habit.cleanup_data()
                messagebox.showinfo("Deleted", f"All Habits Deleted.")

    def manage_quotes(self) -> None:
        """Manage motivational quotes submenu"""
        window = tk.Toplevel(self.root)
        window.title("Motivational Quotes")

        button_config = [
            ("Get Motivated", self.get_motivation),
            ("Add a Quote", self.add_quote),
            ("Delete All Quotes", self.delete_all_quotes_dialog)
        ]

        for text, cmd in button_config:
            tk.Button(
                window,
                text=text,
                command=lambda c=cmd: (c(), window.destroy()),
                width=25
            ).pack(pady=10)




    @staticmethod
    def get_motivation() -> None:
        """Show a random quote from the collection"""
        quotes = Quote.load_quotes()
        if not quotes:
            messagebox.showinfo("No Quotes", "No quotes available. Add some first!")
            return

        # Select a random quote
        import random
        random_quote = random.choice(quotes)
        quote_text, author = list(random_quote.items())[0]
        messagebox.showinfo("Motivational Quote", f'"{quote_text}"\n- {author}')

    def add_quote(self) -> None:
        """Dialog for adding a new quote"""
        window = tk.Toplevel(self.root)
        window.title("Add New Quote")

        # Quote entry
        tk.Label(window, text="Quote Text:").pack(pady=(10, 0))
        quote_entry = tk.Text(window, height=4, width=40)
        quote_entry.pack(pady=5)

        # Author entry
        tk.Label(window, text="Author:").pack(pady=(10, 0))
        author_entry = tk.Entry(window)
        author_entry.pack(pady=5)

        def submit() -> None:
            quote_text = quote_entry.get("1.0", tk.END).strip()
            author = author_entry.get().strip()

            if not quote_text or not author:
                messagebox.showerror("Error", "Both fields are required.")
                return

            # Create and save quote
            quote = Quote(quote_text, author)
            quote.save_quote()
            messagebox.showinfo("Success", "Quote added successfully!")
            window.destroy()

        tk.Button(window, text="Save Quote", command=submit).pack(pady=10)

    @staticmethod
    def delete_all_quotes_dialog() -> None:
        """Delete all quotes dialog"""
        quotes = Quote.load_quotes()
        if not quotes:
            messagebox.showinfo("Info", "No quotes found.")
            return

        if messagebox.askyesno(
                "Confirm",
                "Are you sure you want to delete ALL quotes?\nThis action cannot be undone!"
        ):
            Quote.delete_all_quotes()
            messagebox.showinfo("Deleted", "All quotes have been deleted.")


if __name__ == "__main__":
    root = tk.Tk()
    app = HabitTrackerGUI(root)
    root.mainloop()