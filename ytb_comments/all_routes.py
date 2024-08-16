import os
from flask import request, jsonify, Blueprint
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import asyncio
import logging

from . import limiter

bp = Blueprint("main", __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


api_key = os.getenv("YT_API_KEY")
yt_client = build("youtube", "v3", developerKey=api_key)


async def fetch_comment_threads(client, video_id, token=None):
    try:
        response = await asyncio.to_thread(
            client.commentThreads()
            .list(
                part="snippet",
                videoId=video_id,
                textFormat="plainText",
                pageToken=token,
            )
            .execute
        )
        logger.info(f"Fetched comment threads for video ID: {video_id}")
        return response
    except HttpError as error:
        logger.error(f"HTTP error {error.resp.status}: {error.content}")
        return {"error": f"An HTTP error {error.resp.status} occurred: {error.content}"}
    except Exception as error:
        logger.error(f"General error occurred: {error}")
        return {"error": f"An error occurred: {error}"}


async def fetch_video_statistics(client, video_id, token=None):
    try:
        response = await asyncio.to_thread(
            client.videos()
            .list(
                part="snippet,statistics",
                id=video_id,
                pageToken=token,
            )
            .execute
        )
        logger.info(f"Fetched video statistics for video ID: {video_id}")
        return response
    except HttpError as error:
        logger.error(f"HTTP error {error.resp.status}: {error.content}")
        return {"error": f"An HTTP error {error.resp.status} occurred: {error.content}"}
    except Exception as error:
        logger.error(f"General error occurred: {error}")
        return {"error": f"An error occurred: {error}"}


# Custom error handler for rate limit exceeded
@bp.errorhandler(429)
def ratelimit_error(e):
    logger.info("Rate limit exceeded.")
    response = jsonify(
        {
            "error": "rate_limit_exceeded",
            "message": "You have exceeded the rate limit. Please try again later.",
            "status_code": 429,
        }
    )
    response.status_code = 429
    return response


@bp.route("/get_video_details", methods=["POST"])
# @limiter.limit("100/day;15/hour;3/minute")
async def home_page():

    data = request.get_json()

    error = None

    # Check if the data is valid and supplied
    # if not data:
    #     error = "Missing fields are required"
    #     logger.warning("Missing fields not provided in the request")
    if not data.get("video_id"):
        error = "Video ID is required"
        logger.warning("Video ID not provided in the request")
    # if not data.get("page"):
    #     error = "page is required"
    #     logger.warning("Page not provided in the request")

    if error is None:
        video_id = data["video_id"]
        page: str | None = data.get("page")
        logger.info(f"Processing request for video ID: {video_id} on page: {page}")

        async def fetch_data():
            next_page_token = page
            all_comments = []
            resp = await fetch_comment_threads(yt_client, video_id, next_page_token)
            if "error" in resp:
                return resp  # Return error if any
            all_comments.extend(resp.get("items", []))
            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                logger.info(
                    f"Fetched {len(all_comments)} comments for video ID: {video_id}"
                )
            overall_resp = {
                "comments": all_comments,
                "next_page_token": next_page_token,
            }
            return overall_resp

        try:
            # Run both functions in parallel
            overall_resp, video_statistics_resp = await asyncio.gather(
                fetch_data(), fetch_video_statistics(yt_client, video_id)
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred during async tasks: {e}")
            return jsonify({"error": "An internal error occurred"}), 500

        if "error" in overall_resp:
            logger.warning(
                f"Error in fetching comments: {overall_resp['comments']['error']}"
            )
            return jsonify(overall_resp), 400
        if "error" in video_statistics_resp:
            logger.warning(
                f"Error in fetching video statistics: {video_statistics_resp['error']}"
            )
            return jsonify(video_statistics_resp), 400

        next_page_token = overall_resp["next_page_token"]
        video_statistics = video_statistics_resp.get("items", [])
        total_comments = len(overall_resp.get("comments"))

        response_data = {
            "nextPageToken": next_page_token,
            "total_comments": total_comments,
            "comments": overall_resp["comments"],
            "video_statistics": video_statistics[0],
        }

        logger.info(f"Successfully fetched video details for video ID: {video_id}")
        return (
            jsonify(
                {
                    "message": "Video Details fetched successfully",
                    "status": "success",
                    "data": response_data,
                }
            ),
            200,
        )

    else:
        logger.warning(f"Error occurred: {error}")
        return jsonify({"status": "failure", "message": f"{error}"}), 400
