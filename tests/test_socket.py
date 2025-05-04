import pytest
from app import app, socketio, game_rooms


@pytest.fixture
def test_client():
    app.config['TESTING'] = True
    client = socketio.test_client(app)
    yield client
    client.disconnect()


@pytest.fixture(autouse=True)
def clean_game_rooms():
    game_rooms.clear()
    game_rooms['testroom'] = {
        'host': 'Alice',
        'players': ['Alice'],
        'spy': None,
        'location': None,
        'locations': ['Location1', 'Location2'],
        'roles': {},
        'round_started': False
    }


def test_update_rooms_event(test_client):
    # Simulate a server-side event that emits 'update_rooms'
    socketio.emit('update_rooms', game_rooms, namespace='/')
    socketio.sleep(0.1)  # Let event propagate

    received = test_client.get_received(namespace='/')
    update_rooms_found = any(r['name'] == 'update_rooms' for r in received)
    assert update_rooms_found

    # Optional: Check that the payload matches
    for r in received:
        if r['name'] == 'update_rooms':
            assert r['args'][0] == game_rooms
