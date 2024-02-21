from curses import nonl
from flask import Flask, Response, render_template, request, send_from_directory, abort
from flask_socketio import SocketIO
import subprocess, time, threading, json, random, os, shutil, string
from helpers import youtube

app = Flask(__name__)
socketio = SocketIO(app)    

with open('ytlist.json', 'r') as file:
    ytUrlList = json.load(file)

ffmpeg_opts = [
    '-c:a', 'libmp3lame',           # Audio codec
    '-b:a', '192k',                 # Audio bitrate
    '-ar', '44100',                 # Audio sample rate
    '-ac', '2',                     # Audio channels (stereo)
    '-preset', 'fast',              # Encoding preset for fast encoding
    '-f', 'mp3',                    # Output format MP3,
]

fallbackQueue = {"fpath": "lalalove.wav", "title": "La La Love", "author": "C-Bool, SkyTech, GiangPham"}, 

queue = []
radio = {
    "ffmpeg_processes": {},
    "active_connections": {},
    "fpath": 0, "title": '', "author": '', "duration": 0, "thunbnail": 0,
    "time": 0,
    "NOTREMOVE": True,
    "playID": 0
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

@app.route('/tmp/<path:filename>')
def serve_file(filename):
    # Assuming the files are stored in the 'tmp' folder
    if not filename.endswith('.wav'):    
        return send_from_directory('tmp', filename)
    else:
        # Return a 404 error if the file is not avaiable
        abort(404)

@socketio.on('connect')
def handle_connect():
    global radio
    session_id = request.headers.get('id')
    print("Client connected with session id: " + session_id, flush=True)
    radio["active_connections"][session_id] = request.sid
    if(radio["fpath"] != 0): socketio.emit('trackChange', {'file': radio["fpath"], 'title': radio["title"], 'author': radio["author"], 'duration': radio["duration"], 'time': radio["time"], 'thunbnail': radio["thunbnail"]}, to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.headers.get('id')
    global radio
    radio["active_connections"].pop(session_id, None)  # Remove user from active connections
    if session_id in radio["ffmpeg_processes"]:
        for process in radio['ffmpeg_processes'][session_id]:
            if process != 'terminated':
                print("Terminating ffmpeg process for id '" + session_id + "' for media '" + process["file"] + "'...", flush=True)
                process["process"].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'
        print("Client disconnected with session id: " + session_id, flush=True)

@socketio.on('musicstop')
def handle_music_stop(session_id):
    if session_id in radio["ffmpeg_processes"]:
        for process in radio['ffmpeg_processes'][session_id]:
            if process != 'terminated':
                print("Terminating ffmpeg process for id '" + session_id + "' for media '" + process["file"] + "'...", flush=True)
                process["process"].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'
    else:
        print("No ffmpeg process found for session id: " + session_id, flush=True)

def start_ffmpeg_process():
    global radio
    # Start ffmpeg process
    command = [
        'ffmpeg',
        '-re',                          # Read data from input at native frame rate
        '-ss', str(radio["time"]),      # Start from given time
        '-i', str(radio["fpath"]),      # Input file
    ]
    command.extend(ffmpeg_opts)
    command.append('-')  # Output to stdout
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
                    print("Terminating ffmpeg process for id '" + session_id + "' for media '" + radio["ffmpeg_processes"][session_id][0]["file"] + "'...", flush=True)
                    radio['ffmpeg_processes'][session_id][0]["process"].terminate()
                    del radio["ffmpeg_processes"][session_id][0]
                    return radio["ffmpeg_processes"][session_id][0]["process"]
                elif len(radio["ffmpeg_processes"][session_id]) == 1:
                    return radio["ffmpeg_processes"][session_id][0]["process"]
                else: return False

        else:
            radio["ffmpeg_processes"][session_id] = []

        if not terminate and isinstance(radio["fpath"], str):
            print("Starting new ffmpeg process for id '" + session_id + "' for media '" + radio["fpath"] + "'...", flush=True)       
            ffmpeg_process = start_ffmpeg_process()
            process_json = {
                "process": ffmpeg_process, 
                "file": radio["fpath"]
            }
            radio["ffmpeg_processes"][session_id].append(process_json)
            return ffmpeg_process
        else: return False

    currentlyplaying = radio["playID"]
    data = None
    ffmpeg_process = restart()

    while True:
        if radio["playID"] != currentlyplaying:
            currentlyplaying = radio["playID"]
            restart()

        try: data = ffmpeg_process.stdout.read(128)
        except:pass

        if not data:
            ffmpeg_process = restart(True)
            if not ffmpeg_process:
                time.sleep(3)
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
    global queue, radio, fallbackQueue, ytUrlList
    duration = 0; waiting = False; downloadReqSent = False; waitingFORCE = False; firstLaunchReady = False;
    def on_dwnld_completed(t, a, fp, ext, thunb):
        queue[0]["fpath"] = fp + '.' + ext
        queue[0]["title"] = t
        queue[0]["author"] = a
        queue[0]["thunbnail"] = fp + '.' + thunb
        queue[0]["fetched"] = True
        print("Downloaded and set to queue track " + t + ", id: " + fp, flush=True)
        nonlocal firstLaunchReady; firstLaunchReady = True;

    queue.append({"url": random.choice(ytUrlList)})
    youtube.downloadWavFromUrl(queue[0]['url'], on_dwnld_completed)

    while firstLaunchReady:

        if not duration and ((not waiting and downloadReqSent) or waitingFORCE):
            if queue[0]['url'] and not waitingFORCE:
                waiting = True
                dwnld = threading.Thread(target=youtube.downloadWavFromUrl, args=(queue[0]['url'], on_dwnld_completed))
                dwnld.daemon = True
                dwnld.start()
    
            if waitingFORCE:
                toRemove = []
                if not radio["NOTREMOVE"]: 
                    toRemove = [radio["fpath"]]
                    if('thunbnail' in radio):
                        toRemove.append(radio["thunbnail"])

                radio["NOTREMOVE"] = False
                if (not "fpath" in queue[0] or not "fetched" in queue[0]) and waitingFORCE:
                    print("Using track from fallback queue...", flush=True)
                    queue.pop(0)
                    queue.insert(0, *fallbackQueue)
                    radio["NOTREMOVE"] = True
                
                duration = get_audio_duration(queue[0]["fpath"])
                radio["duration"] = duration
                radio["time"] = 0
                radio["fpath"] = queue[0]["fpath"]
                radio["title"] = queue[0]["title"]
                radio["author"] = queue[0]["author"]
                radio["playID"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                if("thunbnail" in queue[0]):
                    radio["thunbnail"] = queue[0]["thunbnail"]
                # Falback to default icon
                else: radio["thunbnail"] = None

                queue.pop(0)
                socketio.emit('trackChange', {'file': radio["fpath"], 'title': radio["title"], 'author': radio["author"], 'duration': radio["duration"], 'thunbnail': radio["thunbnail"], 'time': 0})
                # Remove ytdl downloaded file
                if len(toRemove) > 0: 
                    for el in toRemove:
                        if(os.path.exists(el)): 
                            os.remove(el)
                            print("Removed file: " + el, flush=True)
                waitingFORCE = False
                waiting = False
                downloadReqSent = False

        if len(queue) < 1:
            queue.append({"url": random.choice(ytUrlList)})

        # Increment time by 0.1 second
        radio["time"] += 0.1

        # Fetch next track when 0.5min to end of track
        if radio["time"] > radio["duration"]-30 and radio["time"] < radio["duration"]-2 and not downloadReqSent:
            duration = 0
            downloadReqSent = True

        # Send force signal to ensure audio playback
        if radio["time"] > radio["duration"]-2 and not waitingFORCE:
            waitingFORCE = True

        time.sleep(0.1)

if os.path.exists('./tmp'):
    shutil.rmtree('./tmp')
    
time_thread = threading.Thread(target=ai_radio_streamer)
time_thread.daemon = True
time_thread.start()
if __name__ == '__main__':
    socketio.run(app, use_reloader=False, debug=False, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True)
