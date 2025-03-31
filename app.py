import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import secrets
# Generates a 32-character hexadecimal string
roles = {}

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Replace with a secure, random key
socketio = SocketIO(app)

game_data = {
    "spy": None,
    "locations": [
        "School", "Casino", "Beach", "Restaurant", "Hospital",
        "Airport", "Park", "Mall", "Train Station", "Library",
        "Movie Theater", "Gym", "Office", "Zoo", "Hotel", "Current location",
        "Jarun lake", "Collage", "Funeral", "Dico club", "Lunopark", "Mars",
        "Bundek", "Prison"
    ],
    "players": []
}

@app.route('/')
def home():
    joined = session.get('joined', False)
    return render_template("index.html", players=game_data['players'], joined=joined, locations=game_data['locations'])


@app.route('/join', methods=['POST'])
def join():
    name = request.form['name']
    if name:
        game_data['players'].append(name)
        session['joined'] = True
        session['player_name'] = name
        # Notify all connected clients about the new player
        socketio.emit('update_players', game_data['players'])
    return redirect(url_for('home'))

# @app.route('/start_game', methods=['POST'])
@socketio.on('start_game')
def start_game():
    if len(game_data['players']) < 2:
        return "Not enough players to start the game!", 400  # Error if fewer than 2 players
    
    # Scale locations 
    locations =  random.sample(game_data["locations"], len(game_data["players"]) * 5)

    # Randomly select a location and a spy
    game_data['location'] = random.choice(game_data['locations'])
    game_data['spy'] = random.choice(game_data['players'])

    # Create a dictionary to hold role-based information
    for player in game_data['players']:
        if player == game_data['spy']:
            roles[player] = "You are the spy! The location is unknown to you."
        else:
            roles[player] = f"You are not the spy! The location is: {game_data['location']}"


    # Broadcast personalized data to all players
    socketio.emit('game_started', {"roles": roles, "locations": locations})
    return redirect(url_for('home'))


@app.route('/reset', methods=['POST'])
def reset_game():
    """Resets the game to its initial state."""
    game_data['players'].clear()
    game_data['spy'] = None
    game_data.pop('location', None)
    roles.clear()
    
    session.clear()  # Clear session to allow rejoining
    socketio.emit('game_reset')  # Notify all clients
    return redirect(url_for('home'))

@socketio.on('connect')
def handle_connect():
    emit('update_players', game_data['players'])
    emit('game_reset')  # Ensure UI resets when a player reconnects



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
