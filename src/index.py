from flask import Flask, Response, render_template
from multiprocessing import Process
import subprocess

app = Flask(__name__)
p = None  # Define p globally

@app.route('/')
def index():
    response = render_template('index.html')
    response = add_no_cache_headers(response)
    return response

def add_no_cache_headers(response):
    response = Response(response)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # Prevent caching by the browser
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def start_audio_stream():
    global p
    while True:
        command = [
            'ffmpeg',
            '-re',             # Read data from input at native frame rate
            '-i', 'test.mp3',  # Path to the file
            '-f', 'mp3',       # Output format MP3
            '-'
        ]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
        p.wait()  # Wait for the subprocess to finish before restarting

@app.route('/listen')
def listen():
    global p
    if p is None or p.poll() is not None:  # If the subprocess has not been started or has finished
        start_audio_stream()  # Start the audio streaming process

    if p and p.stdout:  # Check if p and its stdout attribute are not None
        return Response(iter(lambda: p.stdout.read(1024), b''), mimetype='audio/mpeg')
    else:
        return Response(b'', mimetype='audio/mpeg')

if __name__ == '__main__':
    audio_process = Process(target=start_audio_stream)
    audio_process.start()

    app.run(debug=True, host='0.0.0.0', port=5000)