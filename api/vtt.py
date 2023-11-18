import requests
from pydub import AudioSegment
import speech_recognition as sr
from io import BytesIO

class VideoToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.language = 'en-US'

    def set_language(self, language: str):
        self.language = language

    def download_video(self, url: str) -> BytesIO:
        response = requests.get(url)
        return BytesIO(response.content)

    def convert_to_audio(self, video_stream: BytesIO) -> BytesIO:
        video = AudioSegment.from_file(video_stream, format="mp4")
        audio_stream = BytesIO()
        video.export(audio_stream, format="wav")
        audio_stream.seek(0)
        return audio_stream

    def transcribe_audio(self, audio_stream: BytesIO) -> str:
        with sr.AudioFile(audio_stream) as source:
            audio_data = self.recognizer.record(source)
            try:
                text = self.recognizer.recognize_google(audio_data, language=self.language)
                return text
            except sr.UnknownValueError:
                return "Audio was not understandable"
            except sr.RequestError as e:
                return f"Could not request results from Google Speech Recognition service; {e}"

    def transcribe_video(self, video_url: str) -> str:
        video_stream = self.download_video(video_url)
        audio_stream = self.convert_to_audio(video_stream)
        return self.transcribe_audio(audio_stream)
