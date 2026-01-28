import sqlite3

class Database:
    def __init__(self, db_name: str = "music_player.db") -> None:
        self.db_name = db_name
    
    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_name)

    def _create_tables(self) -> None:
        query_songs = """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT,
            genre TEXT,
            file_path TEXT NOT NULL UNIQUE,
            play_count INTEGER DEFAULT 0
        );
        """

        query_playlists = """
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """

        query_playlist_songs = """
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INTEGER,
            song_id INTEGER,
            FOREIGN KEY(playlist_id) REFERENCES playlists(id),
            FOREIGN KEY(song_id) REFERENCES songs(id)
        );
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query_songs)
            cursor.execute(query_playlists)
            cursor.execute(query_playlist_songs)
            conn.commit()
    
    def add_song(self, title: str, artist: str, genre: str, file_path: str) -> None:
        query = """
        INSERT OR IGNORE INTO songs (title, artist, genre, file_path)
        VALUES (?, ?, ?, ?)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (title, artist, genre, file_path))
            conn.commit()

    def get_all_songs(self) -> list[tuple]:
        query = "SELECT id, title, artist, genre, file_path, play_count FROM songs"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()

    def increment_play_count(self):
        query = "UPDATE songs SET play_count = play_count + 1 WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (song_id,))
            conn.commit()