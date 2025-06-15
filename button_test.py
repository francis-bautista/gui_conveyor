import customtkinter as ctk
from tkinter import ttk  # For combo boxes
import tkinter as tk

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Four Buttons UI")
        self.geometry("400x300")
        self.resizable(True, True)

        # Configure grid layout (2x2 for buttons)
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        # Create buttons
        self.button1 = ctk.CTkButton(
            self,
            text="Button 1",
            command=self.button1_callback,
            width=150,
            height=50
        )
        self.button1.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.button2 = ctk.CTkButton(
            self,
            text="Button 2",
            command=self.button2_callback,
            width=150,
            height=50
        )
        self.button2.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.button3 = ctk.CTkButton(
            self,
            text="Button 3",
            command=self.button3_callback,
            width=150,
            height=50
        )
        self.button3.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        self.button4 = ctk.CTkButton(
            self,
            text="Button 4",
            command=self.button4_callback,
            width=150,
            height=50
        )
        self.button4.grid(row=1, column=1, padx=20, pady=20, sticky="nsew")

        # Status label to show which button was clicked
        self.status_label = ctk.CTkLabel(
            self,
            text="Click a button!",
            font=ctk.CTkFont(size=16)
        )
        self.status_label.grid(row=2, column=0, columnspan=2, pady=20)

    def button1_callback(self):
        self.status_label.configure(text="Button 1 clicked!")
        print("Button 1 was clicked")

    def button2_callback(self):
        self.status_label.configure(text="Button 2 clicked!")
        print("Button 2 was clicked")

    def button3_callback(self):
        self.status_label.configure(text="Button 3 clicked!")
        print("Button 3 was clicked")

    def button4_callback(self):
        self.status_label.configure(text="Button 4 clicked!")
        print("Button 4 was clicked")

if __name__ == "__main__":
    app = App()
    app.mainloop()