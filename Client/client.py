import socket
import threading
import os
import tkinter as tk
from tkinter import scrolledtext, simpledialog, filedialog


class Client:
    def __init__(self, HOST, PORT):
        self.socket = socket.socket()
        self.socket.connect((HOST, PORT))

        # Setup tkinter GUI
        # Chat client main window application
        self.root = tk.Tk()
        self.root.title("Chat Client")

        #Chat window, white text area
        self.chat_window = scrolledtext.ScrolledText(
            self.root, state='disabled', wrap=tk.WORD, width=50, height=20)
        self.chat_window.pack(padx=10, pady=10)
        self.chat_window.tag_config("green", foreground="green")
        self.chat_window.tag_config("right", justify="right")

        self.user_listbox = tk.Listbox(self.root, height=10, width=30)
        self.user_listbox.pack(padx=10, pady=5, side=tk.RIGHT)

        #Input text
        self.message_input = tk.Entry(self.root, width=40)
        self.message_input.pack(padx=10, pady=5, side=tk.LEFT)
        self.message_input.bind("<Return>", self.send_message)# OnClick on the Enter key, it triggers the send_message

        #Send button
        self.send_button = tk.Button(
            self.root, text="Send", command=self.send_message_event)
        self.send_button.pack(pady=5, padx=5, side=tk.LEFT)
        self.file_button = tk.Button(
            self.root, text="Send File", command=self.send_file)
        self.file_button.pack(pady=5, padx=5, side=tk.LEFT)
        self.download_button = tk.Button(
            self.root, text="Download File", command=self.download_file)
        self.download_button.pack(pady=5, padx=5, side=tk.LEFT)

        self.exit_button = tk.Button(
            self.root, text="Exit", command=self.on_close)
        self.exit_button.pack(pady=5, padx=5, side=tk.RIGHT)

        # update the GUI with the component
        self.root.update()

        # Ask user for name
        self.name = simpledialog.askstring(
            "Name", "Enter your name:", parent=self.root)
        if not self.name:
            self.name = "Anonymous"
        self.root.title("Chat Client: " + self.name)

        self.handle_server_connection()

    def handle_server_connection(self):
        self.socket.send(self.name.encode())
        threading.Thread(target=self.receive_message, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)# when close the main window application, end the connection with server
        self.root.mainloop()

    #Define that the button is clickable and "None" there is no default message
    def send_message_event(self):
        self.send_message(None)

    def send_message(self, event):
        client_input = self.message_input.get()
        if client_input.strip():
            client_message = self.name + ": " + client_input
            # Add client message to the chat box before send it to the server socket
            # Put the client message to the right and green color
            self.display_message(client_message, "green", "right")
            self.socket.send(client_message.encode())
            self.message_input.delete(0, tk.END)#Clean input text after sending message

    def receive_message(self):
        while True:
            try:
                server_message = self.socket.recv(1024).decode()

                # Detect user list message
                if server_message.startswith("USERS:"):
                    user_list = server_message[6:].split(",")
                    self.update_user_list(user_list)
                    continue

                # Detect server error message
                if server_message.startswith("ERROR:"):
                    self.display_message(server_message, "red")
                    continue

                # Process regular messages
                self.display_message(server_message)
            except ConnectionResetError:
                break
        self.on_close()

    def update_user_list(self, user_list):
        # Clear the current list
        self.user_listbox.delete(0, tk.END)
        # Populate with updated user list
        for user in user_list:
            self.user_listbox.insert(tk.END, user)

    def send_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                file_name = os.path.basename(file_path)
                with open(file_path, 'rb') as file:
                    file_data = file.read()

                self.socket.send(f'FILE:{file_name}'.encode())
                self.socket.sendall(file_data)
                self.socket.send(b'EOF')

                self.display_message(
                    f"File '{file_name}' sent successfully!", "green", "right")
            except Exception as e:
                self.display_message(
                    f"Error sending file: {str(e)}", "red", "right")

    def download_file(self):
        file_name = simpledialog.askstring(
            "Download File", "Enter the name of the file to download:", parent=self.root)
        if file_name:
            try:
                self.socket.send(f"DOWNLOAD:{file_name}".encode())

                with open(file_name, 'wb') as file:
                    while True:
                        file_data = self.socket.recv(1024)
                        if file_data.endswith(b'EOF'):
                            file.write(file_data[:-3])
                            break
                        file.write(file_data)

                self.display_message(
                    f"File '{file_name}' downloaded successfully!", "green", "right")
            except Exception as e:
                self.display_message(
                    f"Error downloading file: {str(e)}", "red", "right")

    def display_message(self, message, color=None, align="left"):
        self.chat_window.config(state='normal')

        # Determine the tags (tag_config in the init) to apply
        tags = []
        if color:
            tags.append(color)
        if align:
            tags.append(align)

         # Insert the message with the specified tags
        self.chat_window.insert(tk.END, message + '\n', tuple(tags))
        self.chat_window.config(state='disabled')
        self.chat_window.see(tk.END)

    def on_close(self):
        try:
            self.socket.send(f"{self.name}: bye".encode())
            self.socket.close()
        except Exception:
            pass
        self.root.destroy()
        os._exit(0)


if __name__ == '__main__':
    Client('127.0.0.1', 12000)




    ##127.0.0.1 /192.168.1.208
