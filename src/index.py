from flask import Flask, Response, render_template, request
from flask_socketio import SocketIO
import subprocess, time, threading

app = Flask(__name__)
socketio = SocketIO(app)    

fallbackQueue = [
    {"fpath": "lalalove.wav", "title": "La La Love", "author": "C-Bool, SkyTech, GiangPham"}, 
    {"fpath": "myohmy.wav", "title": "Czułe Słowa (My Oh My)", "author": "Piękni I Młodzi, Magdalena Narożna"}
]
queue = []
radio = {
    "ffmpeg_processes": {},
    "active_connections": {},
    "fpath": 0, "title": '', "author": '', "duration": 0,
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
    print("Client connected with session id: " + session_id)
    radio["active_connections"][session_id] = request.sid
    socketio.emit('trackChange', {'file': radio["fpath"], 'title': radio["title"], 'author': radio["author"], 'duration': radio["duration"], 'time': radio["time"]}, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.headers.get('id')
    global radio
    radio["active_connections"].pop(session_id, None)  # Remove user from active connections
    if session_id in radio["ffmpeg_processes"]:
        for process in radio['ffmpeg_processes'][session_id]:
            print("Terminating ffmpeg process for id '" + session_id + "' for media '" + process["file"] + "'...")
            process["process"].terminate()
        print("Client disconnected with session id: " + session_id)

@socketio.on('musicstop')
def handle_music_stop(session_id):
    if session_id in radio["ffmpeg_processes"]:
        for process in radio['ffmpeg_processes'][session_id]:
            print("Terminating ffmpeg process for id '" + session_id + "' for media '" + process["file"] + "'...")
            process["process"].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'
    else:
        print("No ffmpeg process found for session id: " + session_id)

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
    def restart(terminate=False):
        if session_id in radio["ffmpeg_processes"]: 
            if radio["ffmpeg_processes"][session_id] == 'terminated':
                del radio["ffmpeg_processes"][session_id]
                return
            
            if terminate:
                if len(radio['ffmpeg_processes'][session_id]) > 1:
                    print("Terminating ffmpeg process for id '" + session_id + "' for media '" + radio["ffmpeg_processes"][session_id][0]["file"] + "'...")
                    radio['ffmpeg_processes'][session_id][0]["process"].terminate()
                    del radio["ffmpeg_processes"][session_id][0]
                    return radio["ffmpeg_processes"][session_id][0]["process"]
                elif len(radio["ffmpeg_processes"][session_id]) == 1:
                    return radio["ffmpeg_processes"][session_id][0]["process"]
                else: return False

        else:
            radio["ffmpeg_processes"][session_id] = []

        if not terminate:
            print("Starting new ffmpeg process for " + radio["fpath"] + " for id " + session_id + "...")
            ffmpeg_process = start_ffmpeg_process()
            process_json = {
                "process": ffmpeg_process, 
                "file": radio["fpath"]
            }
            radio["ffmpeg_processes"][session_id].append(process_json)
            return ffmpeg_process
        else: return False

    currentlyplaying = radio["fpath"]
    data = None
    ffmpeg_process = restart()

    while True:
        if radio["fpath"] != currentlyplaying:
            currentlyplaying = radio["fpath"]
            restart()

        try: data = ffmpeg_process.stdout.read(128)
        except:pass

        if not data:
            ffmpeg_process = restart(True)
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
            duration = get_audio_duration(queue[0]["fpath"])
            radio["time"] = 0
            radio["fpath"] = queue[0]["fpath"]
            radio["title"] = queue[0]["title"]
            radio["author"] = queue[0]["author"]
            radio["duration"] = duration
            queue.pop(0)
            socketio.emit('trackChange', {'file': radio["fpath"], 'title': radio["title"], 'author': radio["author"], 'duration': radio["duration"], 'time': 0})

        # Increment time by 0.1 second
        radio["time"] += 0.1
        if radio["time"] > duration-2:
            # If time exceeds duration, reset and change to next music
            duration = 0

        time.sleep(0.1)

time_thread = threading.Thread(target=ai_radio_streamer)
time_thread.daemon = True
time_thread.start()
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)
