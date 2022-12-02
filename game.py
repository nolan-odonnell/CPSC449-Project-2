from cmath import exp
from pydoc import doc
import databases
import collections
import dataclasses
import sqlite3
import textwrap
import toml

from quart import Quart, g, request, abort
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request
from logging.config import dictConfig
import uuid

app = Quart(__name__)
QuartSchema(app)

app.config.from_file(f"./etc/{__name__}.toml", toml.load)


dictConfig({
    'version': 1,
    'loggers': {
        'quart.app': {
            'level': 'ERROR',
        },
    },
})


# @dataclasses.dataclass
# class Game:
#     username: str

@dataclasses.dataclass
class Guess:
    gameid: str
    word: str
    
    
# iteration to cycle through URLs    
def cycle(database):
    # cycle('ABCD') --> A B C D A B C D A B C D ...
    saved = []
    for url in database:
        yield url
        saved.append(url)
    while saved:
        for url in saved:
              yield url
              
    return saved

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
              
# async def _connect_db():
#     database = databases.Database(app.config["DATABASES"]["URL"])
#     await database.connect()
#     return database

# async def _get_db():
#     db1 = getattr(g, "_sqlite_db1", None)
#     db2 = getattr(g, "_sqlite_db2", None)
#     db3 = getattr(g, "_sqlite_db3", None)
#     if db1 is None:
#         db1 = g._sqlite_db1 = databases.Database(app.config["DATABASES"]["URL1"])
#         await db1.connect()
#     if db2 is None:
#         db2 = g._sqlite_db2 = databases.Database(app.config["DATABASES"]["URL2"])
#         await db2.connect()
#     if db3 is None:
#         db3 = g._sqlite_db3 = databases.Database(app.config["DATABASES"]["URL3"])
#         await db3.connect()
#     return db1, db2, db3


# @app.teardown_appcontext
# async def close_connection(exception):
#     db1 = getattr(g, "_sqlite_db1", None)
#     db2 = getattr(g, "_sqlite_db2", None)
#     db3 = getattr(g, "_sqlite_db3", None)
#     if db1 is not None:
#         db1 = g._sqlite_db1 = databases.Database(app.config["DATABASES"]["URL1"])
#         await db1.disconnect()
#     if db2 is not None:
#         db2 = g._sqlite_db2 = databases.Database(app.config["DATABASES"]["URL2"])
#         await db2.disconnect()
#     if db3 is not None:
#         db3 = g._sqlite_db3 = databases.Database(app.config["DATABASES"]["URL3"])
#         await db3.disconnect()

@app.route("/", methods=["GET"])
def index():
    return textwrap.dedent(
        """
        <h1>Wordle game microservice</h1>
        """
    )


@app.route("/games/", methods=["POST"])
# @validate_request(Game)
async def create_game():
    auth = request.authorization
    db = await _get_db()
    if auth == None:
        return {"Error": "User not verified"}, 401, {'WWW-Authenticate': 'Basic realm = "Login required"'}
    if auth["username"]:
        # Retrive random ID from the answers table
        word = await db.fetch_one(
            "SELECT answerid FROM answer ORDER BY RANDOM() LIMIT 1"
        )
        # app.logger.info("SELECT answerid FROM answer ORDER BY RANDOM() LIMIT 1")
            
        # Check if the retrived word is a repeat for the user, and if so grab a new word
        while await db.fetch_one(
            "SELECT answerid FROM games WHERE username = :username AND answerid = :answerid",
            values={"username": auth["username"], "answerid": word[0]},
        ):
            # app.logger.info(""""SELECT answerid FROM games WHERE username = :username AND answerid = :answerid",
            # values={"username": auth["username"],"answerid": word[0]}""")
                
            word = await db.fetch_one(
                "SELECT answerid FROM answer ORDER BY RANDOM() LIMIT 1"
            )
            # app.logger.info("SELECT answerid FROM answer ORDER BY RANDOM() LIMIT 1")

        # uuid for game with 0 guesses
        gameuuid = str(uuid.uuid4())
            
        # Create new game with 0 guesses
        query = "INSERT INTO game(gameid, guesses, gstate) VALUES(:gameid, :guesses, :gstate)"
        values = {"gameid": gameuuid, "guesses": 0, "gstate": "In-progress"}
        cur = await db.execute(query=query, values=values)
            

        # Create new row into Games table which connect with the recently connected game
        query = "INSERT INTO games(username, answerid, gameid) VALUES(:username, :answerid, :gameid)"
        values = {"username": auth["username"], "answerid": word[0], "gameid": gameuuid}
        cur = await db.execute(query=query, values=values)

        return values, 201


#Should validate to check if guess is in valid_word table
#if it is then insert into guess table 
#update game table by decrementing guess variable
#if word is not valid throw 404 exception
@app.route("/guess/",methods=["POST"])
@validate_request(Guess)
async def add_guess(data):
    db = await _get_db() 
    auth = request.authorization
    currGame = dataclasses.asdict(data)
    if auth == None:
        return {"Error": "User not verified"}, 401, {'WWW-Authenticate': 'Basic realm = "Login required"'}
    if auth["username"]:
        valid_game = await db.fetch_one(
            "SELECT * FROM games WHERE username = :username AND gameid = :gameid;", 
            values = {"username": auth["username"], "gameid": currGame.get('gameid') }
        )
    
    if valid_game:
        #checks whether guessed word is the answer for that game
        isAnswer= await db.fetch_one(
            "SELECT * FROM answer as a where (select count(*) from games where gameid = :gameid and answerid = a.answerid)>=1 and a.answord = :word;", currGame
            )
        # app.logger.info("""SELECT * FROM answer as a where (select count(*) from games where gameid = :gameid and answerid = a.answerid)>=1 and a.answord = :word;", currGame""")
    
        #is guessed word the answer
        if isAnswer is not None and len(isAnswer) >= 1:
            #update game status
            try:
                id_games = await db.execute(
                    """
                    UPDATE game set gstate = :status where gameid = :gameid
                    """,values={"status":"Finished","gameid":currGame['gameid']}
                )
            
            except sqlite3.IntegrityError as e:
                abort(404, e)
            
            return {"guessedWord":currGame["word"], "Accuracy":u'\u2713'*5},201
    
        #if 1 then word is valid otherwise it isn't valid and also check if they exceed guess limit
        isValidGuess = await db.fetch_one("SELECT * from valid_word where valword = :word;", values={"word":currGame["word"]})
        # app.logger.info(""""SELECT * from valid_word where valword = :word;", values={"word":currGame["word"]}""")
    
        guessNum = await db.fetch_one("SELECT guesses from game where gameid = :gameid",values={"gameid":currGame["gameid"]})
        # app.logger.info("""SELECT guesses from game where gameid = :gameid",values={"gameid":currGame["gameid"]}""")
    
        accuracy = ""
        if(isValidGuess is not None and len(isValidGuess) >= 1 and guessNum[0] < 6):
            try: 
                # make a dict mapping each character and its position from the answer
                answord = await db.fetch_one("SELECT answord FROM answer as a, games as g  where g.gameid = :gameid and g.answerid = a.answerid",values={"gameid":currGame["gameid"]})
                # app.logger.info(""""SELECT answord FROM answer as a, games as g  where g.gameid = :gameid and g.answerid = a.answerid",values={"gameid":currGame["gameid"]}""")
             
                ansDict = {}
                for i in range(len(answord[0])):
                    ansDict[answord[0][i]] = i
                
                #compare location of guessed word with answer
                guess_word = currGame["word"]
                for i in range(len(guess_word)):
                    if guess_word[i] in ansDict:
                        # print(ansDict.get(guess_word[i]))
                        if ansDict.get(guess_word[i]) == i:
                            accuracy += u'\u2713'
                        else:
                            accuracy += 'O'
                    else:
                        accuracy += 'X'
                #insert guess word into guess table with accruracy
                id_guess = await db.execute("INSERT INTO guess(gameid,guessedword, accuracy) VALUES(:gameid, :guessedword, :accuracy)",values={"guessedword":currGame["word"],"gameid":currGame["gameid"],"accuracy":accuracy})
                #update game table's guess variable by decrementing it
                id_games = await db.execute(
                    """
                    UPDATE game set guesses = :guessNum where gameid = :gameid
                    """,values={"guessNum":(guessNum[0]+1),"gameid":currGame['gameid']}
                )
                #if after updating game number of guesses reaches max guesses then mark game as finished 
                if(guessNum[0]+1 >= 6):
                    #update game status as finished
                    id_games = await db.execute(
                        """
                        UPDATE game set gstate = :status where gameid = :gameid
                        """,values={"status":"Finished","gameid":currGame['gameid']}
                    )
                    return currGame,202
            except sqlite3.IntegrityError as e:
                abort(404, e)
        else:
            #should return msg saying invalid word?
            return{"Error":"Invalid Word"}
        return {"guessedWord":currGame["word"], "Accuracy":accuracy},201

@app.route("/games/all", methods=["GET"])
async def all_games():
    db = await _get_db()
    auth = request.authorization
    if auth == None:
        return {"Error": "User not verified"}, 401, {'WWW-Authenticate': 'Basic realm = "Login required"'}
    games_val = await db.fetch_all( "SELECT * FROM game as a where gameid IN (select gameid from games where username = :username) and a.gstate = :gstate;", values = {"username":auth["username"],"gstate":"In-progress"})
    # app.logger.info(""""SELECT * FROM game as a where gameid IN (select gameid from games where username = :username) and a.gstate = :gstate;", values = {"username":auth["username"],"gstate":"In-progress"}""")
    if games_val is None or len(games_val) == 0:
        return { "Message": "No Active Games" },406
    return list(map(dict,games_val))

# getting games based on gameid 
@app.route("/games/<string:gameid>", methods=["GET"])
async def my_game(gameid):
    db = await _get_db()
    
    auth = request.authorization
    if auth == None:
        return {"Error": "User not verified"}, 401, {'WWW-Authenticate': 'Basic realm = "Login required"'}
    guess_val = await db.fetch_all( "SELECT a.*, b.guesses, b.gstate FROM guess as a, game as b WHERE a.gameid = b.gameid and a.gameid = :gameid", values={"gameid":gameid})
    # app.logger.info(""""SELECT a.*, b.guesses, b.gstate FROM guess as a, game as b WHERE a.gameid = b.gameid and a.gameid = :gameid", values={"gameid":gameid}""")

    if guess_val is None or len(guess_val) == 0:

        return { "Message": "No guesses made" },406

    return list(map(dict,guess_val))
    # else:
        # return { "Message": "Not A Valid Id" },406


@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409
