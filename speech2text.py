from gtts import gTTS
from playsound import playsound


class Speech2Text:
    """
    Speech 2 text module
    """

    def __init__(self):
        pass

    def speak(self, text):
        """
        Speak text
        """
        speech_object = gTTS(text=text, lang="en", slow=False)
        speech_object.save("response.mp3")

        playsound("response.mp3")
