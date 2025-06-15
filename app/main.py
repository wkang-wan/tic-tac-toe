from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List

from . import database_models, service_schemas
from .database import SessionLocal, engine
from .exceptions import *
from .service import Service

database_models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_service(db: Session = Depends(get_db)):
    return Service(db)

@app.exception_handler(GameException)
async def game_exception_handler(request: Request, exc: GameException):
    status_code = 400  # Default to 400 Bad Request

    # Assign specific status codes for different exception types
    if isinstance(exc, GameNotFoundException):
        status_code = 404
    elif isinstance(exc, NotPlayerTurnException):
        status_code = 403 # Forbidden
    elif isinstance(exc, (GameFullException, InvalidMoveException, PlayerAlreadyInGameException)):
        status_code = 409 # Conflict

    return JSONResponse(
        status_code=status_code,
        content={"error_message": exc.detail},
    )

@app.post("/players/", response_model=service_schemas.Player)
def create_player(player: service_schemas.PlayerCreate, service: Service = Depends(get_service)):
    db_player = service.get_player_by_username(username=player.username)
    if db_player:
        raise HTTPException(status_code=400, detail="Username already registered")
    return service.create_player(player=player)

@app.get("/players/", response_model=List[service_schemas.Player])
def read_players(skip: int = 0, limit: int = 100, service: Service = Depends(get_service)):
    players = service.get_players(skip=skip, limit=limit)
    return players

@app.post("/games/", response_model=service_schemas.Game)
def create_game(game: service_schemas.GameCreate, service: Service = Depends(get_service)):
    return service.create_game(player_id=game.player1_id)

@app.post("/games/{game_id}/join", response_model=service_schemas.Game)
def join_game(game_id: int, player_id: int, service: Service = Depends(get_service)):
    return service.join_game(game_id=game_id, player2_id=player_id)

@app.get("/games/{game_id}", response_model=service_schemas.Game)
def read_game(game_id: int, service: Service = Depends(get_service)):
    db_game = service.get_game(game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game

@app.post("/games/{game_id}/move", response_model=service_schemas.Game)
def make_move(game_id: int, move: service_schemas.MoveCreate, service: Service = Depends(get_service)):
    try:
        game = service.make_move(game_id=game_id, player_id=move.player_id, row=move.row, col=move.col)
        return game
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/leaderboard/", response_model=List[service_schemas.PlayerWins])
def get_leaderboard_by_wins(service: Service = Depends(get_service)):
    return service.get_leaderboard_by_wins()

@app.get("/leaderboard/efficiency", response_model=List[service_schemas.PlayerEfficiency])
def get_leaderboard_by_efficiency(service: Service = Depends(get_service)):
    return service.get_leaderboard_by_efficiency()
