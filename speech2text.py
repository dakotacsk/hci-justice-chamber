from gtts import gTTS
from playsound import playsound
from pydub import AudioSegment


class Speech2Text:
    """
    Speech 2 text module
    """

    def __init__(self):
        pass

    def speak(self, text, speaker):
        """
        Speak text
        """
        accent = {
            "Jamie (Meritocracy)": "com",
            "Jordan (Rawlsian)": "co.uk",
            "Amara (Restorative)": "com.au",
            "Sam (Utilitarian)": "ie",
        }
        speech_object = gTTS(text=text, lang="en", slow=False, tld=accent[speaker])
        speech_object.save("response.mp3")

        sound = AudioSegment.from_file("response.mp3")
        faster_sound = sound.speedup(playback_speed=1.25)

        # 3. Save the fast version
        faster_sound.export("response.mp3", format="mp3")

        # 4. Play it
        playsound("response.mp3")
