from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    player1_id = Column(Integer, ForeignKey("players.id"))
    player2_id = Column(Integer, ForeignKey("players.id"))
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    current_turn_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    board = Column(JSON, default=[[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    status = Column(String, default="pending")  # pending, in_progress, finished
    move_count = Column(Integer, default=0)

    player1 = relationship("Player", foreign_keys=[player1_id])
    player2 = relationship("Player", foreign_keys=[player2_id])
    winner = relationship("Player", foreign_keys=[winner_id])
    current_turn_player = relationship("Player", foreign_keys=[current_turn_player_id])