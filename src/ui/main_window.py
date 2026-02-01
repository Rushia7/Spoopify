import os
import random
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QLabel, QFileDialog, QSlider, QMessageBox, 
    QLineEdit, QInputDialog, QAbstractItemView, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtMultimedia import QMediaPlayer
from src.logic.database import Database
from src.logic.player import AudioPlayer
from mutagen.easyid3 import EasyID3

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spoopify - Library & Queue Mode")
        self.resize(1000, 600)

        self.db = Database()
        self.player = AudioPlayer()

        self.player.player.mediaStatusChanged.connect(self.on_media_status_changed)

        self._setup_ui()
        self._refresh_library_list() 

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        #TOP
        top_layout = QHBoxLayout()

        btn_add = QPushButton("📂 Import Songs to Library")
        btn_add.clicked.connect(self.add_files)
        
        btn_stats = QPushButton("📊 Stats")
        btn_stats.clicked.connect(self.show_statistics)

        top_layout.addWidget(btn_add)
        top_layout.addWidget(btn_stats)
        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        #SPLITTER
        splitter = QSplitter(Qt.Orientation.Horizontal)

        #LEFT
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        left_layout.addWidget(QLabel("📚 Library"))
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Library...")
        self.search_bar.textChanged.connect(self.search_music) 
        left_layout.addWidget(self.search_bar)

        self.library_list = QListWidget()
        self.library_list.itemDoubleClicked.connect(self.add_to_queue_and_play)
        left_layout.addWidget(self.library_list)

        btn_add_queue = QPushButton("Add Selection to Queue ➡️")
        btn_add_queue.clicked.connect(self.add_selection_to_queue)
        left_layout.addWidget(btn_add_queue)

        #RIGHT
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        right_layout.addWidget(QLabel("🎶 Queue"))

        #PLAYLIST LAYOUT
        playlist_layout = QHBoxLayout()
        btn_save = QPushButton("💾 Save")
        btn_save.clicked.connect(self.save_playlist)
        btn_load = QPushButton("📂 Load")
        btn_load.clicked.connect(self.load_playlist)
        btn_del = QPushButton("🗑️ Delete")
        btn_del.clicked.connect(self.delete_playlist)
        
        playlist_layout.addWidget(btn_save)
        playlist_layout.addWidget(btn_load)
        playlist_layout.addWidget(btn_del)
        right_layout.addLayout(playlist_layout)

        self.queue_list = QListWidget()
        self.queue_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.queue_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.queue_list.itemDoubleClicked.connect(self.play_from_queue)
        right_layout.addWidget(self.queue_list)

        btn_clear_q = QPushButton("❌ Remove Selected")
        btn_clear_q.clicked.connect(self.remove_from_queue)
        right_layout.addWidget(btn_clear_q)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 550])
        main_layout.addWidget(splitter)

        #DOWN
        self.lbl_now_playing = QLabel("Stopped")
        self.lbl_now_playing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_now_playing)

        controls_layout = QHBoxLayout()
        
        btn_prev = QPushButton("⏮️")
        btn_prev.clicked.connect(self.play_previous)

        btn_play = QPushButton("▶️")
        btn_play.clicked.connect(self.player.play)

        btn_pause = QPushButton("⏸️")
        btn_pause.clicked.connect(self.player.pause)
        
        btn_stop = QPushButton("⏹️")
        btn_stop.clicked.connect(self.player.stop)

        btn_next = QPushButton("⏭️")
        btn_next.clicked.connect(self.play_next)

        btn_shuffle = QPushButton("🔀 Shuffle Queue")
        btn_shuffle.clicked.connect(self.shuffle_queue)

        controls_layout.addWidget(btn_shuffle)
        controls_layout.addWidget(btn_prev)
        controls_layout.addWidget(btn_play)
        controls_layout.addWidget(btn_pause)
        controls_layout.addWidget(btn_stop)
        controls_layout.addWidget(btn_next)

        main_layout.addLayout(controls_layout)

        # VOLUME
        volume_layout = QHBoxLayout()
        lbl_vol = QLabel("Volume:")
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(50)
        self.slider_vol.valueChanged.connect(self.player.set_volume)
        volume_layout.addWidget(lbl_vol)
        volume_layout.addWidget(self.slider_vol)
        main_layout.addLayout(volume_layout)

    
    def on_media_status_changed(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()

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
                    if 'title' in audio: title = audio['title'][0]
                    if 'artist' in audio: artist = audio['artist'][0]
                    if 'genre' in audio: genre = audio['genre'][0]
                except Exception:
                    pass
                self.db.add_song(title, artist, genre, file_path)
                count += 1
            
            self._refresh_library_list()
            QMessageBox.information(self, "Success", f"Added {count} songs!")

    def _refresh_library_list(self, songs_data: list = None) -> None:
        self.library_list.clear()
        if songs_data is None:
            data = self.db.get_all_songs()
        else:
            data = songs_data
        
        for song in data:
            text = f"{song[1]} - {song[2]}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, song)
            self.library_list.addItem(item)

    def search_music(self, text: str) -> None:
        if not text:
            self._refresh_library_list()
        else:
            results = self.db.search_songs(text)
            self._refresh_library_list(results)

    def add_to_queue_and_play(self, item: QListWidgetItem) -> None:
        song_data = item.data(Qt.ItemDataRole.UserRole)
        new_item = self._add_item_to_queue(song_data)
        self.queue_list.setCurrentItem(new_item)
        self.play_from_queue()

    def add_selection_to_queue(self) -> None:
        items = self.library_list.selectedItems()
        for item in items:
            data = item.data(Qt.ItemDataRole.UserRole)
            self._add_item_to_queue(data)

    def _add_item_to_queue(self, song_data) -> QListWidgetItem:
        text = f"{song_data[1]} - {song_data[2]}"
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, song_data)
        self.queue_list.addItem(item)
        return item

    def play_from_queue(self) -> None:
        item = self.queue_list.currentItem()
        if item:
            data = item.data(Qt.ItemDataRole.UserRole) 
            self.lbl_now_playing.setText(f"Playing: {data[1]} - {data[2]}")
            self.player.load_song(data[4])
            self.player.play()
            self.db.increment_play_count(data[0])

    def play_next(self) -> None:
        count = self.queue_list.count()
        if count == 0: return

        row = self.queue_list.currentRow()
        if row < count - 1:
            next_row = row + 1
        else:
            next_row = 0
        
        self.queue_list.setCurrentRow(next_row)
        self.play_from_queue()

    def play_previous(self) -> None:
        count = self.queue_list.count()
        if count == 0: return

        row = self.queue_list.currentRow()
        if row > 0:
            prev_row = row - 1
        else:
            prev_row = count - 1
        
        self.queue_list.setCurrentRow(prev_row)
        self.play_from_queue()

    def shuffle_queue(self) -> None:
        count = self.queue_list.count()
        items_data = []
        for i in range(count):
            items_data.append(self.queue_list.item(i).data(Qt.ItemDataRole.UserRole))
        
        random.shuffle(items_data)
        
        self.queue_list.clear()
        for data in items_data:
            self._add_item_to_queue(data)

    def remove_from_queue(self) -> None:
        selected = self.queue_list.selectedItems()
        for item in selected:
            self.queue_list.takeItem(self.queue_list.row(item))

    def save_playlist(self) -> None:
        count = self.queue_list.count()
        if count == 0:
            QMessageBox.warning(self, "Error", "Queue is empty!")
            return

        name, ok = QInputDialog.getText(self, "Save Playlist", "Enter Playlist Name:")
        if ok and name:
            song_ids = []
            for i in range(count):
                item = self.queue_list.item(i)
                data = item.data(Qt.ItemDataRole.UserRole)
                song_ids.append(data[0])
            
            if self.db.create_playlist(name, song_ids):
                QMessageBox.information(self, "Success", f"Saved '{name}'")
            else:
                QMessageBox.warning(self, "Error", "Name already exists.")

    def load_playlist(self) -> None:
        playlists = self.db.get_playlists()
        if not playlists:
            QMessageBox.information(self, "Info", "No playlists found.")
            return

        names = [p[1] for p in playlists]
        item, ok = QInputDialog.getItem(self, "Load Playlist", "Choose:", names, 0, False)
        
        if ok and item:
            pid = next(p[0] for p in playlists if p[1] == item)
            songs = self.db.get_playlist_songs(pid)
            
            for s in songs:
                self._add_item_to_queue(s)
            
            QMessageBox.information(self, "Loaded", f"Added {len(songs)} songs to Queue.")

    def delete_playlist(self) -> None:
        playlists = self.db.get_playlists()
        if not playlists: return

        names = [p[1] for p in playlists]
        item, ok = QInputDialog.getItem(self, "Delete", "Select:", names, 0, False)
        
        if ok and item:
            playlist_id = [p[0] for p in playlists if p[1] == item]
            self.db.delete_playlist(playlist_id)
            QMessageBox.information(self, "Deleted", f"Playlist '{item}' deleted.")

    def show_statistics(self) -> None:
        report = self.db.get_statistics()
        QMessageBox.information(self, "Statistics", report)