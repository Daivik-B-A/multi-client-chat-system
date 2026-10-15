import socket
import threading
import time

# Server configuration
HOST = '0.0.0.0'
PORT = 6666

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((HOST, PORT))
server.listen()

clients = {}      # socket -> username
client_rooms = {} # socket -> room name

def broadcast(message, sender_socket, room_name, include_sender=False):
    """Sends a message to all clients in the specified room."""
    for client in clients:
        if client_rooms.get(client) == room_name:
            if client != sender_socket or include_sender:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    client.close()
                    remove_client(client)

def remove_client(client):
    """Clean up disconnected clients."""
    if client in clients:
        name = clients[client]
        room = client_rooms.get(client, 'Lobby')
        del clients[client]
        if client in client_rooms:
            del client_rooms[client]
        broadcast(f"SYSTEM: {name} left the chat.\n", client, room)
        client.close()

def handle_client(client):
    """Handles individual client connections, commands, and messaging."""
    try:
        # Request and store username
        client.send("REGISTER: Enter username:\n".encode('utf-8'))
        username = client.recv(1024).decode('utf-8').strip()
        if not username:
            client.close()
            return

        clients[client] = username
        client_rooms[client] = 'Lobby'  # Default starting room
        
        print(f"[+] {username} connected.")
        broadcast(f"SYSTEM: {username} joined.\n", client, 'Lobby', include_sender=True)

        while True:
            start_time = time.time()
            data = client.recv(1024)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            if not message:
                continue

            # Calculate and log latency metric
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            print(f"[METRIC] Latency for {username}: {latency_ms:.3f} ms")

            current_room = client_rooms.get(client, 'Lobby')

            # Handle room switching command: /join <room_name>
            if message.startswith('/join '):
                new_room = message.split(' ', 1)[1].strip()
                if new_room:
                    # Notify old room that user left
                    broadcast(f"SYSTEM: {username} left for {new_room}.\n", client, current_room)
                    
                    # Update room state
                    client_rooms[client] = new_room
                    client.send(f"SYSTEM: Joined room '{new_room}'\n".encode('utf-8'))
                    
                    # Notify new room that user arrived
                    broadcast(f"SYSTEM: {username} joined.\n", client, new_room)

            # Handle private messaging command: /msg <username> <message>
            elif message.startswith('/msg '):
                parts = message.split(' ', 2)
                if len(parts) >= 3:
                    target_user = parts[1]
                    private_msg = parts[2]
                    target_socket = None
                    for sock, name in clients.items():
                        if name == target_user:
                            target_socket = sock
                            break
                    if target_socket:
                        try:
                            target_socket.send(f"[PM from {username}]: {private_msg}\n".encode('utf-8'))
                            client.send(f"[PM to {target_user}]: {private_msg}\n".encode('utf-8'))
                        except:
                            client.send(f"SYSTEM: Error sending private message.\n".encode('utf-8'))
                    else:
                        client.send(f"SYSTEM: User '{target_user}' not found.\n".encode('utf-8'))
            
            # Handle standard public messages within the current room
            else:
                formatted_msg = f"[{username}]: {message}\n"
                broadcast(formatted_msg, client, current_room)

    except Exception as e:
        print(f"[-] Error handling client: {e}")
    finally:
        remove_client(client)

def receive():
    print(f"[*] Server running on port {PORT}...")
    while True:
        client, address = server.accept()
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    receive()
