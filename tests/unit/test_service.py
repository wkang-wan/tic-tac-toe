import pytest
from app.service import Service
from app.service_schemas import PlayerCreate
from app.exceptions import (
    GameFullException,
    GameNotFoundException,
    InvalidMoveException,
    NotPlayerTurnException,
    PlayerAlreadyInGameException
)

def test_create_player(db_session):
    """
    GIVEN a database session
    WHEN a new player is created with valid data
    THEN a new player record should be created in the database
    """
    # Arrange
    service = Service(db=db_session)
    player_data = PlayerCreate(username="test_player")

    # Act
    new_player = service.create_player(player=player_data)
    queried_player = service.get_player(new_player.id)
    queried__by_name_player = service.get_player_by_username(username=new_player.username)
    all_players = service.get_players()

    # Assert
    assert new_player is not None
    assert new_player.username == "test_player"
    assert new_player.id is not None
    assert queried_player is not None
    assert queried__by_name_player is not None
    assert len(all_players) == 1

def test_create_game(db_session):
    """
    GIVEN a database session
    WHEN a new game is created with valid data
    THEN a new game record should be created in the database
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))

    # Act
    new_game = service.create_game(player_id=player1.id)
    queried_game = service.get_game(game_id=new_game.id)

    # Assert
    assert new_game is not None
    assert queried_game is not None

def test_join_full_game_raises_exception(db_session):
    """
    GIVEN a game that is already full (has player1 and player2)
    WHEN another player tries to join
    THEN a GameFullException should be raised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    player3 = service.create_player(player=PlayerCreate(username="p3"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id) # Game is now full

    # Act & Assert
    with pytest.raises(GameFullException) as excinfo:
        service.join_game(game_id=game.id, player2_id=player3.id)
    
    assert "Game is already full" in str(excinfo.value)

def test_join_non_existed_game_raises_exception(db_session):
    """
    GIVEN a game that is not existed (has player1 and player2)
    WHEN another player tries to join
    THEN a GameNotFoundException should be raised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))

    # Act & Assert
    with pytest.raises(GameNotFoundException) as excinfo:
        service.join_game(game_id=999, player2_id=player1.id)
    
    assert "Game with id 999 not found" in str(excinfo.value)

def test_join_player_own_game_raises_exception(db_session):
    """
    GIVEN a game that is created by player1
    WHEN player1 tries to join again
    THEN a PlayerAlreadyInGameException should be raised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    
    game = service.create_game(player_id=player1.id)

    # Act & Assert
    with pytest.raises(PlayerAlreadyInGameException) as excinfo:
        service.join_game(game_id=game.id, player2_id=player1.id)
    
    assert "Player cannot join their own game" in str(excinfo.value)

def test_make_move(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 makes a move
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id) # Game is now full

    # Act & Assert
    updated_game = service.make_move(game_id=game.id, player_id=player1.id, row=0, col=0)
    assert updated_game.board[0][0] == player1.id

def test_make_move_game_not_found_raises_exception(db_session):
    """
    Makes a move in a non-existing game
    Then GameNotFoundException should be reaised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))

    # Act & Assert
    with pytest.raises(GameNotFoundException) as excinfo:
        service.make_move(game_id=999, player_id=player1.id, row=0, col=0)
    
    assert "Game with id 999 not found" in str(excinfo.value)

def test_make_move_in_invalid_cell_raises_exception(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 makes a move in an invalid cell
    Then InvalidMoveException should be reaised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id)

    # Act & Assert
    with pytest.raises(InvalidMoveException) as excinfo:
        service.make_move(game_id=game.id, player_id=player1.id, row=3, col=3)
    
    assert "Invalid cell coordinates" in str(excinfo.value)

def test_make_move_in_occupied_cell_raises_exception(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 has made a move in cell (0,0), Player2 tries to make a move in cell (0, 0) again
    Then InvalidMoveException should be reaised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id)

    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=0)

    # Act & Assert
    with pytest.raises(InvalidMoveException) as excinfo:
        service.make_move(game_id=game.id, player_id=player2.id, row=0, col=0)
    
    assert "Cell is already occupied" in str(excinfo.value)

def test_make_move_player_in_wrong_turn_raises_exception(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 has made a move in cell (0,0), Player1 tries to make a move again
    Then InvalidMoveException should be reaised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id)

    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=0)

    # Act & Assert
    with pytest.raises(NotPlayerTurnException) as excinfo:
        service.make_move(game_id=game.id, player_id=player1.id, row=1, col=0)
    
    assert "It's not your turn" in str(excinfo.value)

def test_make_move_player_in_wrong_turn_raises_exception(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 tries to move in a finished game
    Then InvalidMoveException should be raised
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id)

    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=0)
    service.make_move(game_id=game.id, player_id=player2.id, row=1, col=0)
    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=1)
    service.make_move(game_id=game.id, player_id=player2.id, row=1, col=1)
    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=2)

    # Act & Assert
    with pytest.raises(InvalidMoveException) as excinfo:
            service.make_move(game_id=game.id, player_id=player2.id, row=1, col=2)
    
    assert "Game is not in progress" in str(excinfo.value)

def test_get_leaderboard_by_wins(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 is the top winner
    """
    # Arrange
    service = Service(db=db_session)
    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game = service.create_game(player_id=player1.id)
    service.join_game(game_id=game.id, player2_id=player2.id)

    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=0)
    service.make_move(game_id=game.id, player_id=player2.id, row=1, col=0)
    service.make_move(game_id=game.id, player_id=player1.id, row=0, col=1)
    service.make_move(game_id=game.id, player_id=player2.id, row=1, col=1)
    game = service.make_move(game_id=game.id, player_id=player1.id, row=0, col=2)
    
    assert game.winner_id == player1.id
    assert game.move_count == 5

    playerWins = service.get_leaderboard_by_wins()
    assert playerWins[0].player_id == player1.id

def test_get_leaderboard_by_efficiency(db_session):
    """
    GIVEN a game that is joined by two players
    Player1 is the top winner
    """
    # Arrange
    service = Service(db=db_session)

    player1 = service.create_player(player=PlayerCreate(username="p1"))
    player2 = service.create_player(player=PlayerCreate(username="p2"))
    
    game1 = service.create_game(player_id=player1.id)
    service.join_game(game_id=game1.id, player2_id=player2.id)

    service.make_move(game_id=game1.id, player_id=player1.id, row=0, col=0)
    service.make_move(game_id=game1.id, player_id=player2.id, row=1, col=0)
    service.make_move(game_id=game1.id, player_id=player1.id, row=2, col=1)
    service.make_move(game_id=game1.id, player_id=player2.id, row=1, col=1)
    service.make_move(game_id=game1.id, player_id=player1.id, row=0, col=2)
    service.make_move(game_id=game1.id, player_id=player2.id, row=1, col=2)

    game2 = service.create_game(player_id=player1.id)
    service.join_game(game_id=game2.id, player2_id=player2.id)

    service.make_move(game_id=game2.id, player_id=player1.id, row=0, col=0)
    service.make_move(game_id=game2.id, player_id=player2.id, row=1, col=0)
    service.make_move(game_id=game2.id, player_id=player1.id, row=0, col=1)
    service.make_move(game_id=game2.id, player_id=player2.id, row=1, col=1)
    service.make_move(game_id=game2.id, player_id=player1.id, row=2, col=1)
    service.make_move(game_id=game2.id, player_id=player2.id, row=2, col=2)
    service.make_move(game_id=game2.id, player_id=player1.id, row=0, col=2)

    playerWins = service.get_leaderboard_by_efficiency()
    assert playerWins[0].player_id == player2.id