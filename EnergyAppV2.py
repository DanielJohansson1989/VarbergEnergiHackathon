import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import random
import os

class Room:
    """Klasse til at repræsentere et rum og dets strømforbrug på tre faser"""
    def __init__(self, name, sockets=1):
        self.name = name
        self.sockets = sockets  # Antal stikkontakter
        self.phase1 = 0
        self.phase2 = 0
        self.phase3 = 0
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

    def load_data_from_csv(self, csv_file):
        """Aflæs data fra CSV-fil og opdater historik"""
        try:
            # Læs CSV med pandas og fjern ekstra mellemrum fra kolonneoverskrifter
            df = pd.read_csv(csv_file)
            df.columns = df.columns.str.strip()  # Fjern ekstra mellemrum fra kolonnenavne
            
            # Kontroller, at nødvendige kolonner eksisterer
            required_columns = ['Time', 'Phase1', 'Phase2', 'Phase3']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Kolonnen '{col}' mangler i CSV-filen.")
            
            # Konverter tidskolonnen til datetime
            df['Time'] = pd.to_datetime(df['Time'])
            
            # Opdater historikken
            self.history = df

            print(f"Data importeret succesfuldt fra {csv_file}")
        except ValueError as ve:
            messagebox.showerror("Fejl", f"Fejl ved indlæsning af CSV-fil: {ve}")
        except Exception as e:
            messagebox.showerror("Fejl", f"Kunne ikke importere CSV-fil: {str(e)}")


class PowerMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Strømovervågning")
        self.rooms = {}  # Ordbog til at holde styr på de forskellige rum
        self.warning_threshold = 300  # Advarselsgrænse i watt

        # UI Setup
        self.room_frame = tk.Frame(root)
        self.room_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        # Kald add_default_rooms fra __init__-metoden
        self.add_default_rooms()

        # Indstillingsfelt for advarselsgrænse
        self.warning_label = tk.Label(root, text="Indstil advarselsgrænse (W):")
        self.warning_label.grid(row=1, column=0, pady=5, sticky="ew")
        
        self.warning_entry = tk.Entry(root)
        self.warning_entry.insert(0, str(self.warning_threshold))  # Sætter standardværdi
        self.warning_entry.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        # Knap til manuel opdatering af alle rums forbrug
        self.update_button = tk.Button(root, text="Opdater strømforbrug", command=self.update_all_rooms)
        self.update_button.grid(row=3, column=0, pady=10, sticky="ew")

        # Knap til at importere CSV-data
        self.import_button = tk.Button(root, text="Importer CSV-data", command=self.import_csv)
        self.import_button.grid(row=4, column=0, pady=10, sticky="ew")

        # Filtrering: Vælg rum og fase til grafer
        self.filter_label = tk.Label(root, text="Vælg rum og fase til grafer:")
        self.filter_label.grid(row=5, column=0, pady=5, sticky="ew")

        # Dropdown-menu til valg af rum
        self.room_filter = ttk.Combobox(root, values=list(self.rooms.keys()), state="readonly")
        self.room_filter.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        self.room_filter.bind("<<ComboboxSelected>>", self.update_phase_filter)  # Opdater faser ved valg af rum
        
        # Dropdown-menu til valg af fase (Phase 1, Phase 2, Phase 3)
        self.phase_filter = ttk.Combobox(root, values=["Phase 1", "Phase 2", "Phase 3"], state="readonly")
        self.phase_filter.grid(row=7, column=0, padx=10, pady=5, sticky="ew")

        # Knap til visning af grafer
        self.graph_button = tk.Button(root, text="Vis grafer", command=self.plot_filtered_data)
        self.graph_button.grid(row=8, column=0, pady=10, sticky="ew")

        # Knap til at lukke programmet
        self.quit_button = tk.Button(root, text="Luk program", command=root.quit)
        self.quit_button.grid(row=9, column=0, pady=10, sticky="ew")

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
            frame.grid(row=len(self.rooms), column=1, sticky="w", padx=10, pady=5)

            label = tk.Label(frame, text=f"{room_name}:")
            label.grid(row=0, column=0, padx=10, sticky="w")

            # Dropdown-menu til valg af antal stikkontakter
            socket_menu = ttk.Combobox(frame, values=[1, 2, 3, 4, 5], state="readonly")
            socket_menu.set('1')  # Sæt standardværdien til 1 (kan ændres, afhængigt af krav)
            socket_menu.grid(row=11, column=1, padx=10, sticky="w")
            
            # Bind dropdown-valg til en funktion, der opdaterer antal stikkontakter
            socket_menu.bind("<<ComboboxSelected>>", lambda event, room=room_name, menu=socket_menu: self.set_sockets(room, menu))

    def set_sockets(self, room_name, menu):
        """Opdater antal stikkontakter for et specifikt rum"""
        try:
            sockets = int(menu.get())
            self.rooms[room_name].sockets = sockets
            messagebox.showinfo("Opdatering", f"Antal stikkontakter i {room_name} sat til {sockets}")
        except ValueError:
            messagebox.showerror("Fejl", f"Ugyldigt antal stikkontakter for {room_name}. Prøv igen.")

    def display_rooms(self):
        """Vis alle rum og deres strømforbrug"""
        # Fjern tidligere visning
        for widget in self.room_frame.winfo_children():
            widget.destroy()

        # Tilføj header
        header_frame = tk.Frame(self.room_frame)
        header_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=5)
        tk.Label(header_frame, text="Rum", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, sticky="w")
        tk.Label(header_frame, text="Stikkontakter", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10, sticky="w")
        tk.Label(header_frame, text="Strømforbrug", font=("Arial", 12, "bold")).grid(row=0, column=2, padx=10, sticky="w")

        # Vis hvert rum med info om forbrug og antal stikkontakter
        for idx, room in enumerate(self.rooms.values()):
            frame = tk.Frame(self.room_frame)
            frame.grid(row=idx + 1, column=1, sticky="ew", padx=10, pady=5)

            tk.Label(frame, text=room.name).grid(row=0, column=0, padx=10, sticky="w")
            tk.Label(frame, text=room.sockets).grid(row=0, column=1, padx=10, sticky="w")
            tk.Label(frame, text=f"Phase 1: {room.phase1} W, Phase 2: {room.phase2} W, Phase 3: {room.phase3} W").grid(row=0, column=2, padx=10, sticky="w")

    def update_all_rooms(self):
        """Opdater strømforbrug for alle rum"""
        for room in self.rooms.values():
            room.update_usage(random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))

        self.display_rooms()

    def import_csv(self):
        """Importer data fra CSV-fil"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            for room in self.rooms.values():
                room.load_data_from_csv(file_path)

    def update_phase_filter(self, event):
        """Opdater fase dropdown-menu baseret på valgt rum"""
        room_name = self.room_filter.get()
        room = self.rooms[room_name]
        # Fasevalget bliver aktiveret uanset hvad
        self.phase_filter.set("Phase 1")  # For at sikre, at der er en valgt fase i starten

    def plot_filtered_data(self):
        """Plot graf baseret på det valgte rum og fase"""
        room_name = self.room_filter.get()
        phase_name = self.phase_filter.get()

        if room_name and phase_name:
            room = self.rooms[room_name]
            if phase_name == "Phase 1":
                data = room.history[['Time', 'Phase1']]
                data.set_index('Time', inplace=True)
                data.plot(title=f"Strømforbrug for {room_name} - {phase_name}")
            elif phase_name == "Phase 2":
                data = room.history[['Time', 'Phase2']]
                data.set_index('Time', inplace=True)
                data.plot(title=f"Strømforbrug for {room_name} - {phase_name}")
            elif phase_name == "Phase 3":
                data = room.history[['Time', 'Phase3']]
                data.set_index('Time', inplace=True)
                data.plot(title=f"Strømforbrug for {room_name} - {phase_name}")
            plt.show()

# Opsætning af GUI og applikation
if __name__ == "__main__":
    root = tk.Tk()
    app = PowerMonitorApp(root)
    root.mainloop()
