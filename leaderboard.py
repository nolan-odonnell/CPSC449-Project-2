from pydoc import doc
import sqlite3
import redis
import dataclasses
import collections
import textwrap
from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

redisClient = redis.Redis(host='localhost', port=5100, db=0, decode_responses=True)

@dataclasses.dataclass
class Leaderboard:
    user: str
    score: int

@app.route("/scores/", methods=["POST"])
@validate_request(Leaderboard)
async def postScores(data: Leaderboard):
    boardSet = "Leaderboard"
    boardData = dataclasses.asdict(data)
    scores = redisClient.zadd(boardSet, {boardData["user"]: boardData["score"]})

    if scores == 1:
        return {boardData["user"]: boardData["score"]}, 200
    elif scores == 0:
        return {boardData["user"]: boardData["score"]}, 200
    elif scores != int:
        return {"ERROR:" "Error"}, 404
    else:
        return {"ERROR": "Unknown Error"}, 409

@app.route("/topten/", methods=["GET"])
async def topTen():
    boardSet = "Leaderboard"
    topTen = redisClient.zrange(boardSet, 0, 9, desc=True, withscores=True)
    if topTen != None:
        return dict(topTen), 200
    else:
        return {"ERROR": "Empty"}, 404