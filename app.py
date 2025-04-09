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
    "Bundek", "Prison"
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


# Route to host a new game room (GET presents a form; POST creates the room).
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
                    'round_started': False  # Indicates whether a round is currently in progress.
                }
            # Save room and player info in session
            session['room'] = room_name
            session['player_name'] = host_name
            return redirect(url_for('home'))
    return render_template("host.html")

@app.route('/delete_room', methods=['POST'])
def delete_room():
    room = session.get('room')
    # Verify the room exists and the current user is the host.
    if room and room in game_rooms:
        if session.get('player_name') == game_rooms[room]['host']:
            # Delete the room and clear the room from the session.
            del game_rooms[room]
            session.pop('room', None)
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
            # If a round is already in progress, mark the player as waiting.
            if room.get('round_started', False):
                session['waiting'] = True
            else:
                session['waiting'] = False
            session['room'] = room_name
            session['player_name'] = player_name
            return redirect(url_for('home'))
    return render_template("join.html")


# SocketIO event: when a client connects, add them to their room.
@socketio.on('connect')
def on_connect():
    room = session.get('room')
    if room:
        join_room(room)
        # Send the list of players for that room to all users in the room.
        emit('update_players', game_rooms[room]['players'], room=room)

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
            min(len(default_locations), len(room_data['players']) * 5))
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
