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
    "fpath": "",
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
    
    elif session_id in radio["ffmpeg_processes"]:
        app.logger.info("Restarting ffmpeg process for id " + session_id + "...")
        radio["ffmpeg_processes"][session_id].terminate()
        del radio["ffmpeg_processes"][session_id]

    else:
        app.logger.info("Starting ffmpeg process for id " + session_id + "...")

    ffmpeg_process = start_ffmpeg_process()
    radio["ffmpeg_processes"][session_id] = ffmpeg_process

    time.sleep(1)

    return add_no_cache_headers(Response(generate_audio(ffmpeg_process, radio["fpath"]), mimetype='audio/mpeg'))

@socketio.on('connect')
def handle_connect():
    global radio
    session_id = request.headers.get('id')
    app.logger.info("Client connected with session id: " + session_id)
    radio["active_connections"][session_id] = True

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.headers.get('id')
    app.logger.info("Client disconnected with session id: " + session_id)
    global radio
    radio["active_connections"].pop(session_id, None)  # Remove user from active connections
    if session_id in radio["ffmpeg_processes"]:
        app.logger.info("Terminating ffmpeg process for id " + session_id + "...")
        radio["ffmpeg_processes"][session_id].terminate()
        del radio["ffmpeg_processes"][session_id]

def start_ffmpeg_process():
    global radio
    # Rozpocznij proces ffmpeg
    command = [
        'ffmpeg',
        '-re',                      # Read data from input at native frame rate
        '-ss', str(radio["time"]),     # Start from given time
        '-i', str(radio["fpath"]),        # Input file
        '-f', 'mp3',                # Output format MP3,
        '-'
    ]
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**8)

def generate_audio(ffmpeg_process, currentlyplaying):
    global radio
    while True:
        if(radio["fpath"] != currentlyplaying):
            break
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

def ai_radio_streamer():
    global radio, queue
    duration = 0
    while True:
        if not queue:
            queue = fallbackQueue

        if not radio["fpath"]:
           radio["fpath"] = queue[0]
           queue.pop(0)

        if not duration:
            duration = get_audio_duration(radio["fpath"])
 
        # Increment time by 1 second
        radio["time"] += 0.1
        if radio["time"] > duration:
            # If time exceeds duration, reset to 0 and change to next music
            radio["time"] = 0
            radio["fpath"] = 0

        time.sleep(0.1)

if __name__ == '__main__':
    time_thread = threading.Thread(target=ai_radio_streamer)
    time_thread.daemon = True
    time_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)
