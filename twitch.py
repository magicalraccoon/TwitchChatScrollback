import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import socket
import threading
from pynput import keyboard, mouse
from dotenv import load_dotenv
import os


# Ensure the .env file exists and create it if missing
def ensure_env_file():
    """Check for .env file and create it if it doesn't exist."""
    if not os.path.exists('.env'):
        with open('.env', 'w') as env_file:
            env_file.write("TWITCH_OAUTH_TOKEN=oauth:your_twitch_oauth_token\n")
            env_file.write("TWITCH_USERNAME=your_twitch_username\n")
            env_file.write("CHANNEL=channel to observe")
        print(".env file created. Please edit it with your Twitch credentials.")
        return False
    return True


# Load environment variables
if ensure_env_file():
    load_dotenv()
else:
    messagebox.showerror("Error", ".env file created. Edit it and restart the program.")
    exit()

# Twitch IRC Connection Details
SERVER = "irc.chat.twitch.tv"
PORT = 6667
OAUTH_TOKEN = os.getenv("TWITCH_OAUTH_TOKEN")  # Replace with your token in the .env file. Include oauth: prefix
USERNAME = os.getenv("TWITCH_USERNAME")  # Replace with your Twitch username in the .env file
CHANNEL = os.getenv("CHANNEL")

if not OAUTH_TOKEN or not USERNAME:
    messagebox.showerror("Error", "Missing credentials in the .env file. Please add your Twitch OAuth Token, "
                                  "Username, and Channel to observe.")
    exit()


def connect_to_twitch():
    """Establish connection to Twitch IRC."""
    try:
        irc = socket.socket()
        irc.connect((SERVER, PORT))
        irc.send(f"PASS {OAUTH_TOKEN}\n".encode('utf-8'))
        irc.send(f"NICK {USERNAME}\n".encode('utf-8'))
        irc.send(f"JOIN #{CHANNEL}\n".encode('utf-8'))
        return irc
    except Exception as e:
        print(f"Failed to connect to Twitch: {e}")
        return None


def listen_to_chat(irc, chat_display, auto_scroll_flag):
    """Continuously listen for chat messages and update the display."""
    bots = ["nightbot", "moobot", "streamelements"]
    colors = ["#f0f0f0", "#d0d0d0"]  # Alternating message background colors
    message_count = 0

    while True:
        try:
            response = irc.recv(2048).decode("utf-8")
            if response.startswith("PING"):
                irc.send("PONG :tmi.twitch.tv\n".encode("utf-8"))
            else:
                parts = response.split(":", 2)
                if len(parts) > 2 and "PRIVMSG" in parts[1]:
                    user = parts[1].split("!")[0]
                    message = parts[2]
                    if user.lower() not in bots:
                        # Schedule the chat update in the main thread
                        chat_display.after(0, update_chat_display, chat_display, user, message, message_count, colors, auto_scroll_flag)
                        message_count += 1
        except Exception as e:
            print(f"Error in chat listener: {e}")
            break


def update_chat_display(chat_display, user, message, message_count, colors, auto_scroll_flag):
    """Update the chat display in the main thread."""
    chat_display.config(state=tk.NORMAL)
    chat_display.insert(
        tk.END,
        f"{user}: {message[:-2]} \n",
        (f"color{message_count % 2}",),
    )
    chat_display.tag_configure(
        f"color{message_count % 2}",
        background=colors[message_count % 2],
    )

    # Auto-scroll if enabled
    if auto_scroll_flag[0]:
        chat_display.see(tk.END)

    chat_display.config(state=tk.DISABLED)


def start_global_input_listener(chat_display, auto_scroll_flag):
    """Start global input listeners for mouse and keyboard hotkeys."""
    is_shift_pressed = [False]  # Track the Shift key state

    def on_key_press(key):
        """Handle global key press events."""
        try:
            if key == keyboard.Key.shift_r:  # Right Shift toggles auto-scroll
                auto_scroll_flag[0] = not auto_scroll_flag[0]
                print(
                    "Auto-scroll enabled." if auto_scroll_flag[0] else "Auto-scroll paused."
                )
            elif key == keyboard.Key.shift:  # Track Shift state for scrolling
                is_shift_pressed[0] = True
        except Exception as e:
            print(f"Key Error: {e}")

    def on_key_release(key):
        """Handle global key release events."""
        if key == keyboard.Key.shift:
            is_shift_pressed[0] = False

    def on_scroll(x, y, dx, dy):
        """Handle global mouse scroll events."""
        if not auto_scroll_flag[0] and is_shift_pressed[0]:
            if dy > 0:  # Scroll up
                chat_display.yview_scroll(-1, "units")
            elif dy < 0:  # Scroll down
                chat_display.yview_scroll(1, "units")

    # Start listeners for keyboard and mouse
    key_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
    mouse_listener = mouse.Listener(on_scroll=on_scroll)

    key_listener.start()
    mouse_listener.start()


def start_chat_window():
    """Create and start the GUI for displaying chat messages."""
    root = tk.Tk()
    root.title("Twitch Chat Viewer")
    root.geometry("500x400")
    root.attributes("-topmost", True)  # Keep the window always on top
    root.attributes("-alpha", 0.8)  # Semi-transparent window (80% opacity)

    # Set a dark background color (black or gray for a "transparent" look)
    root.configure(bg='#2c2f33')  # Dark gray background to simulate transparency

    # Create a scrollable text widget with a transparent-like effect
    chat_display = ScrolledText(
        root,
        state=tk.DISABLED,
        wrap=tk.WORD,
        borderwidth=0,
        highlightthickness=0,  # No borders
    )
    chat_display.pack(expand=True, fill=tk.BOTH)

    # Auto-scroll flag
    auto_scroll_flag = [True]  # Use a mutable object to share state between threads

    # Connect to Twitch and start listening
    irc = connect_to_twitch()
    if irc:
        threading.Thread(target=listen_to_chat, args=(irc, chat_display, auto_scroll_flag), daemon=True).start()

        # Start global input listeners
        start_global_input_listener(chat_display, auto_scroll_flag)

        # Run the Tkinter event loop
        root.mainloop()
    else:
        print("Failed to connect to Twitch. Exiting...")


if __name__ == "__main__":
    start_chat_window()
