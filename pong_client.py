import pygame
import socket
import pickle

# client settings
SERVER_IP = "192.168.0.133"
SERVER_PORT = 12346
BUFFER_SIZE = 4096
list_of_sockets = []

# game settings
paddle_height = 80
paddle_width = 15
ball_size = 15
ball_radius = 12
game_width = 800
game_height = 400

# get player name and server password
player_name = input('Enter your name: ')
password = input('Enter server password: ')
server_pass = pickle.dumps(password)

# initialize pygame
pygame.init()
screen = pygame.display.set_mode((game_width, game_height))
pygame.display.set_caption("Game of Pong")
clock = pygame.time.Clock()

# game socket setup
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
list_of_sockets.append(sock)

# set two sockets for identyfication and authentication
identification_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
list_of_sockets.append(identification_socket)

authentication_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
list_of_sockets.append(authentication_socket)


def authenticate():
    authentication_socket.sendto(server_pass, (SERVER_IP, 12347))
    data, _ = authentication_socket.recvfrom(BUFFER_SIZE)
    if data:
        status_code = pickle.loads(data)
        if status_code == 'OK':
            return True
        else:
            return False


def join_game():
    global running
    # authenticate with server password
    authentication_is_successfull = authenticate()

    if authentication_is_successfull:
        # send name and receive player_id
        identification_socket.sendto(pickle.dumps(player_name), (SERVER_IP, 12345))
        player_id_data, _ = identification_socket.recvfrom(BUFFER_SIZE)
        player_id = pickle.loads(player_id_data)
        print(f'player_id: {player_id}')

        if player_id == 'player_2':
            running = True
            return player_id
        elif player_id == 'player_1':
            waiting = True
            while waiting:
                print('. ', end='')
                data,_ = authentication_socket.recvfrom(BUFFER_SIZE)
                data = pickle.loads(data)
                if data:
                    if data == "START":
                        running = True
                        waiting = False
                        return player_id
        else:
            print('Waiting for the server...')
    else:
        print('Wrong password, try again.')


# initial player position
player_pos = game_height // 2 - paddle_height // 2

# initial value for the main game loop
running = False

# if you're assigned player_id we can start the game
# as the running will be set to True
player_id = join_game()

# main game loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                pygame.quit()
                for s in list_of_sockets: s.close()

    # player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player_pos -= 5
    if keys[pygame.K_DOWN]:
        player_pos += 5

    # keep paddle on screen
    player_pos = max(player_pos, 0)
    player_pos = min(player_pos, game_height - paddle_height)

    # send player position to server
    sock.sendto(pickle.dumps((player_id, player_pos, player_name)), (SERVER_IP, SERVER_PORT))

    # receive game state from server
    data, _ = sock.recvfrom(BUFFER_SIZE)
    game_state = pickle.loads(data)

    # draw everything
    screen.fill((0, 0, 0))
    for p_id, p_info in game_state["players"].items():
        color = (0, 255, 0) if p_id == player_id else (255, 0, 0)
        # extract oponent's name
        if p_info["name"] != player_name:
            enemy_name = p_info["name"]

        pygame.draw.rect(
            screen, color, (p_info["x"], p_info["y"], paddle_width, paddle_height)
        )

    ball = game_state["ball"]
    pygame.draw.circle(
        screen, (255,255,255), (ball["x"], ball["y"]), ball_radius
    )

    # displaying the score
    # first create font object to then render text on screen
    font = pygame.font.Font('freesansbold.ttf',24)

    # at some point maybe I can figure out more elegant way to do this, but for now
    player_score = font.render(f'{player_name}: {game_state["players"][player_id]["score"]}', True, (255, 255, 255))
    enemy_score = font.render(f'{enemy_name}: {game_state["players"]["player_2"]["score"] if player_id == "player_1" else game_state["players"]["player_1"]["score"]}', True, (255, 255, 255))
    
    # placing player's score above player's paddle
    # left paddle is player_1, right paddle is player_2
    if game_state["players"]["player_1"]["name"] == player_name:
        screen.blit(player_score, (10,10))
        screen.blit(enemy_score, (500,10))
    else:
        screen.blit(enemy_score, (10,10))
        screen.blit(player_score, (500,10))

    # update the display
    pygame.display.flip()

    # cap the frame rate
    clock.tick(60)

pygame.quit()
for s in list_of_sockets: s.close()
