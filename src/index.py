import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Ścieżka do pliku MP4
audio_file_path = 'src/test.mp4'

# Funkcja do odtwarzania pliku MP4 jako strumienia audio
# async def play_audio_stream():
#     while True:
#         # Otwórz plik MP4 za pomocą moviepy
#         audio_clip = AudioFileClip(audio_file_path)
#         # Odtwarzaj strumień audio
#         for chunk in audio_clip.iter_chunks():
#             yield chunk
#             await asyncio.sleep(0.1)  # Dla asynchroniczności

# Trasa do strumienia audio
# @app.get('/audio_stream')
# async def audio_stream(request):
#     headers = {'Content-Type': 'audio/mpeg'}
#     return stream(play_audio_stream(), headers=headers)

@app.get("/")
async def root():
    return """
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
  
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)