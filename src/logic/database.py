import sqlite3

class Database:
    def __init__(self, db_name: str = "music_player.db") -> None:
        self.db_name = db_name
        self._create_tables()
    
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

    def increment_play_count(self, song_id: int) -> None:
        query = "UPDATE songs SET play_count = play_count + 1 WHERE id = ?"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (song_id,))
            conn.commit()

    def search_songs(self, search: str) -> list[tuple]:
        search_term = f"%{search}%"
        sql = """
        SELECT id, title, artist, genre, file_path, play_count 
        FROM songs 
        WHERE title LIKE ? OR artist LIKE ?
        """

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (search_term, search_term))
            return cursor.fetchall()
    
    def create_playlist(self, name: str, song_ids: list[int]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
                playlist_id = cursor.lastrowid
                for song_id in song_ids:
                    cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", (playlist_id, song_id))
                conn.commit()
                return True
            except sqlite3.IntegrityError: #If paylist name exists
                return False

    def get_playlists(self) -> list[tuple]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM playlists")
            return cursor.fetchall()

    def get_playlist_songs(self, playlist_id: int) -> list[tuple]:
        query = """
        SELECT s.id, s.title, s.artist, s.genre, s.file_path, s.play_count
        FROM songs s
        JOIN playlist_songs link ON s.id = link.song_id
        WHERE link.playlist_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (playlist_id,))
            return cursor.fetchall()

    def delete_playlist(self, playlist_id: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM playlist_songs WHERE playlist_id = ?", (playlist_id,))
            cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
            conn.commit()
    
    def get_statistics(self) -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title, artist, play_count FROM songs ORDER BY play_count DESC LIMIT 1")
            top_song = cursor.fetchone()

            cursor.execute("""
                SELECT artist, SUM(play_count) as total 
                FROM songs 
                WHERE artist != 'Unknown Artist' 
                GROUP BY artist 
                ORDER BY total DESC LIMIT 1
            """)
            top_artist = cursor.fetchone()

            lines = ["📊  --- СТАТИСТИКА ---  📊\n"]
            
            if top_song and top_song[2] > 0:
                lines.append(f"🎵 Най-слушана песен:\n{top_song[0]} - {top_song[1]} ({top_song[2]} слушания)")
            else:
                lines.append("🎵 Най-слушана песен: Няма данни.")

            if top_artist and top_artist[1] > 0:
                lines.append(f"\n🎤 Любим изпълнител:\n{top_artist[0]} ({top_artist[1]} слушания)")
            else:
                lines.append("\n🎤 Любим изпълнител: Няма данни.")
            
            return "\n".join(lines)
