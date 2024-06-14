from app import create_app
from logging_config import setup_logging
import os

env = os.getenv('FLASK_ENV', 'development')
setup_logging(env)

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host="0.0.0.0", port=port, debug=(env == 'development'))