import yt_dlp, random, string, subprocess, os
from youtube_title_parse import get_artist_title

def downloadWavFromUrl(url, callback):
    ext = 'wav'
    fpath = 'tmp/' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': fpath,  # Save with the title as filename
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': ext,  # Save as .wav file
            'preferredquality': '192',
        },
        { 'key': 'SponsorBlock' }, 
        {
            'key': 'ModifyChapters',
            'remove_sponsor_segments': [
                'filler',
                'interaction',
                'intro',
                'music_offtopic',
                'outro',
                'preview',
                'selfpromo',
                'sponsor'
            ],
        }],
        'writethumbnail': True,  # Write thumbnail
        'merge_output_format': ext,  # Merge into .wav file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
    
    filename = fpath + '.' + ext
    os.rename(filename, filename + '.' + 'tmp')
    subprocess.run(['ffmpeg', '-i', filename + '.' + 'tmp', '-af', 'silenceremove=start_periods=1:start_duration=1:start_silence=0.05:start_threshold=0.02:stop_periods=1:stop_duration=1:stop_silence=0.05:stop_threshold=0.02', filename], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(filename + '.' + 'tmp')

    artist, title = get_artist_title(info_dict.get('title', None))

    # Title, author, filepath, extension, thumbnail
    callback(title, artist, fpath, ext, 'webp')
