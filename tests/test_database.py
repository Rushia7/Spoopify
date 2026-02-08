import pytest
import sqlite3
import os
from src.logic.database import Database

# --- ПОДГОТОВКА (FIXTURE) ---
@pytest.fixture
def db():
    """
    Създава временен файл с база данни за всеки тест.
    Използваме файл, защото твоят клас Database затваря връзката
    след всяка заявка, което би изтрило :memory: база веднага.
    """
    test_db_name = "test_music_full.db"
    
    # Почистване преди теста
    if os.path.exists(test_db_name):
        os.remove(test_db_name)
    
    database = Database(test_db_name)
    yield database
    
    # Почистване след теста
    if os.path.exists(test_db_name):
        os.remove(test_db_name)

# --- ТЕСТОВЕ ЗА ПЕСНИ (SONGS) ---

def test_add_and_get_song(db):
    """Сценарий: Успешно добавяне и четене на песен."""
    db.add_song("Title A", "Artist A", "Pop", "/path/a.mp3")
    
    songs = db.get_all_songs()
    assert len(songs) == 1
    # songs[0] -> (id, title, artist, genre, path, play_count)
    assert songs[0][1] == "Title A"
    assert songs[0][4] == "/path/a.mp3"
    assert songs[0][5] == 0  # Play count трябва да е 0

def test_add_duplicate_song_path(db):
    """Сценарий: Защита от дублиране (UNIQUE file_path)."""
    db.add_song("Song 1", "Artist 1", "Pop", "/same/path.mp3")
    # Опитваме да добавим същия файл пак
    db.add_song("Song 1 New", "Artist 1", "Pop", "/same/path.mp3")
    
    songs = db.get_all_songs()
    # Трябва да има само 1 запис (първия)
    assert len(songs) == 1
    assert songs[0][1] == "Song 1"

def test_search_songs(db):
    """Сценарий: Търсене (точно, частично, празно)."""
    db.add_song("Yellow Submarine", "The Beatles", "Rock", "/p/1")
    db.add_song("Yellow", "Coldplay", "Pop", "/p/2")
    
    # Частично търсене
    assert len(db.search_songs("Yellow")) == 2
    
    # Търсене по артист
    assert len(db.search_songs("Beatles")) == 1
    
    # Няма резултат
    assert len(db.search_songs("Eminem")) == 0
    
    # Case Insensitive (ако SQL-а го поддържа, LIKE обикновено е insensitive)
    assert len(db.search_songs("yellow")) == 2

def test_increment_play_count(db):
    """Сценарий: Увеличаване на брояча."""
    db.add_song("Song", "Art", "Gen", "path")
    songs = db.get_all_songs()
    s_id = songs[0][0]
    
    db.increment_play_count(s_id)
    db.increment_play_count(s_id)
    
    updated = db.get_all_songs()
    assert updated[0][5] == 2

def test_increment_invalid_id(db):
    """Сценарий: Увеличаване на несъществуващо ID (не трябва да гърми)."""
    try:
        db.increment_play_count(9999)
    except Exception as e:
        pytest.fail(f"increment_play_count crashed: {e}")

# --- ТЕСТОВЕ ЗА ПЛЕЙЛИСТИ (PLAYLISTS) ---

def test_create_playlist_success(db):
    """Сценарий: Успешно създаване на плейлист с песни."""
    # 1. Добавяме песни
    db.add_song("S1", "A1", "G1", "p1")
    db.add_song("S2", "A2", "G2", "p2")
    songs = db.get_all_songs()
    ids = [s[0] for s in songs]
    
    # 2. Създаваме плейлист
    res = db.create_playlist("My Mix", ids)
    assert res is True
    
    # 3. Проверяваме
    pls = db.get_playlists()
    assert len(pls) == 1
    assert pls[0][1] == "My Mix"
    
    # 4. Проверяваме съдържанието
    pl_songs = db.get_playlist_songs(pls[0][0])
    assert len(pl_songs) == 2

def test_create_playlist_duplicate_name(db):
    """Сценарий: Два плейлиста с едно име (не трябва да става)."""
    db.create_playlist("Gym", [])
    res = db.create_playlist("Gym", []) # Втори път
    
    assert res is False
    assert len(db.get_playlists()) == 1

def test_get_playlists_empty(db):
    """Сценарий: Няма плейлисти."""
    assert len(db.get_playlists()) == 0

def test_delete_playlist(db):
    """Сценарий: Триене на плейлист и връзките му."""
    db.add_song("S1", "A1", "G1", "p1")
    s_id = db.get_all_songs()[0][0]
    
    db.create_playlist("To Delete", [s_id])
    pl_id = db.get_playlists()[0][0]
    
    # Проверяваме, че има песни преди триенето
    assert len(db.get_playlist_songs(pl_id)) == 1
    
    # Трием
    db.delete_playlist(pl_id)
    
    # Проверяваме
    assert len(db.get_playlists()) == 0
    # Песента НЕ трябва да е изтрита от library, само от плейлиста
    assert len(db.get_all_songs()) == 1 

def test_delete_non_existent_playlist(db):
    """Сценарий: Триене на грешно ID."""
    try:
        db.delete_playlist(999)
    except Exception as e:
        pytest.fail(f"delete_playlist crashed: {e}")

# --- ТЕСТОВЕ ЗА СТАТИСТИКА (STATISTICS) ---

def test_statistics_empty(db):
    """Сценарий: Празна база."""
    report = db.get_statistics()
    # Проверяваме точните стрингове от твоя код
    assert "STATS" in report
    assert "Top song:\n no data" in report
    assert "Top artist:\nno data" in report

def test_statistics_populated(db):
    """Сценарий: Има слушания."""
    db.add_song("Hit Song", "Star", "Pop", "p1")
    s_id = db.get_all_songs()[0][0]
    
    # Трябва да има > 0 слушания, за да излезе в статистиката
    db.increment_play_count(s_id)
    
    report = db.get_statistics()
    assert "Hit Song" in report
    assert "Star" in report
    assert "(1 times streamed)" in report

def test_statistics_ignore_unknown_artist(db):
    """Сценарий: Unknown Artist не трябва да е Top Artist."""
    # 1. Unknown Artist с много слушания
    db.add_song("Mystery", "Unknown Artist", "Pop", "p1")
    id1 = db.get_all_songs()[0][0]
    for _ in range(10): db.increment_play_count(id1)
    
    # 2. Real Artist с малко слушания
    db.add_song("Real Hit", "Real Star", "Pop", "p2")
    id2 = db.get_all_songs()[1][0]
    for _ in range(2): db.increment_play_count(id2)
    
    report = db.get_statistics()
    
    # Real Star трябва да е "Top artist", въпреки че има по-малко слушания
    assert "Top artist:\nReal Star" in report
    
    # Но Unknown Artist ще е "Top song", защото песента е най-слушана
    assert "Top song:\nMystery - Unknown Artist" in report

# --- ТЕСТОВЕ ЗА IMPORT LOGIC (GET SONG BY META) ---

def test_get_song_by_meta_exact(db):
    """Сценарий: Намиране по точно съвпадение."""
    db.add_song("Hello", "Adele", "Pop", "/path/hello.mp3")
    res = db.get_song_by_meta("Hello", "Adele")
    
    assert res is not None
    assert res[4] == "/path/hello.mp3"

def test_get_song_by_meta_case_insensitive(db):
    """Сценарий: Различни главни/малки букви."""
    db.add_song("Hello", "Adele", "Pop", "/path/hello.mp3")
    
    # Търсим "hello" и "ADELE"
    res = db.get_song_by_meta("hello", "ADELE")
    
    assert res is not None
    assert res[1] == "Hello"

def test_get_song_by_meta_not_found(db):
    """Сценарий: Песента липсва."""
    res = db.get_song_by_meta("Nothing", "Nobody")
    assert res is None

def test_statistics_empty(db):
    """Сценарий: Празна база."""
    report = db.get_statistics()
    assert "STATS" in report
    assert "Top song:\nno data" in report
    assert "Top artist:\nno data" in report
    assert "Top genre:\nno data" in report # Проверяваме и за жанр

def test_statistics_top_genre(db):
    """Сценарий: Проверка дали правилно смята най-слушания жанр."""
    # 1. Добавяме Rock песен и я слушаме 5 пъти
    db.add_song("Rock Song", "Artist A", "Rock", "p1")
    id1 = db.get_all_songs()[0][0]
    for _ in range(5): db.increment_play_count(id1)

    # 2. Добавяме Pop песен и я слушаме 2 пъти
    db.add_song("Pop Song", "Artist B", "Pop", "p2")
    id2 = db.get_all_songs()[1][0]
    for _ in range(2): db.increment_play_count(id2)

    report = db.get_statistics()
    
    # Rock трябва да е победител с 5 слушания
    assert "Top genre:\nRock (5 times streamed)" in report