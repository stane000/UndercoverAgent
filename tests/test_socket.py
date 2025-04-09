from flask_socketio import SocketIOTestClient
import unittest
from app import app, socketio, game_rooms

class SocketIOTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = socketio.test_client(app)
        # Start with a clean game_rooms state
        game_rooms.clear()
        # Optionally add a room that you can test against
        game_rooms['testroom'] = {
            'host': 'Alice',
            'players': ['Alice'],
            'spy': None,
            'location': None,
            'locations': ['Location1', 'Location2'],
            'roles': {},
            'round_started': False
        }

    def test_update_rooms_event(self):
        # Emit an event to trigger update_rooms (normally, your endpoints do this for you)
        socketio.emit('update_rooms', game_rooms)
        received = self.client.get_received()
        # Look for the 'update_rooms' event among the received messages
        update_rooms_found = any(r['name'] == 'update_rooms' for r in received)
        self.assertTrue(update_rooms_found)

    def tearDown(self):
        self.client.disconnect()

if __name__ == '__main__':
    unittest.main()
