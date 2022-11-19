PRAGMA foreign_KEYs=ON;
BEGIN TRANSACTION;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS game;
DROP TABLE IF EXISTS guess;
DROP TABLE IF EXISTS answer;
DROP TABLE IF EXISTS valid_word;

CREATE TABLE games (
    gamesid INTEGER PRIMARY KEY AUTOINCREMENT,
    username INTEGER,
    answerid INTEGER,
    gameid TEXT,
    FOREIGN KEY (answerid) REFERENCES answer(answerid),
    FOREIGN KEY(gameid) REFERENCES game(gameid)
);

CREATE TABLE game(
    gameid TEXT PRIMARY KEY,
    guesses INTEGER,
    gstate VARCHAR(12)
);

CREATE TABLE guess(
    guessid INTEGER PRIMARY KEY AUTOINCREMENT,
    gameid TEXT,
    guessedword VARCHAR(5),
    accuracy VARCHAR(5),
    FOREIGN KEY(gameid) REFERENCES game(gameid)
);

CREATE TABLE answer(
    answerid INTEGER PRIMARY KEY AUTOINCREMENT,
    answord VARCHAR(5)
);

CREATE TABLE valid_word(
    valid_id INTEGER PRIMARY KEY AUTOINCREMENT,
    valword VARCHAR(5)
);

CREATE INDEX games_idx_a114f231 ON games(username, answerid);
CREATE INDEX games_idx_8df6ac78 ON games(gameid, answerid);
CREATE INDEX answer_idx_0382b0a6 ON answer(answord);
CREATE INDEX valid_word_idx_0420916f ON valid_word(valword);
CREATE INDEX games_idx_25674218 ON games(username);
CREATE INDEX game_idx_0069bed0 ON game(gstate);
CREATE INDEX guess_idx_0067de6f ON guess(gameid);
COMMIT;