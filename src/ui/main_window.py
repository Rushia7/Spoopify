import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QLabel, QFileDialog, QSlider, QMessageBox, QLineEdit, QInputDialog, QAbstractItemView
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

        #top layout
        top_layout = QHBoxLayout()

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search title or artist")
        self.search_bar.textChanged.connect(self.search_music)

        btn_add = QPushButton("➕")
        btn_add.clicked.connect(self.add_files)

        btn_save_playlist = QPushButton("📥")
        btn_save_playlist.clicked.connect(self.save_playlist)
        btn_load_playlist = QPushButton("📤")
        btn_load_playlist.clicked.connect(self.load_playlist)
        btn_delete_playlist = QPushButton("❌")
        btn_delete_playlist.clicked.connect(self.delete_playlist)

        top_layout.addWidget(QLabel("🔍"))
        top_layout.addWidget(self.search_bar)
        top_layout.addWidget(btn_save_playlist)
        top_layout.addWidget(btn_load_playlist)
        top_layout.addWidget(btn_delete_playlist)
        top_layout.addWidget(btn_add)

        main_layout.addLayout(top_layout)

        #song list
        self.song_list_widget = QListWidget()
        self.song_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        main_layout.addWidget(self.song_list_widget)
        self.song_list_widget.itemDoubleClicked.connect(self.play_selected_song)

        self.lbl_now_playing = QLabel("Ready to play")
        self.lbl_now_playing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_now_playing)

        #bot_layout
        controls_layout = QHBoxLayout()
        
        btn_play = QPushButton("▶️")
        btn_play.clicked.connect(self.player.play)

        btn_pause = QPushButton("⏸️")
        btn_pause.clicked.connect(self.player.pause)
        
        btn_stop = QPushButton("⏹️")
        btn_stop.clicked.connect(self.player.stop)

        btn_next = QPushButton("⏭️")
        btn_next.clicked.connect(self.play_next)

        btn_previous = QPushButton("⏮️")
        btn_previous.clicked.connect(self.play_previous)

        btn_shuffle = QPushButton("🔀")
        btn_shuffle.clicked.connect(self.shuffle_songs)

        btn_stats = QPushButton("📊")
        btn_stats.clicked.connect(self.show_statistics)

        controls_layout.addWidget(btn_shuffle)
        controls_layout.addWidget(btn_previous)
        controls_layout.addWidget(btn_play)
        controls_layout.addWidget(btn_pause)
        controls_layout.addWidget(btn_stop)
        controls_layout.addWidget(btn_next)
        controls_layout.addWidget(btn_stats)

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

    def shuffle_songs(self) -> None:
        if self.current_songs:
            random.shuffle(self.current_songs)
            self._refresh_song_list(self.current_songs)

    def play_next(self) -> None:
        current_row = self.song_list_widget.currentRow()
        count = self.song_list_widget.count()

        if count == 0:
            return

        if current_row < count - 1:
            next_row = current_row + 1
            self.song_list_widget.setCurrentRow(next_row)
            self.play_selected_song()
        else:
            self.song_list_widget.setCurrentRow(0)
            self.play_selected_song()

    def play_previous(self) -> None:
        current_row = self.song_list_widget.currentRow()
        count = self.song_list_widget.count()
        previous_row = current_row - 1

        if count == 0:
            return

        if previous_row >= 0:
            self.song_list_widget.setCurrentRow(previous_row)
            self.play_selected_song()
        else:
            self.song_list_widget.setCurrentRow(count - 1)
            self.play_selected_song()

    def save_playlist(self) -> None:
        if not self.current_songs:
            QMessageBox.warning(self, "Error", "List is empty!")
            return
        selected_indexes = self.song_list_widget.selectedIndexes()
        songs_to_save = []
        
        if selected_indexes:
            for index in selected_indexes:
                row = index.row()
                if row < len(self.current_songs):
                    songs_to_save.append(self.current_songs[row])
            
            info_text = f"Save {len(songs_to_save)} selected songs?"
        else:
            songs_to_save = self.current_songs
            info_text = "No songs selected. Save ALL visible songs?"

        name, ok = QInputDialog.getText(self, "Save Playlist", f"{info_text}\nEnter Playlist Name:")
        
        if ok and name:
            song_ids = [song[0] for song in songs_to_save]
            
            success = self.db.create_playlist(name, song_ids)
            if success:
                QMessageBox.information(self, "Success", f"Playlist '{name}' saved with {len(song_ids)} songs!")
            else:
                QMessageBox.warning(self, "Error", "Playlist with this name already exists.")


    def load_playlist(self) -> None:
        playlists = self.db.get_playlists()
        if not playlists:
            QMessageBox.warning(self, "Error", "No playlists found!")
            return
        playlist_names = [playlist[1] for playlist in playlists]
        item, ok = QInputDialog.getItem(self, "Load Playlist", "Choose a playlist:", playlist_names, 0, False)
        if ok and item:
            playlist_id = [p[0] for p in playlists if p[1] == item]
            songs = self.db.get_playlist_songs(playlist_id[0])
            self._refresh_song_list(songs)
            QMessageBox.information(self, "Loaded", f"Loaded playlist '{item}' with {len(songs)} songs.")


    def delete_playlist(self) -> None:
        pass
    def show_statistics(self) -> None:
        pass