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

    if not file.filename.lower().endswith('.mp3'):
        logging.debug("Invalid file format")
        return jsonify({"error": "Invalid file format. Only MP3 files are accepted."}), 400

    file_path = "uploaded_audio.mp3"
    wav_file_path = "uploaded_audio.wav"
    logging.debug(f"Saving file to {file_path}")
    file.save(file_path)

    try:
        logging.debug("Converting MP3 to WAV...")
        result = subprocess.run(["ffmpeg", "-i", file_path, wav_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logging.error(f"FFmpeg conversion error: {result.stderr.decode()}")
            return jsonify({"error": f"FFmpeg conversion error: {result.stderr.decode()}"}), 500

        logging.debug("Loading audio file and transcribing...")
        audio = AudioSegment.from_file(wav_file_path, format="wav")

        # Convert AudioSegment to byte array
        audio_bytes = io.BytesIO()
        audio.export(audio_bytes, format="wav")
        audio_bytes.seek(0)

        transcription = transcribe(audio_bytes)  # Custom transcribe function should be defined
        logging.debug(f"Transcription result: {transcription}")
        os.remove(file_path)
        os.remove(wav_file_path)
        logging.debug("Files removed after processing")

        return send_file(audio_bytes, attachment_filename="transcribed_audio.wav", as_attachment=True), 200

    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(wav_file_path):
            os.remove(wav_file_path)
        return jsonify({"error": str(e)}), 500



def transcribe(audio):
    print("okkkkkkkkkkkkkkkkkkkkkkkkkkkk",audio)
    logging.debug("Transcribing audio")
    transcriber = pipeline("automatic-speech-recognition", model="vinai/PhoWhisper-large", device="cpu")

    transcript=transcriber(audio)
    return transcript

if __name__ == "__main__":
    logging.debug("Starting Flask application...")
    app.run(debug=True, host="0.0.0.0", port=5000)
