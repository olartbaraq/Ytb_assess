from flask import Flask
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
import os
from flask_cors import CORS

# Load .env file auyomatically
load_dotenv()

# initialize Rate Limiter instance
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],  # Example default limits
    storage_uri=os.getenv("REDIS_URI"),
)

# initialize cors origin
cors = CORS()


def create_app():
    # Initialize Flask APP
    app = Flask(__name__)

    # Initialize Redis Client
    Redis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASSWORD"),
        username=os.getenv("REDIS_USERNAME"),
    )

    # load limiter into app
    limiter.init_app(app)

    # Load cors into app
    cors.init_app(app)

    from .all_routes import bp  # Import the blueprint

    app.register_blueprint(bp)  # Register the blueprint

    return app
