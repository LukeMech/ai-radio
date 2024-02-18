import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from moviepy.editor import AudioFileClip
import uvicorn

app = FastAPI()

# Ścieżka do pliku MP4
audio_file_path = 'sciezka/do/pliku.mp4'

# Kolejka asynchroniczna do przechowywania strumienia audio
audio_queue = asyncio.Queue()

# Funkcja do odtwarzania pliku MP4 jako strumienia audio
async def play_audio_stream():
    while True:
        # Otwórz plik MP4 za pomocą moviepy
        audio_clip = AudioFileClip(audio_file_path)
        # Odtwarzaj strumień audio
        for chunk in audio_clip.iter_chunks():
            await audio_queue.put(chunk)
            await asyncio.sleep(0.1)  # Dla asynchroniczności

# Rozpoczęcie odtwarzania globalnego strumienia audio
async def start_global_audio_stream():
    asyncio.create_task(play_audio_stream())  # uruchomienie odtwarzania strumienia

# Trasa do strumienia audio
@app.get('/audio_stream')
async def audio_stream(request: Request):
    async def audio_stream_generator():
        while True:
            chunk = await audio_queue.get()
            yield chunk

    return StreamingResponse(audio_stream_generator(), media_type="audio/mpeg")

# Trasa do strony głównej z przyciskiem start
@app.get('/')
async def index():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AIRadio</title>
        <script>
            var audio = new Audio('/audio_stream');
            function startAudio() {
                audio.play();
            }
        </script>
    </head>
    <body>
        <h1>AIRadio</h1>
        <button onclick="startAudio()">Start</button>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
    asyncio.run(start_global_audio_stream())  # Uruchomienie globalnego strumienia audio
