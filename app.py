import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app)

# Global dictionary for rooms. Each room holds its own game data.
game_rooms = {}

# Default set of locations
default_locations = [
    "School", "Casino", "Beach", "Restaurant", "Hospital",
    "Airport", "Park", "Mall", "Train Station", "Library",
    "Movie Theater", "Gym", "Office", "Zoo", "Hotel", "Current location",
    "Jarun lake", "College", "Funeral", "Disco club", "Lunopark", "Mars",
    "Bundek", "Prison", "Strip club"
]

@app.route('/')
def home():
    room = session.get('room')
    if room and room in game_rooms:
        room_data = game_rooms[room]
        return render_template("room.html", room=room, 
                               players=room_data['players'], 
                               locations=room_data['locations'], 
                               host=room_data['host'])
    # For players not in a room, pass the list of active game rooms
    return render_template("index.html", rooms=game_rooms)

@app.route('/host', methods=['GET', 'POST'])
def host():
    if request.method == 'POST':
        room_name = request.form['room']
        host_name = request.form['host']
        if room_name and host_name:
            if room_name not in game_rooms:
                game_rooms[room_name] = {
                    'host': host_name,
                    'players': [host_name],
                    'spy': None,
                    'location': None,
                    'locations': default_locations.copy(),
                    'roles': {},
                    'round_started': False,
                    'scores': {host_name: 0}  # Initialize the score for the host
                }
            session['room'] = room_name
            session['player_name'] = host_name
            # Broadcast the updated room list to everyone.
            socketio.emit('update_rooms', game_rooms)
            return redirect(url_for('home'))
    return render_template("host.html")

@socketio.on('update_score')
def update_score(data):
    room = session.get('room')
    if room and room in game_rooms:
        room_data = game_rooms[room]
        agent_won = data.get('agent_won', False)  # Boolean indicating if the agent won

        if agent_won:
            # Add a point to the agent's score
            room_data['scores'][room_data['spy']] += 1
        else:
            # Add a point to each non-agent player
            for player in room_data['players']:
                if player != room_data['spy']:
                    room_data['scores'][player] += 1

        #Emit updated scores to all players in the room
        socketio.emit('update_players', {
            'players': room_data['players'],
            'scores': room_data['scores']
        }, room=room)

@app.route('/delete_room', methods=['POST'])
def delete_room():
    room = session.get('room')
    if room and room in game_rooms:
        if session.get('player_name') == game_rooms[room]['host']:
            # Notify all players in the room that it has been deleted.
            socketio.emit('room_deleted', {'message': 'The room has been deleted by the host.'}, room=room)
            # Remove the room from the game_rooms dictionary.
            del game_rooms[room]
            # Clear session data for room membership.
            session.pop('room', None)
            socketio.emit('update_rooms', game_rooms)
            # (For the host, redirect immediately.)
            return redirect(url_for('home'))
        else:
            return "Unauthorized", 403
    return redirect(url_for('home'))

@app.route('/join_room', methods=['GET', 'POST'])
def join_room_route():
    if request.method == 'POST':
        room_name = request.form['room']
        player_name = request.form['player']
        if room_name in game_rooms and player_name:
            room = game_rooms[room_name]
            if player_name not in room['players']:
                room['players'].append(player_name)
                room['scores'][player_name ] = 0  # Initialize score for the new player
            # If a round is already in progress, mark the player as waiting.
            if room.get('round_started', False):
                session['waiting'] = True
            else:
                session['waiting'] = False
            session['room'] = room_name
            session['player_name'] = player_name
            return redirect(url_for('home'))
    return render_template("join.html")

@app.route('/leave_room', methods=['POST'])
def leave_room():
    room = session.get('room')
    player = session.get('player_name')
    if room and room in game_rooms:
        if player in game_rooms[room]['players']:
            game_rooms[room]['players'].remove(player)
            game_rooms[room]['scores'].pop(player, None)
        if not game_rooms[room]['players']:
            del game_rooms[room]
        else:
            socketio.emit('update_players', {
                    'players': game_rooms[room]['players'],
                    'scores': game_rooms[room]['scores']
                }, room=room)
        # If the player was the host, delete the room.
        # Broadcast updated room list—since a player left, it might change available rooms.
        socketio.emit('update_rooms', game_rooms)
    session.pop('room', None)
    session.pop('player_name', None)
    session.pop('waiting', None)
    return redirect(url_for('home'))

@socketio.on('connect')
def on_connect():
    room = session.get('room')
    if room and room in game_rooms:
        join_room(room)
        room_data = game_rooms[room]
        #Emit the current state of the game
        socketio.emit('update_players', {
        'players': room_data['players'],
        'scores': room_data['scores']
        }, room=room)
        socketio.emit('update_locations', {'locations': room_data['locations'], 'round_started': room_data['round_started']}, room=room)
        

@socketio.on('start_game')
def start_game():
    room = session.get('room')
    if room and room in game_rooms:
        room_data = game_rooms[room]

        # Only the host is allowed to start a game or next round.
        if session.get('player_name') != room_data['host']:
            return
        
        if len(room_data['players']) < 2:
            emit('error_message', "Not enough players to start the game!", room=room)
            return
        
        # (Optionally) Scale locations and choose random location/spy as before:
        room_data['locations'] = random.sample(default_locations,
            min(len(default_locations), (len(room_data['players']) -1) * 5))
        room_data['location'] = random.choice(room_data['locations'])
        room_data['spy'] = random.choice(room_data['players'])
        
        # Assign roles to ALL players
        for player in room_data['players']:
            if player == room_data['spy']:
                room_data['roles'][player] = "You are the spy! The location is unknown to you."
            else:
                room_data['roles'][player] = f"You are NOT the spy. The location is: {room_data['location']}"
        
        # Mark that a round has started.
        room_data['round_started'] = True

        # Emit game started event with updated roles and locations.
        emit('game_started', {'roles': room_data['roles'], 'locations': room_data['locations']}, room=room)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
