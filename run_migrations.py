from app import create_app, db
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)

with app.app_context():
    # This script is just for setting up the context.
    # You still need to run the flask db commands in your terminal.
    print("Flask app context created. Run 'flask db migrate' and 'flask db upgrade'.")
