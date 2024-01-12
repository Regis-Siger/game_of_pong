import socket
import threading
import pickle

# server conf
SERVER_IP = "192.168.0.133"
SERVER_PORT = 12346
BUFFER_SIZE = 4096
number_of_players = 0
PASSWORD = '69'

# game settings
paddle_height = 80
paddle_width = 15
ball_size = 15
ball_radius = 12.0
game_width = 800
game_height = 400

# player positions
players = {
    "player_1": {
        "x": 30,
        "y": game_height // 2 - paddle_height // 2,
        "score": 0,
        "ip": None,
        "port": None,
        "name": None
    },
    "player_2": {
        "x": game_width - 30 - paddle_width,
        "y": game_height // 2 - paddle_height // 2,
        "score": 0,
        "ip": None,
        "port": None,
        "name": None
    },
}

# ball position and velocity
ball = {
    "x": game_width // 2, 
    "y": game_height // 2, 
    "vx": 8, 
    "vy": 0, 
    "radius": ball_radius,
    "max_vel": 9
}

# game socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((SERVER_IP, SERVER_PORT))

# veryfication socket setup
veryfication_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
veryfication_socket.bind((SERVER_IP, 12345))

print(f"Server started at {SERVER_IP}:{SERVER_PORT}")

# maing game logic
def game_logic():
    global ball
    while True:
        # update ball position
        ball["x"] += ball["vx"]
        ball["y"] += ball["vy"]

        # collistion with top/bottom walls
        if ball["y"] <= 0 or ball["y"] >= game_height - ball_size:
            ball["vy"] = -ball["vy"]

        # collision with paddles
        p1 = players["player_1"] # left paddle
        p2 = players["player_2"] # right paddle
        
        if ball['vx'] < 0:
            if ball['y'] >= p1['y'] and ball['y'] <= p1['y'] + paddle_height:
                if ball['x'] - ball['radius'] <= p1['x'] + paddle_width:
                    ball['vx'] *= -1

                    middle_y = p1["y"] + paddle_height / 2
                    difference_in_y = middle_y - ball['y']
                    reduction_factor = (paddle_height / 2) / ball['max_vel']
                    y_vel = difference_in_y / reduction_factor
                    ball['vy'] = -1 * y_vel

        else:
            if ball['y'] >= p2['y'] and ball['y'] <= p2['y'] + paddle_height:
                if ball['x'] + ball['radius'] >= p2['x']:
                    ball['vx'] *= -1

                    middle_y = p2["y"] + paddle_height / 2
                    difference_in_y = middle_y - ball['y']
                    reduction_factor = (paddle_height / 2) / ball['max_vel']
                    y_vel = difference_in_y / reduction_factor
                    ball['vy'] = -1 * y_vel


        # scoring
        if ball["x"] <= 0:
            players["player_2"]["score"] += 1
            ball = {
                "x": game_width // 2, 
                "y": game_height // 2, 
                "vx": 8, 
                "vy": 0, 
                "radius": ball_radius,
                "max_vel": 9
            }
            
        elif ball["x"] >= game_width - ball_radius:
            players["player_1"]["score"] += 1
            ball = {
                "x": game_width // 2, 
                "y": game_height // 2, 
                "vx": -8, 
                "vy": 0, 
                "radius": ball_radius,
                "max_vel": 9
            }
            


        # send game state to all players
        game_state = pickle.dumps({"players": players, "ball": ball})
        for player in players.values():
            if player["ip"] is not None and player["port"] is not None:
                sock.sendto(game_state, (player["ip"], player["port"]))

        # game update rate (60 fps)
        threading.Event().wait(1 / 60)

# listen for incoming players and authenticate them against PASSWORD
def listen_for_players():
    while True:
        data, address = veryfication_socket.recvfrom(BUFFER_SIZE)
        name, passw = pickle.loads(data)
        print(f'{name} from {address} connected')
        if passw == PASSWORD:
            if players["player_1"]["name"] is None:
                players["player_1"]["name"] = name
                veryfication_socket.sendto(pickle.dumps('player_1'), (address))


            elif players["player_2"]["name"] is None:
                players["player_2"]["name"] = name
                veryfication_socket.sendto(pickle.dumps('player_2'), (address))

            else:
                veryfication_socket.sendto(pickle.dumps('WaitForPlayer'), (address))
        else:
            print(f'{name} messed up the password, disconnected.')
            veryfication_socket.sendto(pickle.dumps('Wrong password.'), (address))


# receive communication from clients
def receive_data_from_client():
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        player_id, player_pos, player_name = pickle.loads(data)
        players[player_id]["name"] = player_name
        players[player_id]["y"] = player_pos
        players[player_id]["ip"], players[player_id]["port"] = addr    

        
threading.Thread(target=listen_for_players).start()
threading.Thread(target=receive_data_from_client).start()
threading.Thread(target=game_logic).start()
