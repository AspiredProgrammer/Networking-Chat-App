import socket
import threading

# Class Server has a list of clients


class Server:
    Clients = []

    def __init__(self, HOST, PORT, log_file='chat_log.txt'):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))
        self.socket.listen(5)
        print('Server waiting for connection....')

        # File to save chat messages
        self.log_file = log_file

        # Inform server admin that logs are being appended
        print(f"Chat logs will be appended to: {self.log_file}")

    def handle_client_connection(self):
        while True:
            client_socket, address = self.socket.accept()
            print("\nGot connection from %s\n" % str(address))

            # Receive the client name
            client_name = client_socket.recv(1024).decode()
            client = {'client_name': client_name,
                      'client_socket': client_socket}

            # Broadcast message that a new client has connected
            self.send_message_to_clients(
                client_name, client_name + ' has joined the chat!')

            Server.Clients.append(client)
            threading.Thread(target=self.handle_new_message,
                             args=(client,)).start()

    def handle_new_message(self, client):
        client_name = client['client_name']
        client_socket = client['client_socket']
        while True:
            try:
                client_message = client_socket.recv(1024).decode()

                # Checks if the message is a file related request
                if client_message.startswith('FILE:'):
                    file_name = client_message.split(':')[1]
                    self.receive_file(client_socket, file_name)
                    print(f"File '{file_name}' received from {client_name}.")
                    continue

                if client_message.startswith('DOWNLOAD:'):
                    file_name = client_message.split(':')[1]
                    self.send_file_to_client(client_socket, file_name)
                    continue

                print(client_message.strip())

                # Save message on log file
                self.save_message_to_file(client_message.strip())

                # Handle client disconnection
                if client_message.strip() == client_name + ': bye' or not client_message.strip():
                    self.send_message_to_clients(
                        client_name, client_name + ' has left the chat!')
                    self.save_message_to_file(
                        client_name + ' has left the chat!')
                    Server.Clients.remove(client)
                    client_socket.close()
                    break
                else:
                    # Send message to all other clients
                    self.send_message_to_clients(client_name, client_message)
            except ConnectionResetError:
                print(f"Connection with {client_name} lost.")
                Server.Clients.remove(client)
                client_socket.close()
                break

    def send_message_to_clients(self, sender_name, message):
        for client in self.Clients:
            client_socket = client['client_socket']
            client_name = client['client_name']
            if client_name != sender_name:
                client_socket.send(message.encode())

    def receive_file(self, client_socket, file_name):
        try:
            with open(file_name, 'wb') as file:
                while True:
                    file_data = client_socket.recv(1024)
                    if file_data.endswith(b'EOF'):  # End of file marker
                        # Remove 'EOF' and save the remaining data
                        file.write(file_data[:-3])
                        break
                    file.write(file_data)
        except Exception as e:
            print(f"Error receiving file '{file_name}': {str(e)}")

    def send_file_to_client(self, client_socket, file_name):
        try:
            with open(file_name, 'rb') as file:
                while chunk := file.read(1024):
                    client_socket.send(chunk)  # Send file in chunks
                client_socket.send(b'EOF')  # Marks as end of file
            print(f"File '{file_name}' sent to client.")
        except FileNotFoundError:
            # Send error if file not found
            client_socket.send(b"ERROR: File not found.\nEOF")
            print(f"File '{file_name}' not found.")
        except Exception as e:
            # Send generic error
            client_socket.send(b"ERROR: Unable to send file.\nEOF")
            print(f"Error sending file '{file_name}': {str(e)}")

    # Save messages to a file
    def save_message_to_file(self, message):
        with open(self.log_file, 'a') as file:  # Open in append mode
            file.write(message + '\n')


if __name__ == '__main__':
    server = Server('127.0.0.1', 12000)
    server.handle_client_connection()
