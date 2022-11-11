from pydoc import doc
import databases
import collections
import dataclasses
import sqlite3
import textwrap
import toml

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)


@dataclasses.dataclass
class User:
    first_name: str
    last_name: str
    user_name: str
    password: str


async def _connect_db():
    database = databases.Database(app.config["DATABASES"]["URL"])
    await database.connect()
    return database


def _get_db():
    if not hasattr(g, "sqlite_db"):
        g.sqlite_db = _connect_db()
    return g.sqlite_db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()


@app.route("/users/", methods=["POST"])
@validate_request(User)
async def create_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)
    try:
        #Attempt to create new user in database
        id = await db.execute(
            """
            INSERT INTO user(fname, lname, username, passwrd)
            VALUES(:first_name, :last_name, :user_name, :password)
            """,
            user,
        )
    #Return 409 error if username is already in table
    except sqlite3.IntegrityError as e:
        abort(409, e)

    user["id"] = id
    return user, 201

# User authentication endpoint
@app.route("/user-auth/<string:username>/<string:password>", methods=["GET"])
async def userAuth( username, password ):
    db = await _get_db()
    # Selection query with raw queries
    select_query = "SELECT * FROM user WHERE username= :username AND passwrd= :password"
    values = {"username": username, "password": password}

    # Run the command
    result = await db.fetch_one( select_query, values )

    # Is the user registered?
    if result:
        return { "authenticated": True }, 200

    else:
        return 401, { "WWW-Authenticate": "Fake Realm" }


@app.route("/games/<string:username>/all", methods=["GET"])
async def all_games(username):
    db = await _get_db()

    userid = await db.fetch_one(
            "SELECT userid FROM user WHERE username = :username", values={"username":username})
    if userid:

        games_val = await db.fetch_all( "SELECT * FROM game as a where gameid IN (select gameid from games where userid = :userid) and a.gstate = :gstate;", values = {"userid":userid[0],"gstate":"In-progress"})
        
        if games_val is None or len(games_val) == 0:
            return { "Message": "No Active Games" },406

        return list(map(dict,games_val))

    else:
        abort(404)


@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409
