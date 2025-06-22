from sqlalchemy import create_engine, inspect
import os

# Path to the database file
db_path = os.path.join('instance', 'app.db')
engine = create_engine(f'sqlite:///{db_path}')

inspector = inspect(engine)

# Get constraints for the user_quiz_answer table
try:
    constraints = inspector.get_unique_constraints('user_quiz_answer')
    print("Unique constraints on user_quiz_answer:")
    if constraints:
        for constraint in constraints:
            print(f"- Name: {constraint['name']}, Columns: {constraint['column_names']}")
    else:
        print("No unique constraints found.")
except Exception as e:
    print(f"An error occurred: {e}")
    print("This might mean the table 'user_quiz_answer' does not exist yet.")
