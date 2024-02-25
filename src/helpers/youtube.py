import yt_dlp, random, string, subprocess, os
from youtube_title_parse import get_artist_title

# Somehow using aria2 prevents github actions from stopping...? 
# So, let's use it even though its slower (slows at the dwnld end)
def downloadWavFromUrl(url, callback, i, country):
    ERR=None; title=None; artist=None; fpath=None; ext=None; thunb=None
    try:
        ext = 'wav'
        fpath = 'tmp/' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        if not country: country = 'default'
        ydl_opts = {
            'format': 'bestaudio/best',
            'download_options': '-N 16',
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
            'merge_output_format': ext,  # Merge into .wav file,
        }
        if(country): ydl_opts['geo_bypass_country'] = country

        print(country, True)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = "https://www.youtube.com/watch?v=EAexp0w3H3c" # TESTING
            info_dict = ydl.extract_info(url, download=True)
        
        filename = fpath + '.' + ext
        os.rename(filename, filename + '.' + 'tmp')
        print("[info] Running silence cutter...", flush=True)
        subprocess.run(f'ffmpeg -hide_banner -loglevel error -i {filename + "." + "tmp"} -af silenceremove=start_periods=1:start_duration=1:start_threshold=-60dB:detection=peak,aformat=dblp,areverse,silenceremove=start_periods=1:start_duration=1:start_threshold=-60dB:detection=peak,aformat=dblp,areverse {filename}', shell=True)
        os.remove(filename + '.' + 'tmp')

        try:
            artist, title = get_artist_title(info_dict.get('title', None)) # type: ignore
        except:
            artist = info_dict.get('uploader', None) # type: ignore
            title = info_dict.get('title', None) # type: ignore
            
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
    callback(title, artist, fpath, ext, thunb, ERR, i)
