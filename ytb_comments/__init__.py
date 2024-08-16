from flask import Flask
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
import os

load_dotenv()

limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"],  # Example default limits
    storage_uri="rediss://red-cqvm6vbtq21c7384431g:qYrmxOQPKJ3IQjUTOLGXHoTUsPmUuWG2@oregon-redis.render.com:6379",
)


def create_app():
    app = Flask(__name__)

    redis_conn = Redis(
        host="oregon-redis.render.com",
        port=6379,
        password="qYrmxOQPKJ3IQjUTOLGXHoTUsPmUuWG2",
        username="red-cqvm6vbtq21c7384431g",
    )

    # Initialize Flask-Limiter with default limits
    limiter.init_app(app)

    from .all_routes import bp  # Import the blueprint

    app.register_blueprint(bp)  # Register the blueprint

    return app
