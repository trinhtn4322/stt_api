from flask import Flask, request, jsonify
from pydub import AudioSegment
import os
import subprocess
import logging
import time
import speech_recognition as sr

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
    if 'file' not in request.files:
        logging.debug("No file uploaded")
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    logging.debug(f"Received file: {file.filename}")

    # Generate a unique filename
    timestamp = str(int(time.time()))
    file_path = f"uploaded_audio_{timestamp}.{file.filename.split('.')[-1]}"
    logging.debug(f"Saving file to {file_path}")

    try:
        file.save(file_path)

        logging.debug("Loading audio file and transcribing...")
        audio = AudioSegment.from_file(file_path, format="mp3") # Assuming MP3 for now
        transcription = transcribe(audio)
        logging.debug(f"Transcription result: {transcription}")
        os.remove(file_path)
        logging.debug("File removed after processing")
        return jsonify({"transcription": transcription}), 200
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({"error": str(e)}), 500

def transcribe(audio):
    # Speech Recognition using Google Speech Recognition API
    r = sr.Recognizer()
    with sr.AudioFile(audio) as source:
        audio_data = r.record(source)

    try:
        logging.debug("Transcribing audio using Google Speech Recognition...")
        transcription = r.recognize_google(audio_data)
        return transcription
    except sr.UnknownValueError:
        logging.error("Google Speech Recognition could not understand audio")
        return "Could not understand audio"
    except sr.RequestError as e:
        logging.error(f"Could not request results from Google Speech Recognition; {e}")
        return "Error requesting transcription"

if __name__ == "__main__":
    logging.debug("Starting Flask application...")
    app.run(debug=True, host="0.0.0.0", port=5000)