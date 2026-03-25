import os
from flask import Flask, request, send_file, jsonify
import torchaudio as ta
import torch
from chatterbox.tts_turbo import ChatterboxTurboTTS
# from chatterbox.mtl_tts import ChatterboxMultilingualTTS # Unused for now
import logging
import io

app = Flask(__name__)

# Setting up logging for error detection in production
logging.basicConfig(level=logging.INFO)

# Automatically detect the best available device
if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

app.logger.info(f"Using device: {device}")

# Loading the model with error catching
try:
    model = ChatterboxTurboTTS.from_pretrained(device="cuda")
    app.logger.info("Model loaded successfully!")
except Exception as e:
    app.logger.error(f"Failed to load model: {e}")
    raise

@app.route("/tts", methods=["POST"])
def tts():
    if not request.is_json or "text" not in request.json:
        return jsoinfy({"error": "Invalid request. Please provide JSON with a 'text' field."}), 400

    data = request.json
    text = data.get("text")
    # text = "Hello there Sophie! How are you today?"

    voice_file = data.get("voice", "Orweyna.wav")

    settings = data.get("settings", {})

    if not os.path.exists(voice_file):
        app.logger.error(f"Voice file missing: {voice_file}")
        return jsonify({"error": f"Voice file '{voice_file}' not found on the server."}), 404

    try:
        # **settings unpacks the dictionary directly into the function
        wav = model.generate(text, audio_prompt_path=voice_file, **settings)
        buf = io.BytesIO()
        ta.save(buf, wav, model.sr, format="wav")
        buf.seek(0)
        app.logger.info("File created successfully!")
        return send_file(buf, mimetype="audio/wav")
    except TypeError as e:
        app.logger.error(f"Invalid model parameter: {e}")
        return jsonify({"error": f"Invalid setting provided: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Generation error: {e}")
        return jsonify({"error": "Failed to generate audio."}), 500

if __name__ == "__main__":
    # Will be ignored in production by Gunicorn
    app.logger.warning("Starting development server. Do not use in production.")
    app.run(host="10.38.94.252", port=5000)
    
