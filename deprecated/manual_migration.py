from app import create_app, db

def run_manual_migration():
    """
    Manually adds the lesson_page table to the database.
    """
    app = create_app()
    with app.app_context():
        with db.engine.connect() as connection:
            # Use a transaction to ensure atomicity
            with connection.begin():
                # Create the lesson_page table
                connection.execute(db.text("""
                    CREATE TABLE lesson_page (
                        id INTEGER NOT NULL,
                        lesson_id INTEGER NOT NULL,
                        page_number INTEGER NOT NULL,
                        title VARCHAR(200),
                        description TEXT,
                        PRIMARY KEY (id),
                        FOREIGN KEY(lesson_id) REFERENCES lesson (id),
                        UNIQUE (lesson_id, page_number)
                    )
                """))
    print("Manual migration completed: 'lesson_page' table created.")

if __name__ == '__main__':
    run_manual_migration()
