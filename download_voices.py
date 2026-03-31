import urllib.request
import os

print("Downloading Voice Starter Pack...")

# A dictionary of voice names and URLs to short, public-domain/open-source voice clips
voices_to_download = {
    "Fable.wav": "https://raw.githubusercontent.com/coqui-ai/TTS/dev/tests/data/ljspeech/wavs/LJ001-0001.wav"
}

for filename, url in voices_to_download.items():
    if not os.path.exists(filename):
        try:
            print(f"Fetching {filename}...")
            urllib.request.urlretrieve(url, filename)
            print(f"  -> Successfully saved {filename}!")
        except Exception as e:
            print(f"  -> Failed to download {filename}: {e}")
    else:
        print(f"{filename} already exists. Skipping.")

print("\nDone!")
