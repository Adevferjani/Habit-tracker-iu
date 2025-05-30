import json
import os

# Create data directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


class Quote:
    filename = os.path.join(DATA_DIR, "motivational_quotes.json")

    def __init__(self, quote, author):
        self.quote = quote
        self.author = author

    def to_dict(self):
        return {self.quote: self.author}

    def save_quote(self):
        # Initialize empty list if file doesn't exist
        if not os.path.exists(self.filename):
            data = []
        else:
            with open(self.filename, 'r') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []

        # Append new quote and save
        data.append(self.to_dict())
        with open(self.filename, 'w') as file:
            json.dump(data, file, indent=4)

    @classmethod
    def load_quotes(cls):
        """Load all quotes from the JSON file."""
        try:
            if os.path.exists(cls.filename):
                with open(cls.filename, 'r') as file:
                    return json.load(file)  # Returns a list of dictionaries
            return []
        except json.JSONDecodeError:
            # Return empty list if file is empty/corrupted
            return []

    @classmethod
    def delete_all_quotes(cls):
        """Delete all quotes from the JSON file"""
        try:
            with open(cls.filename, 'w') as file:
                json.dump([], file, indent=4)  # Overwrite with empty list
        except Exception as e:
            print(f"Error deleting quotes: {str(e)}")