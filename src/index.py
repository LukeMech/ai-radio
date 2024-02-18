from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO
import subprocess, time, threading

app = Flask(__name__)
socketio = SocketIO(app)
radio = {
    "ffmpeg_processes": {},
    "active_connections": {},
    "time": 0
}
WAV_FILE_PATH = 'test.wav'

def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # Prevent caching by the browser
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    response = add_no_cache_headers(Response(render_template('index.html')))
    return response
    
@app.route('/listen')
def listen():
    global radio
    session_id = request.remote_addr
    if session_id not in radio["active_connections"]:
        return "Not authorized", 403  # Return forbidden status if user is not connected via WebSocket
    
    elif session_id in radio["ffmpeg_processes"]:
        print(f"Terminating ffmpeg process for IP {session_id}...")
        radio["ffmpeg_processes"][session_id].terminate()
        del radio["ffmpeg_processes"][session_id]

    print(f"Starting ffmpeg proccess for ip {str(session_id)}...")
    ffmpeg_process = start_ffmpeg_process(radio["time"])
    radio["ffmpeg_processes"][session_id] = ffmpeg_process

    time.sleep(1)

    return add_no_cache_headers(Response(generate_audio(ffmpeg_process), mimetype='audio/mpeg'))

@socketio.on('connect')
def handle_connect():
    global radio
    session_id = request.remote_addr
    print(f"Client connected: {session_id}")
    radio["active_connections"][session_id] = True

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.remote_addr
    print(f"Client disconnected: {session_id}")
    global radio
    radio["active_connections"].pop(session_id, None)  # Remove user from active connections
    if session_id in radio["ffmpeg_processes"]:
        print(f"Terminating ffmpeg process for IP {session_id}...")
        radio["ffmpeg_processes"][session_id].terminate()
        del radio["ffmpeg_processes"][session_id]

def start_ffmpeg_process(start_time):
    # Rozpocznij proces ffmpeg
    command = [
        'ffmpeg',
        '-re',                      # Read data from input at native frame rate
        '-stream_loop', '-1',       # Loop indefinitely
        '-ss', str(start_time),     # Start from given time
        '-i', WAV_FILE_PATH,        # Input file
        '-f', 'mp3',                # Output format MP3,
        '-'
    ]
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)

def generate_audio(ffmpeg_process):
    while True:
        data = ffmpeg_process.stdout.read(1024)
        if not data:
            break
        else: 
            yield data

def get_audio_duration(file_path):
    # Run ffprobe to get audio duration
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = float(result.stdout)
    return duration

def count_time():
    duration = get_audio_duration(WAV_FILE_PATH)
    global radio
    while True:
        # Increment time by 1 second
        radio["time"] += 0.1
        if radio["time"] > duration:
            # If time exceeds duration, reset to 0
            radio["time"] = 0
        time.sleep(0.1)

if __name__ == '__main__':
    time_thread = threading.Thread(target=count_time)
    time_thread.daemon = True
    time_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=8000)
