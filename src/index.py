from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO
import subprocess, time, threading

app = Flask(__name__)
socketio = SocketIO(app)    

fallbackQueue = ["lalalove.wav", "myohmy.wav"]
queue = []
radio = {
    "ffmpeg_processes": {},
    "active_connections": {},
    "fpath": 0,
    "time": 0
}

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
    session_id = request.args.get('id')

    if session_id not in radio["active_connections"]:
        return "Not connected to websocket, not authorized", 403  # Return forbidden status if user is not connected via WebSocket
    
    return add_no_cache_headers(Response(generate_audio(session_id), mimetype='audio/mpeg'))

@socketio.on('connect')
def handle_connect():
    global radio
    session_id = request.headers.get('id')
    app.logger.info("Client connected with session id: " + session_id)
    radio["active_connections"][session_id] = True

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.headers.get('id')
    global radio
    radio["active_connections"].pop(session_id, None)  # Remove user from active connections
    if session_id in radio["ffmpeg_processes"]:
        app.logger.info("Terminating ffmpeg process for id " + session_id + "...")
        radio["ffmpeg_processes"][session_id].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'
    app.logger.info("Client disconnected with session id: " + session_id)


@socketio.on('musicstop')
def handle_music_stop(session_id):
    if session_id in radio["ffmpeg_processes"]:
        app.logger.info("Terminating ffmpeg process for id " + session_id + "...")
        radio["ffmpeg_processes"][session_id].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'
    else:
        app.logger.info(f"No ffmpeg process found for session id: {session_id}")

def start_ffmpeg_process():
    global radio
    # Start ffmpeg process
    command = [
        'ffmpeg',
        '-re',                          # Read data from input at native frame rate
        '-ss', str(radio["time"]),      # Start from given time
        '-i', str(radio["fpath"]),      # Input file
        '-c:a', 'libmp3lame',           # Audio codec
        '-b:a', '128k',                 # Audio bitrate
        '-ar', '44100',                 # Audio sample rate
        '-ac', '2',                     # Audio channels (stereo)
        '-preset', 'fast',              # Encoding preset for fast encoding
        '-f', 'mp3',                    # Output format MP3,
        '-'
    ]
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=128)

def generate_audio(session_id):
    global radio
    currentlyplaying = None
    ffmpeg_process = None
    data = None

    def restart():
        if session_id in radio["ffmpeg_processes"]: 
            if radio["ffmpeg_processes"][session_id] == 'terminated':
                del radio["ffmpeg_processes"][session_id]
                return
            
            radio["ffmpeg_processes"][session_id].terminate()
            del radio["ffmpeg_processes"][session_id]

        app.logger.info("Starting new ffmpeg process for id " + session_id + "...")
        ffmpeg_process = start_ffmpeg_process()
        radio["ffmpeg_processes"][session_id] = ffmpeg_process
        return ffmpeg_process

    while True:
        try: data = ffmpeg_process.stdout.read(128)
        except:pass

        # TODO : Array of ffmpeg processes, start playing another file, then switch to second process

        # if radio["fpath"] != currentlyplaying:
        #     currentlyplaying = radio["fpath"]
        #     ffmpeg_process2 = restart()

        if not data:
            ffmpeg_process = restart()
            if not ffmpeg_process:
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

def ai_radio_streamer():
    global queue, radio, fallbackQueue
    duration = 0
    while True:

        if len(queue) == 0:
            queue.extend(fallbackQueue)
        if not duration:
            duration = get_audio_duration(queue[0])
            radio["fpath"] = queue[0]
            radio["time"] = 0
            queue.pop(0)

        # Increment time by 0.1 second
        radio["time"] += 0.1
        if radio["time"] > duration-1:
            # If time exceeds duration, reset to 0 and change to next music
            duration = 0

        time.sleep(0.1)

if __name__ == '__main__':
    time_thread = threading.Thread(target=ai_radio_streamer)
    time_thread.daemon = True
    time_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
