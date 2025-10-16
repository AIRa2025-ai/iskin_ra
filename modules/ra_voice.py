# modules/ra_voice.py
class RaVoice:
    def __init__(self, context, stt_provider='whisper', tts_provider='pyttsx3'):
        self.context = context

    async def speech_to_text(self, audio_bytes: bytes) -> str:
        # call provider
        return "распознанный текст"

    async def text_to_speech(self, text: str) -> bytes:
        # returns audio bytes
        return b"mp3bytes"
