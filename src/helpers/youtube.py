import yt_dlp, random, string, subprocess, os
from youtube_title_parse import get_artist_title

def downloadWavFromUrl(url, callback):
    ERR=None; title=None; artist=None; fpath=None; ext=None; thunb=None
    try:
        ext = 'wav'
        fpath = 'tmp/' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

        ydl_opts = {
            'format': 'bestaudio/best',
            'external_downloader' : 'aria2c',
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
        subprocess.run([
            'ffmpeg', '-i', filename + '.' + 'tmp', 
            '-af', 'silenceremove=start_periods=1:start_duration=1:start_threshold=-60dB:detection=peak,aformat=dblp,areverse,silenceremove=start_periods=1:start_duration=1:start_threshold=-60dB:detection=peak,aformat=dblp,areverse', 
            filename
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(filename + '.' + 'tmp')

        try:
            artist, title = get_artist_title(info_dict.get('title', None))
        except:
            artist = info_dict.get('uploader', None)
            title = info_dict.get('title', None)
            
        if(os.path.exists(fpath + '.' + 'webp')):
            thunb = 'webp'
        elif(os.path.exists(fpath + '.' + 'jpg')):
            thunb = 'jpg'
        elif(os.path.exists(fpath + '.' + 'png')):
            thunb = 'png'
        else:
            thunb = None
    
    except Exception as e:
        ERR = e

    # Title, author, filepath, extension, thumbnail
    callback(title, artist, fpath, ext, thunb, ERR)
