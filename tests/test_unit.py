import unittest
from app import app, game_rooms

class FlaskRoutesTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        # Optionally clear or set up game_rooms for a clean state
        game_rooms.clear()

    def test_host_room(self):
        # Simulate a post to create a room
        response = self.client.post('/host', data={
            'host': 'Alice',
            'room': 'testroom'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # After hosting, the room should appear in the game_rooms dictionary
        self.assertIn('testroom', game_rooms)

    def test_join_room_without_player(self):
        # This test would simulate what happens when the "player" field is missing,
        # ensuring that your code returns an error.
        response = self.client.post('/join_room', data={
            'room': 'testroom'
        })
        self.assertEqual(response.status_code, 400)  # or however you handle the error

if __name__ == '__main__':
    unittest.main()
