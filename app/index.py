from sanic import Sanic
from sanic.response import html, stream
from moviepy.editor import AudioFileClip
import asyncio

app = Sanic('AIRadio')

# Ścieżka do pliku MP4
audio_file_path = 'test.mp4'

# Funkcja do odtwarzania pliku MP4 jako strumienia audio
async def play_audio_stream():
    while True:
        # Otwórz plik MP4 za pomocą moviepy
        audio_clip = AudioFileClip(audio_file_path)
        # Odtwarzaj strumień audio
        for chunk in audio_clip.iter_chunks():
            yield chunk
            await asyncio.sleep(0.1)  # Dla asynchroniczności

# Trasa do strumienia audio
@app.route('/audio_stream')
async def audio_stream(request):
    headers = {'Content-Type': 'audio/mpeg'}
    return stream(play_audio_stream(), headers=headers)

# Trasa do strony głównej z przyciskiem start
@app.route('/')
async def index(request):
    return html("""
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
    """)
