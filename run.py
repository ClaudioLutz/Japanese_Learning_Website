# run.py
from app import create_app, db
from flask_migrate import Migrate
import click

app = create_app()
migrate = Migrate(app, db)

@app.cli.command("db_init")
def db_init():
    """Initializes the database."""
    db.create_all()
    print("Database initialized.")

@app.cli.command("db_migrate")
@click.argument("message")
def db_migrate(message):
    """Generates a new migration."""
    from flask_migrate import migrate as migrate_command
    migrate_command(message=message)

@app.cli.command("db_upgrade")
def db_upgrade():
    """Applies the latest migration."""
    from flask_migrate import upgrade
    upgrade()

@app.cli.command("db_downgrade")
def db_downgrade():
    """Downgrades the database by one revision."""
    from flask_migrate import downgrade
    downgrade()

if __name__ == '__main__':
    app.run(debug=True) # debug=True for development, turn off for production
