import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QFileDialog, QSlider, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt
from src.logic.database import Database
from src.logic.player import AudioPlayer
from mutagen.easyid3 import EasyID3
import random

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spoopify")
        self.resize(600, 400)

        self.db = Database()
        self.player = AudioPlayer()

        self.current_songs: list[tuple] = []
        self._setup_ui()
        self._refresh_song_list()

    def _setup_ui(self) -> None:
        #central widget, main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        #search
        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search title or artist")
        self.search_bar.textChanged.connect(self.search_music)
        search_layout.addWidget(QLabel("🔍"))
        search_layout.addWidget(self.search_bar)
        main_layout.addLayout(search_layout)

        #song list
        self.song_list_widget = QListWidget()
        main_layout.addWidget(self.song_list_widget)
        self.song_list_widget.itemDoubleClicked.connect(self.play_selected_song)

        self.lbl_now_playing = QLabel("Ready to play")
        self.lbl_now_playing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_now_playing)

        #main buttons
        controls_layout = QHBoxLayout()

        btn_add = QPushButton("➕")
        btn_add.clicked.connect(self.add_files)
        
        btn_play = QPushButton("▶️")
        btn_play.clicked.connect(self.player.play)

        btn_pause = QPushButton("⏸️")
        btn_pause.clicked.connect(self.player.pause)
        
        btn_stop = QPushButton("⏹️")
        btn_stop.clicked.connect(self.player.stop)

        btn_next = QPushButton("⏭️")
        btn_previous = QPushButton("⏮️")

        btn_shuffle = QPushButton("🔀")
        btn_shuffle.clicked.connect(self.shuffle_songs)


        controls_layout.addWidget(btn_add)
        controls_layout.addWidget(btn_shuffle)
        controls_layout.addWidget(btn_previous)
        controls_layout.addWidget(btn_play)
        controls_layout.addWidget(btn_pause)
        controls_layout.addWidget(btn_stop)
        controls_layout.addWidget(btn_next)

        main_layout.addLayout(controls_layout)

        #volume
        volume_layout = QHBoxLayout()
        lbl_vol = QLabel("Volume:")
        
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.slider_vol.valueChanged.connect(self.player.set_volume)
        
        volume_layout.addWidget(lbl_vol)
        volume_layout.addWidget(self.slider_vol)
        main_layout.addLayout(volume_layout)

    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Songs", os.path.expanduser("~"), "Audio (*.mp3 *.wav)"
        )
        
        if files:
            count = 0
            for file_path in files:
                filename = os.path.basename(file_path)
                title = os.path.splitext(filename)[0]
                artist = "Unknown Artist"
                genre = "Unknown Genre"

                try:
                    audio = EasyID3(file_path)
                    if 'title' in audio:
                        title = audio['title'][0]
                    if 'artist' in audio:
                        artist = audio['artist'][0]
                    if 'genre' in audio:
                        genre = audio['genre'][0]
                except Exception:
                    pass

                self.db.add_song(title, artist, genre, file_path)
                count += 1
            
            self._refresh_song_list()
            QMessageBox.information(self, "Success", f"Added {count} songs with metadata!")

    def _refresh_song_list(self, songs_data: list = None) -> None:
        self.song_list_widget.clear()

        if songs_data == None:
            self.current_songs = self.db.get_all_songs()
        else:
            self.current_songs = songs_data
        
        for song in self.current_songs:
            name_artist = f"{song[1]} - {song[2]}"
            self.song_list_widget.addItem(name_artist)

    def play_selected_song(self) -> None:
        row = self.song_list_widget.currentRow()
        if row >= 0 and row < len(self.current_songs):
            song_data = self.current_songs[row]

        song_id = song_data[0]
        title = song_data[1]
        file_path = song_data[4]

        self.lbl_now_playing.setText(f"Playing: {title}")

        self.player.load_song(file_path)
        self.player.play()

        self.db.increment_play_count(song_id)
    
    def search_music(self, text: str) -> None:
        if not text:
            self._refresh_song_list()
        else:
            results = self.db.search_songs(text)
            self._refresh_song_list(results)

    def shuffle_songs(self):
        if self.current_songs:
            random.shuffle(self.current_songs)
            self._refresh_song_list(self.current_songs)