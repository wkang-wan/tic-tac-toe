class GameException(Exception):
    """Base exception for the game."""
    def __init__(self, detail: str):
        super().__init__(detail)

        self.detail = detail

class GameNotFoundException(GameException):
    pass

class GameFullException(GameException):
    pass

class NotPlayerTurnException(GameException):
    pass

class InvalidMoveException(GameException):
    pass

class PlayerAlreadyInGameException(GameException):
    pass