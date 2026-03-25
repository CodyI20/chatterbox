import io
import os
import glob
import logging
import psutil
import torch
import torchaudio as ta
from flask import Flask, request, send_file, jsonify, render_template

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ==========================================
# WINDOWS PRIORITY
# Tells Windows not to throttle this process when UE5 is in focus
# ==========================================
p = psutil.Process(os.getpid())
try:
    p.nice(psutil.HIGH_PRIORITY_CLASS)
    app.logger.info("Set process to High Priority to prevent Windows throttling.")
except Exception as e:
    app.logger.warning(f"Could not set high priority: {e}")

# ==========================================
# VRAM OPTIMIZATION
# ==========================================
if torch.cuda.is_available():
    device = "cuda"
    # Restrict PyTorch to only use vram_to_use*100% of your GPU VRAM (Adjust this fraction as needed!)
    vram_to_use = 0.4
    torch.cuda.set_per_process_memory_fraction(vram_to_use, 0)
    app.logger.info(f"Capped CUDA VRAM usage at {vram_to_use*100}.")
else:
    device = "cpu"

app.logger.info(f"Using device: {device}")

try:
    from chatterbox.tts_turbo import ChatterboxTurboTTS
    model = ChatterboxTurboTTS.from_pretrained(device=device)
    # Optional: If the model supports it, convert to half-precision to save even more VRAM
    # model.half() 
    app.logger.info("Model loaded successfully!")
except Exception as e:
    app.logger.error(f"Failed to load model: {e}")
    raise

# ==========================================
# WEB UI ENDPOINTS
# ==========================================
@app.route("/")
def index():
    # Serves the HTML file we will create next
    return render_template("index.html")

@app.route("/voices", methods=["GET"])
def get_voices():
    # Automatically finds all .wav files in the server folder
    wav_files = glob.glob("*.wav")
    return jsonify(wav_files)

@app.route("/tts", methods=["POST"])
def tts():
    if not request.is_json or "text" not in request.json:
        return jsonify({"error": "Invalid request."}), 400
        
    data = request.json
    text = data.get("text")
    voice_file = data.get("voice", "Orweyna.wav")
    settings = data.get("settings", {})
    
    if not os.path.exists(voice_file):
        return jsonify({"error": f"Voice file '{voice_file}' not found."}), 404
    
    try:
        # INFERENCE MODE & CACHE CLEARING
        # This tells PyTorch not to store memory for training, making it much faster
        with torch.inference_mode():
            wav = model.generate(text, audio_prompt_path=voice_file, **settings)
        
        # Clean up any leftover GPU memory immediately after generation
        if device == "cuda":
            torch.cuda.empty_cache()
            
        buf = io.BytesIO()
        ta.save(buf, wav, model.sr, format="wav")
        buf.seek(0)
        return send_file(buf, mimetype="audio/wav")
    except Exception as e:
        app.logger.error(f"Generation error: {e}")
        return jsonify({"error": str(e)}), 500
