from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class PlayerBase(BaseModel):
    username: str

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class GameBase(BaseModel):
    pass

class GameCreate(GameBase):
    player1_id: int

class GameJoin(GameBase):
    game_id: int
    player2_id: int

class Game(GameBase):
    id: int
    player1_id: int
    player2_id: Optional[int] = None
    winner_id: Optional[int] = None
    current_turn_player_id: Optional[int] = None
    board: List[List[int]]
    status: str
    move_count: int

    model_config = ConfigDict(from_attributes=True)

class MoveCreate(BaseModel):
    player_id: int
    row: int
    col: int

class PlayerWins(BaseModel):
    player_id: int
    username: str
    win_count: int

class PlayerEfficiency(BaseModel):
    player_id: int
    username: str
    efficiency: float
