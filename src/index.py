from flask import Flask, Response, request, send_from_directory, abort
from flask_cors import CORS
from flask_socketio import SocketIO
import subprocess, time, threading, random, os, string, requests, json, datetime
from helpers import youtube

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")    
token = os.environ['AWS_TOKEN']

def today():
    return datetime.datetime.now().isoweekday()

# Set to false when pushing
if os.environ.get("NONLOCAL"): local_ytlist = False
else: local_ytlist = False

if not local_ytlist:
    with open('ytlist.url', 'r') as file:
        ytlist_url = file.read().strip()

ffmpeg_opts = [
    '-c:a', 'libmp3lame',           # Audio codec
    '-b:a', '192k',                 # Audio bitrate
    '-ar', '44100',                 # Audio sample rate
    '-ac', '2',                     # Audio channels (stereo)
    '-preset', 'fast',              # Encoding preset for fast encoding
    '-f', 'mp3',                    # Output format MP3,
]

fallbackQueue = {"fpath": "helpers/lalalove.wav", "title": "La La Love", "author": "C-Bool, SkyTech, GiangPham", "additional": {}}

queue = []
alreadyPlayed = []
radio = {
    "ffmpeg_processes": {}, "active_connections": {},
    "title": '', "author": '', "duration": 0, "thumbnail": 0, "additional": {},
    "fpath": 0, "time": 0, "NOTREMOVE": True, "playID": 0
}
def create_track_change_args(radio):
    return {
        'title': radio.get("title", ""),
        'author': radio.get("author", ""),
        'duration': radio.get("duration", ""),
        'thumbnail': radio.get("thumbnail", ""),
        "time": radio.get("time", 0),
        'additional': radio.get("additional", "")
    }

def create_queue_change_args(q): 
    return [
        {
            'title': track.get("title", ""),
            'author': track.get("author", ""),
            'duration': track.get("duration", ""),
            'thumbnail': track.get("thumbnail", "")
        }
        for track in q
        if track.get("title") and track.get("author")     
    ]
    

def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # Prevent caching by the browser
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response
    
@app.route('/listen')
def listen():
    global radio
    session_id = request.args.get('id')

    if session_id not in radio["active_connections"]:
        return "Not connected to websocket, not authorized", 403  # Return forbidden status if user is not connected via WebSocket
    
    return add_no_cache_headers(Response(generate_audio(session_id), mimetype='audio/mpeg'))

@app.route('/<path:num>')
def main(num):
    return add_no_cache_headers(Response("Online, reached /" + num))

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
    if not session_id: return
    print("Client connected with session id: " + session_id, flush=True)
    # type: ignore
    radio["active_connections"][session_id] = request.sid # type: ignore
    with open('server.version.txt', 'r') as file:
        socketio.emit('serverVersion', file.read(), to=request.sid)
    if(radio["fpath"] != 0): socketio.emit('trackChange', create_track_change_args(radio), to=request.sid) # type: ignore
    if(len(queue) > 0): socketio.emit('queueChange', create_queue_change_args(queue), to=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.headers.get('id') or ''
    global radio
    radio["active_connections"].pop(session_id, None)  # Remove user from active connections
    if session_id in radio["ffmpeg_processes"]:
        for process in radio['ffmpeg_processes'][session_id]:
            if process != 'terminated' and isinstance(process, dict) and "file" in process and "process" in process:
                print("Terminating ffmpeg process for id '" + session_id + "' for media '" + process["file"] + "'...", flush=True)
                process["process"].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'
    print("Client disconnected with session id: " + session_id, flush=True)

@socketio.on('musicstop')
def handle_music_stop(session_id):
    if session_id in radio["ffmpeg_processes"]:
        for process in radio['ffmpeg_processes'][session_id]:
            if isinstance(process, dict) and "file" in process and "process" in process:
                print("Terminating ffmpeg process for id '" + session_id + "' for media '" + process["file"] + "'...", flush=True)
                process["process"].terminate()
        radio["ffmpeg_processes"][session_id] = 'terminated'

@socketio.on('urlChanged')
def handle_url_changed(data):
    url = data['url']
    getToken = data['token']
    if(getToken == token):
        socketio.emit('urlChanged', url)
        print(f"Send URL changed event to connected clients, url: {url}")

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

        try: data = ffmpeg_process.stdout.read(128) # type: ignore
        except:pass

        if not data:
            ffmpeg_process = restart(True)
            if not ffmpeg_process:
                time.sleep(1)
                return

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
    forceChange = False; firstLaunchReady = False; downloadErr = -1; downloading = False; indexChanged = 0;
    def on_dwnld_completed(t, a, fp, ext, thunb, ERR, i):
        nonlocal indexChanged, downloadErr, firstLaunchReady, downloading
        if(indexChanged): i = i - indexChanged
        if(ERR): 
            print("Failed to download track ", flush=True)
            downloadErr = i
            downloading = False
            return 
        
        queue[i]["fpath"] = fp + '.' + ext
        queue[i]["title"] = t
        queue[i]["author"] = a
        queue[i]["duration"] = get_audio_duration(queue[i]["fpath"])
        if(thunb): queue[i]["thumbnail"] = fp + '.' + thunb
        else: queue[i]["thumbnail"] = None
        print("Downloaded and added to queue track " + t + ", id: " + fp, flush=True)
        firstLaunchReady = True; downloading = False
        socketio.emit('queueChange', create_queue_change_args(queue))

    def addToQueue():
        if not local_ytlist:
            response = requests.get(ytlist_url)
            if response.ok:
                tracksList = response.json()
            else: return
        else: 
            with open('ytlist.min.json', 'r') as file:
                tracksList = json.load(file)

        weighted_choices = []
        for entry in tracksList:
            if isinstance(entry, str):
                url = entry
                multiplier = 1
                setting = None
            else:
                url = entry[0]
                multiplier = entry[1].get("m", 1)
                setting = {key: value for key, value in entry[1].items() if key != "m"}
                if 'dm' in entry[1]:
                    day, additional_multiplier = map(int, entry[1]['dm'].split(';'))
                    if day == today():
                        multiplier *= additional_multiplier
            weighted_choices.extend([(url, setting)] * multiplier)

        if len(weighted_choices) < 1: return
        else:
            if(len(alreadyPlayed) > len(tracksList)/3): alreadyPlayed.pop(0)
            def shuffle():
                random.shuffle(weighted_choices)
                chosen_url, setting = random.choice(weighted_choices)
                if not setting: setting = {}
                return chosen_url, setting
           
            chosen_url, setting = shuffle()
            while chosen_url in alreadyPlayed: 
                chosen_url, setting = shuffle()

            queue.append({"url": chosen_url, "additional": setting})
            alreadyPlayed.append(chosen_url)

    addToQueue()
    if len(queue) < 1: queue.append({})
    if("url" in queue[0]): 
        youtube.downloadWavFromUrl(queue[0]['url'], on_dwnld_completed, 0)
    else: 
        firstLaunchReady = True

    while firstLaunchReady:
        # Pre-adding & fetching next songs
        if len(queue) < 2:
            addToQueue()

        # Error downloading
        if downloadErr > -1:
            queue.pop(downloadErr)
            print(f"Popped from queue errored track ({downloadErr})", flush=True)
            downloadErr = -1

        # Request download
        for track in queue:
            if not downloading and "url" in track and not "fpath" in track:
                indexChanged = 0
                downloading = True
                threading.Thread(target=youtube.downloadWavFromUrl,daemon=True,args=(track["url"], on_dwnld_completed, queue.index(track))).start()

        # Change radio playing title
        if forceChange:
            forceChange = False
            toRemove = []
            if not radio["NOTREMOVE"]: 
                toRemove = [radio["fpath"]]
                if('thumbnail' in radio):
                    toRemove.append(radio["thumbnail"])
            radio["NOTREMOVE"] = False
            if (not "fpath" in queue[0]):
                print("Using track from fallback queue...", flush=True)
                queue.pop(0)
                if(len(queue) < 1): queue.append({})
                queue.insert(0, fallbackQueue)
                radio["NOTREMOVE"] = True
                radio["additional"] = {}

            radio["duration"] = queue[0]["duration"] if "duration" in queue[0] else get_audio_duration(queue[0]["fpath"])
            radio["time"] = 0 # Change to duration-10 for debugging
            radio["fpath"] = queue[0]["fpath"]
            radio["title"] = queue[0]["title"]
            radio["author"] = queue[0]["author"]
            radio["additional"] = queue[0].get("additional", {})
            radio["playID"] = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            radio["thumbnail"] = queue[0].get("thumbnail", None)
            queue.pop(0)
            indexChanged += 1
            socketio.emit('trackChange', create_track_change_args(radio))
            # Remove ytdl downloaded file
            if len(toRemove) > 0: 
                for el in toRemove:
                    if(os.path.exists(el)): 
                        os.remove(el)
                        print("Removed file: " + el, flush=True)

        # Increment time by 0.1 second
        radio["time"] += 0.1

        # Send force signal to ensure audio playback
        if radio["time"] >= radio["duration"]-0.1 and not forceChange:
            forceChange = True

        time.sleep(0.1)
    
threading.Thread(target=ai_radio_streamer,daemon=True).start()
if __name__ == '__main__':
    socketio.run(app, use_reloader=False, host='0.0.0.0', port=8000, allow_unsafe_werkzeug=True) # type: ignore
