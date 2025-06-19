from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import func

from . import database_models, service_schemas
from .exceptions import (
    GameNotFoundException,
    GameFullException,
    NotPlayerTurnException,
    InvalidMoveException,
    PlayerAlreadyInGameException
)

class Service:

    def __init__(self, db: Session):
        self.db = db

    def get_player(self, player_id: int):
        return self.db.query(database_models.Player).filter(database_models.Player.id == player_id).first()

    def get_player_by_username(self, username: str):
        return self.db.query(database_models.Player).filter(database_models.Player.username == username).first()

    def get_players(self, skip: int = 0, limit: int = 100):
        return self.db.query(database_models.Player).offset(skip).limit(limit).all()

    def create_player(self, player: service_schemas.PlayerCreate):
        db_player = database_models.Player(username=player.username)
        self.db.add(db_player)
        self.db.commit()
        self.db.refresh(db_player)
        return db_player

    def create_game(self, player_id: int):
        db_game = database_models.Game(player1_id=player_id)
        self.db.add(db_game)
        self.db.commit()
        self.db.refresh(db_game)
        return db_game

    def get_games(self, skip: int = 0, limit: int = 100):
        return self.db.query(database_models.Game).order_by(database_models.Game.id).offset(skip).limit(limit).all()

    def join_game(self, game_id: int, player2_id: int):
        db_game = self.db.query(database_models.Game).filter(database_models.Game.id == game_id).first()
        if not db_game:
            raise GameNotFoundException(detail=f"Game with id {game_id} not found.")
        if db_game.player2_id:
            raise GameFullException(detail="Game is already full.")
        if db_game.player1_id == player2_id:
            raise PlayerAlreadyInGameException(detail="Player cannot join their own game.")


        db_game.player2_id = player2_id
        db_game.status = "in_progress"
        db_game.current_turn_player_id = db_game.player1_id
        self.db.commit()
        self.db.refresh(db_game)
        return db_game

    def get_game(self, game_id: int):
        return self.db.query(database_models.Game).filter(database_models.Game.id == game_id).first()

    def _check_win(self, board, player_id):
        # Check rows and columns
        for i in range(3):
            if all(board[i][j] == player_id for j in range(3)) or \
            all(board[j][i] == player_id for j in range(3)):
                return True
        # Check diagonals
        if all(board[i][i] == player_id for i in range(3)) or \
        all(board[i][2-i] == player_id for i in range(3)):
            return True
        return False

    def make_move(self, game_id: int, player_id: int, row: int, col: int):
        with self.db.begin_nested():
            # The .with_for_update() translates to a SELECT ... FOR UPDATE SQL statement.
            # When PostgreSQL executes this, it places a write lock on the specific row(s) returned by the query.
            # Instead of this Pessimistic Locking solution, we can also consider use Optimistic Locking solution
                # 1. Add a version column: add an integer version column to your games table.
                # 2. Read and Check: When make_move is called, read the game data and its current version number (e.g., 5).
                # 3. Conditional Write: When writing the changes back, use a conditional UPDATE statement:
                #    UPDATE games SET board = ..., version = 6 WHERE id = 123 AND version = 5;
                # 4. Verify the Update: when 1 row is updated, the update is successful; otherwise 0 row is updated.
                # 5. Handle the failure: when 0 row is updated, we need to handle it in the application.
                #    We can either retry automatically, or ask client to retry
            db_game = self.db.query(database_models.Game).filter(database_models.Game.id == game_id).with_for_update().first()

            if not db_game:
                raise GameNotFoundException(detail=f"Game with id {game_id} not found.")
            if db_game.status != "in_progress":
                raise InvalidMoveException(detail="Game is not in progress.")
            if db_game.current_turn_player_id != player_id:
                raise NotPlayerTurnException(detail="It's not your turn.")
            if not (0 <= row < 3 and 0 <= col < 3):
                raise InvalidMoveException(detail="Invalid cell coordinates.")
            if db_game.board[row][col] != 0:
                raise InvalidMoveException(detail="Cell is already occupied.")

            # Modify in-place
            db_game.board[row][col] = player_id
            
            flag_modified(db_game, "board")

            db_game.move_count += 1

            if self._check_win(db_game.board, player_id):
                db_game.winner_id = player_id
                db_game.status = "finished"
            elif db_game.move_count == 9:
                db_game.status = "finished" # Draw

            db_game.current_turn_player_id = db_game.player2_id if db_game.current_turn_player_id == db_game.player1_id else db_game.player1_id
            self.db.commit()
        self.db.refresh(db_game)
        return db_game

    def get_leaderboard_by_wins(self):
        results = self.db.query(
            database_models.Player.id,
            database_models.Player.username,
            func.count(database_models.Game.winner_id).label('win_count')
        ).join(database_models.Game, database_models.Player.id == database_models.Game.winner_id)\
        .group_by(database_models.Player.id)\
        .order_by(func.count(database_models.Game.winner_id).desc())\
        .limit(3).all()

        return [service_schemas.PlayerWins(player_id=r[0], username=r[1], win_count=r[2]) for r in results]

    def get_leaderboard_by_efficiency(self):
        results = self.db.query(
            database_models.Player.id,
            database_models.Player.username,
            func.avg(database_models.Game.move_count).label('efficiency')
        ).join(database_models.Game, database_models.Player.id == database_models.Game.winner_id)\
        .group_by(database_models.Player.id)\
        .order_by(func.avg(database_models.Game.move_count).asc())\
        .limit(3).all()

        return [service_schemas.PlayerEfficiency(player_id=r[0], username=r[1], efficiency=r[2]) for r in results]
