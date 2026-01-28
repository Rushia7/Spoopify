from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl

class AudioPlayer:
    def __init__(self) -> None:
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)
    
    def load_song(self, path: str) -> None:
        self.player.setSource(QUrl.fromLocalFile(path))

    def play(self) -> None:
        self.player.play()

    def pause(self) -> None:
        self.player.pause()

    def stop(self) -> None:
        self.player.stop()

    def set_volume(self, volume: int) -> None:
        float_volume = volume / 100.0
        self.audio_output.setVolume(float_volume)