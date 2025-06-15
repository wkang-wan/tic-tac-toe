"""
Integration tests for the API endpoints.

These tests use the `client` fixture which provides a FastAPI TestClient
with an isolated, in-memory database for each test function, ensuring
that tests do not interfere with one another.
"""

def test_create_player_success(client):
    """
    GIVEN a running FastAPI application
    WHEN a POST request is sent to /players/ with a valid username
    THEN the response should be 200 OK and return the created player.
    """
    response = client.post("/players/", json={"username": "player_one"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "player_one"
    assert "id" in data

def test_create_player_duplicate_fails(client):
    """
    GIVEN a player already exists
    WHEN a POST request is sent to /players/ with the same username
    THEN the response should be 400 Bad Request.
    """
    client.post("/players/", json={"username": "duplicate_user"}) # First time is OK
    response = client.post("/players/", json={"username": "duplicate_user"}) # Second time fails
    assert response.status_code == 400

def test_game_creation_and_joining(client):
    """
    GIVEN two players have been created
    WHEN one player creates a game and the second player joins it
    THEN the game state should be updated to 'in_progress' with both players.
    """
    # Arrange: Create two players
    p1_res = client.post("/players/", json={"username": "p1"})
    p2_res = client.post("/players/", json={"username": "p2"})
    p1_id = p1_res.json()["id"]
    p2_id = p2_res.json()["id"]

    # Act: Player 1 creates a game
    create_res = client.post("/games/", json={"player1_id": p1_id})
    assert create_res.status_code == 200
    game_data = create_res.json()
    game_id = game_data["id"]
    assert game_data["status"] == "pending"
    assert game_data["player2_id"] is None

    # Act: Player 2 joins the game
    join_res = client.post(f"/games/{game_id}/join?player_id={p2_id}")
    assert join_res.status_code == 200
    game_data = join_res.json()

    # Assert: Game is now in progress
    assert game_data["status"] == "in_progress"
    assert game_data["player1_id"] == p1_id
    assert game_data["player2_id"] == p2_id
    assert game_data["current_turn_player_id"] == p1_id

def test_join_nonexistent_game_fails(client):
    """
    GIVEN a player has been created
    WHEN they try to join a game with an ID that does not exist
    THEN the response should be 404 Not Found.
    """
    p1_res = client.post("/players/", json={"username": "p1"})
    p1_id = p1_res.json()["id"]

    response = client.post(f"/games/9999/join?player_id={p1_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["error_message"].lower()

def test_make_move_not_your_turn_fails(client):
    """
    GIVEN a game is in progress and it's player 1's turn
    WHEN player 2 tries to make a move
    THEN the response should be 403 Forbidden.
    """
    p1_res = client.post("/players/", json={"username": "p1"}).json()
    p2_res = client.post("/players/", json={"username": "p2"}).json()
    game = client.post("/games/", json={"player1_id": p1_res["id"]}).json()
    client.post(f"/games/{game['id']}/join?player_id={p2_res['id']}") # Game starts, p1's turn

    # Act: Player 2 tries to move out of turn
    response = client.post(f"/games/{game['id']}/move", json={"player_id": p2_res["id"], "row": 0, "col": 0})

    # Assert
    assert response.status_code == 403
    assert "not your turn" in response.json()["error_message"].lower()

def test_make_move_on_occupied_cell_fails(client):
    """
    GIVEN it is player 2's turn after player 1 moved to (0,0)
    WHEN player 2 tries to move to the same cell (0,0)
    THEN the response should be 409 Conflict.
    """
    p1 = client.post("/players/", json={"username": "p1"}).json()
    p2 = client.post("/players/", json={"username": "p2"}).json()
    game = client.post("/games/", json={"player1_id": p1["id"]}).json()
    client.post(f"/games/{game['id']}/join?player_id={p2['id']}")
    game_id = game['id']

    # P1 makes the first move
    client.post(f"/games/{game_id}/move", json={"player_id": p1["id"], "row": 0, "col": 0})

    # Act: P2 tries to move to the occupied cell
    response = client.post(f"/games/{game_id}/move", json={"player_id": p2["id"], "row": 0, "col": 0})

    # Assert
    assert response.status_code == 409
    assert "cell is already occupied" in response.json()["error_message"].lower()


def test_full_game_ends_in_win_and_updates_leaderboard(client):
    """
    GIVEN a fresh game
    WHEN players make moves resulting in a win for player 1
    THEN the game status should be 'finished', a winner declared, and the leaderboard updated.
    """
    # Arrange
    p1 = client.post("/players/", json={"username": "winner"}).json()
    p2 = client.post("/players/", json={"username": "loser"}).json()
    game = client.post("/games/", json={"player1_id": p1["id"]}).json()
    client.post(f"/games/{game['id']}/join?player_id={p2['id']}")
    game_id = game["id"]

    # Act: A sequence of moves leading to a win for P1 (top row)
    client.post(f"/games/{game_id}/move", json={"player_id": p1["id"], "row": 0, "col": 0}) # P1
    client.post(f"/games/{game_id}/move", json={"player_id": p2["id"], "row": 1, "col": 0}) # P2
    client.post(f"/games/{game_id}/move", json={"player_id": p1["id"], "row": 0, "col": 1}) # P1
    client.post(f"/games/{game_id}/move", json={"player_id": p2["id"], "row": 1, "col": 1}) # P2
    final_move_res = client.post(f"/games/{game_id}/move", json={"player_id": p1["id"], "row": 0, "col": 2}) # P1 wins

    # Assert game is finished with a winner
    assert final_move_res.status_code == 200
    final_game_state = final_move_res.json()
    assert final_game_state["status"] == "finished"
    assert final_game_state["winner_id"] == p1["id"]

    # Assert leaderboards are updated
    leaderboard_res = client.get("/leaderboard/")
    assert leaderboard_res.status_code == 200
    leaderboard_data = leaderboard_res.json()
    assert len(leaderboard_data) == 1
    assert leaderboard_data[0]["username"] == "winner"
    assert leaderboard_data[0]["win_count"] == 1

    efficiency_res = client.get("/leaderboard/efficiency")
    assert efficiency_res.status_code == 200
    efficiency_data = efficiency_res.json()
    assert efficiency_data[0]["username"] == "winner"
    assert efficiency_data[0]["efficiency"] == 5.0 # Game took 5 moves total

def test_full_game_ends_in_a_draw(client):
    """
    GIVEN a fresh game
    WHEN players fill the board with no winner
    THEN the game status should be 'finished' with no winner.
    """
    p1 = client.post("/players/", json={"username": "draw_p1"}).json()
    p2 = client.post("/players/", json={"username": "draw_p2"}).json()
    game = client.post("/games/", json={"player1_id": p1["id"]}).json()
    client.post(f"/games/{game['id']}/join?player_id={p2['id']}")
    game_id = game["id"]

    # A sequence of moves filling the board leading to a draw
    moves = [
        (p1["id"], 0, 0), (p2["id"], 1, 1),
        (p1["id"], 0, 1), (p2["id"], 0, 2),
        (p1["id"], 2, 0), (p2["id"], 1, 0),
        (p1["id"], 1, 2), (p2["id"], 2, 1),
        (p1["id"], 2, 2)
    ]

    final_move_res = None
    for player_id, r, c in moves:
        final_move_res = client.post(f"/games/{game_id}/move", json={"player_id": player_id, "row": r, "col": c})

    # Assert game is a draw
    assert final_move_res.status_code == 200
    final_game_state = final_move_res.json()
    assert final_game_state["status"] == "finished"
    assert final_game_state["winner_id"] is None
    assert final_game_state["move_count"] == 9
