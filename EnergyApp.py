import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random

class Room:
    """Klasse til at repræsentere et rum og dets strømforbrug på tre faser"""
    def __init__(self, name, sockets=1):
        self.name = name
        self.sockets = sockets  # Antal stikkontakter
        self.phase1 = 0
        self.phase2 = 0
        self.phase3 = 0
        # DataFrame til at logge historisk forbrug per fase
        self.history = pd.DataFrame(columns=['Time', 'Phase1', 'Phase2', 'Phase3'])

    def update_usage(self, phase1, phase2, phase3):
        """Opdater strømforbrug og log i history"""
        self.phase1 = phase1
        self.phase2 = phase2
        self.phase3 = phase3
        # Log tidspunkt og faseforbrug
        self.history = pd.concat([self.history, pd.DataFrame({
            'Time': [datetime.now()],
            'Phase1': [phase1],
            'Phase2': [phase2],
            'Phase3': [phase3]
        })], ignore_index=True)

class PowerMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Strømovervågning")
        self.rooms = {}  # Ordbog til at holde styr på de forskellige rum
        self.warning_threshold = 300  # Advarselsgrænse i watt

        # UI Setup
        self.room_frame = tk.Frame(root)
        self.room_frame.pack(pady=10)

        # Standardrum med dropdown til antal stikkontakter
        self.add_default_rooms()

        # Indstillingsfelt for advarselsgrænse
        self.warning_label = tk.Label(root, text="Indstil advarselsgrænse (W):")
        self.warning_label.pack()
        self.warning_entry = tk.Entry(root)
        self.warning_entry.insert(0, str(self.warning_threshold))  # Sætter standardværdi
        self.warning_entry.pack()

        # Knap til manuel opdatering af alle rums forbrug
        self.update_button = tk.Button(root, text="Opdater strømforbrug", command=self.update_all_rooms)
        self.update_button.pack(pady=10)

        # Filtrering: Vælg rum og fase til grafer
        self.filter_label = tk.Label(root, text="Vælg rum og fase til grafer:")
        self.filter_label.pack()
        
        # Dropdown-menu til valg af rum
        self.room_filter = ttk.Combobox(root, values=list(self.rooms.keys()), state="readonly")
        self.room_filter.pack()
        self.room_filter.bind("<<ComboboxSelected>>", self.update_phase_filter)  # Opdater faser ved valg af rum
        
        # Dropdown-menu til valg af fase (Phase 1, Phase 2, Phase 3)
        self.phase_filter = ttk.Combobox(root, values=["Phase 1", "Phase 2", "Phase 3"], state="readonly")
        self.phase_filter.pack()

        # Knap til visning af grafer
        self.graph_button = tk.Button(root, text="Vis grafer", command=self.plot_filtered_data)
        self.graph_button.pack(pady=10)

        # Knap til at lukke programmet
        self.quit_button = tk.Button(root, text="Luk program", command=root.quit)
        self.quit_button.pack(pady=10)

        # Vis alle nuværende rum
        self.display_rooms()

    def add_default_rooms(self):
        """Opret standardrum og tilføj widgets til valg af stikkontakter"""
        default_rooms = ["Køkken", "Stue", "Soveværelse", "Badeværelse"]
        
        for room_name in default_rooms:
            # Initialiser med 1 stikkontakt som standard
            self.rooms[room_name] = Room(room_name, sockets=1)

            # UI-element til at vælge antal stikkontakter for hvert standardrum
            frame = tk.Frame(self.room_frame)
            frame.grid(row=len(self.rooms), column=0, sticky="w", padx=10, pady=5)
            
            label = tk.Label(frame, text=f"{room_name}:")
            label.grid(row=0, column=0, padx=10)

            # Dropdown-menu til valg af antal stikkontakter
            socket_menu = ttk.Combobox(frame, values=[1, 2, 3, 4, 5], state="readonly")
            socket_menu.current(0)  # Vælg standard 1 stikkontakt
            socket_menu.grid(row=0, column=1, padx=10)
            
            # Bind dropdown-valg til en funktion, der opdaterer antal stikkontakter
            socket_menu.bind("<<ComboboxSelected>>", lambda event, room=room_name, menu=socket_menu: self.set_sockets(room, menu))

    def set_sockets(self, room_name, menu):
        """Opdater antal stikkontakter for et specifikt rum"""
        sockets = int(menu.get())
        self.rooms[room_name].sockets = sockets
        messagebox.showinfo("Opdatering", f"Antal stikkontakter i {room_name} sat til {sockets}")

    def display_rooms(self):
        """Vis alle rum og deres strømforbrug"""
        # Fjern tidligere visning
        for widget in self.room_frame.winfo_children():
            widget.destroy()

        # Tilføj header
        header_frame = tk.Frame(self.room_frame)
        header_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Label(header_frame, text="Rum", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10)
        tk.Label(header_frame, text="Stikkontakter", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10)
        tk.Label(header_frame, text="Strømforbrug (W)", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=10)

        # Vis hvert rum med data
        for idx, (room_name, room) in enumerate(self.rooms.items(), start=1):
            frame = tk.Frame(self.room_frame)
            frame.grid(row=idx, column=0, sticky="w", padx=10, pady=5)

            tk.Label(frame, text=room_name).grid(row=0, column=0, padx=10)
            tk.Label(frame, text=str(room.sockets)).grid(row=0, column=1, padx=10)

            # Format strømforbrug pr. fase og total
            power_usage = f"Fase 1: {room.phase1}W\nFase 2: {room.phase2}W\nFase 3: {room.phase3}W"
            tk.Label(frame, text=power_usage).grid(row=0, column=2, padx=10)

            # Hvis strømforbruget overskrider grænsen, vis advarsel
            if max(room.phase1, room.phase2, room.phase3) > self.warning_threshold:
                tk.Label(frame, text="⚠️ Højt forbrug!", fg="red").grid(row=0, column=3, padx=10)

    def update_all_rooms(self):
        """Opdater strømforbrug for alle rum og tjek for advarsler"""
        try:
            self.warning_threshold = int(self.warning_entry.get())
        except ValueError:
            messagebox.showerror("Fejl", "Indtast venligst et gyldigt tal for advarselsgrænsen.")
            return

        # Opdater forbruget for hvert rum og vis advarsler hvis relevant
        for room in self.rooms.values():
            phase1 = random.randint(0, 500) * room.sockets
            phase2 = random.randint(0, 500) * room.sockets
            phase3 = random.randint(0, 500) * room.sockets
            room.update_usage(phase1, phase2, phase3)

        self.display_rooms()

    def update_phase_filter(self, event):
        """Opdater fasevalg afhængigt af valgt rum"""
        room_name = self.room_filter.get()
        if room_name in self.rooms:
            self.phase_filter['values'] = ["Phase 1", "Phase 2", "Phase 3"]
        else:
            self.phase_filter['values'] = []

    def plot_filtered_data(self):
        """Vis filtrerede grafer af strømforbrug baseret på brugerens valg"""
        room_name = self.room_filter.get()
        phase = self.phase_filter.get()

        if room_name in self.rooms:
            room = self.rooms[room_name]
            phase_data = room.history[phase]  # Fase specifik data
            room.history['Time'] = pd.to_datetime(room.history['Time'])
            plt.plot(room.history['Time'], phase_data, label=f"{room_name} - {phase}")
            plt.xlabel('Tid')
            plt.ylabel('Forbrug (W)')
            plt.title(f"Strømforbrug for {room_name} - {phase}")
            plt.legend()
            plt.show()

# Kør applikationen
root = tk.Tk()
app = PowerMonitorApp(root)
root.mainloop()
