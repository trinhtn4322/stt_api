from flask import Flask, request, jsonify, send_file
from pydub import AudioSegment
import os
import subprocess
import logging
import io
from transformers import pipeline

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def check_ffmpeg_installed():
    try:
        result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.debug(f"FFmpeg Version Check Output: {result.stdout.decode()}")
        if result.returncode != 0:
            raise FileNotFoundError("FFmpeg not found")
    except FileNotFoundError as e:
        logging.error(f"FFmpeg error: {str(e)}")
        return False
    return True

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    logging.debug("Checking if FFmpeg is installed...")
    if not check_ffmpeg_installed():
        logging.debug("FFmpeg not installed or not found")
        return jsonify({"error": "FFmpeg not installed or not found"}), 400

    logging.debug("Checking if file is uploaded...")
    if 'ok' not in request.files or request.files['ok'] is None or request.files['ok'].filename == "":
        logging.debug("No file uploaded")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['ok']
    logging.debug(f"Received file: {file.filename}")

    allowed_extensions = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'wma'}
    if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
        logging.debug("Invalid file format")
        return jsonify({"error": "Invalid file format. Only audio files are accepted."}), 400

    file_path = f"uploaded_audio{os.path.splitext(file.filename)[1]}"
    logging.debug(f"Saving file to {file_path}")
    file.save(file_path)


    try:
 
        with open(file_path, "rb") as audio_file:
            transcription = transcribe(audio_file.read())  

        logging.debug(f"Transcription result: {transcription}")

        return jsonify({"transcription": transcription}), 200

    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return jsonify({"error": str(e)}), 500



def transcribe(audio):
    logging.debug("Transcribing audio")
    
    # Check if CUDA is available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.debug(f"Using device: {device}")

    transcriber = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-large", device=0 if device == "cuda" else -1)
    transcript = transcriber(audio)
    return transcript["text"]

if __name__ == "__main__":
    logging.debug("Starting Flask application...")
    app.run(debug=True, host="0.0.0.0", port=5000)
