document.querySelector('body').addEventListener('languagesLoaded', () => {
    const sessionIDText = document.getElementById('session-id');
    sessionIDText.innerHTML = languageStrings.connecting

    const playPauseButton = document.getElementById('play-pause-button');
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isFirefox = navigator.userAgent.includes("Firefox");
    const useMediaButtons = ('mediaSession' in navigator)
    let connectedToServer = false;
    let audio={paused:true}
    
    function generateid() {
        return Math.random().toString(36).substring(2, 15)
    }
    const id = generateid()
    
    let mediaPlayingMetadata, mediaStoppedMetadata, loadingMetadata, connectingMetadata
    if(useMediaButtons) {
        mediaPlayingMetadata = new MediaMetadata({
            title: 'AI Radio | 2024',
            artist: 'LukeMech',
            artwork: [
                { src: "/static/radio.ico" }
            ]
        });
        mediaStoppedMetadata = new MediaMetadata({
            title: languageStrings.stopped,
            artist: 'LukeMech | AI Radio | 2024',
            artwork: [
                { src: "/static/radio.ico" }
            ]
        });
        loadingMetadata = new MediaMetadata({
            title: languageStrings.loading,
            artist: 'LukeMech | AI Radio | 2024',
            artwork: [
                { src: "/static/radio.ico" }
            ]
        })
        connectingMetadata = new MediaMetadata({
            title: languageStrings.connecting,
            artist: 'LukeMech | AI Radio | 2024',
            artwork: [
                { src: "/static/radio.ico" }
            ]
        })
    }
    
    // Connect to WebSocket
    const socket = io({
        extraHeaders: {
            "id": id,
        }
    });
    socket.on('connect', function() {
        console.log('Authorized via websocket');
        sessionIDText.innerHTML = languageStrings.sessionID + ": " + id
        connectedToServer = true
    });
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        sessionIDText.innerHTML = languageStrings.connecting
        connectedToServer = false
    });
    
    const loadedDataHandler = () => {
        if (audio.readyState >= 2) {
            audio.play();
        }
        if (audio.readyState > 2) {
            if(useMediaButtons) {
                navigator.mediaSession.metadata = mediaPlayingMetadata
                navigator.mediaSession.playbackState = 'playing'
            }
            playPauseButton.classList.remove('loading');
            playPauseButton.classList.add('pause');
        }
    };
    const errorHandler = err => {
        audioErr('Loading audio failed', err)
    };
    const stalledHandler = () => {
        audioStop()
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        setTimeout(() => {
            audioStart()
        }, 2000);
    };
    const pausedHandler = () => {
        audioStop()
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.remove('loading');
        playPauseButton.classList.add('play');
        audio.src = ''
    }
    
    function audioStop() {
        if(useMediaButtons) {
            navigator.mediaSession.metadata = mediaStoppedMetadata
            navigator.mediaSession.playbackState = 'paused'
        }
        socket.emit('musicstop', id)
        try {
            audio.removeEventListener("pause", pausedHandler);
            audio.removeEventListener("loadeddata", loadedDataHandler);
            audio.removeEventListener("error", errorHandler);
            audio.removeEventListener("stalled", stalledHandler);
            audio.removeEventListener("ended", stalledHandler);
            audio.pause();
        }
        catch (err) {}
    }
    function audioStart(ignorePlayClass=false) {
        if(playPauseButton.classList.contains('play') && !ignorePlayClass) return
        if (!connectedToServer) {
            playPauseButton.classList.remove('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.add('loading')
            if(useMediaButtons) {
                navigator.mediaSession.metadata = connectingMetadata
                navigator.mediaSession.playbackState = 'playing'
            }
    
            setTimeout(() => {
                audioStart()
            }, 2000);
            return
        }
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        if(!isMobile || isFirefox) audio.src = ''
        audio = new Audio('/listen?id=' + id);
        if (!audio.canPlayType('audio/mpeg')) {
            return audioErr('Type not currently supported', '', false)
        }
    
        if(useMediaButtons) {
            navigator.mediaSession.metadata = loadingMetadata
            navigator.mediaSession.playbackState = 'playing'
        }
        audio.addEventListener("loadeddata", loadedDataHandler);
        audio.addEventListener('error', errorHandler);
        audio.addEventListener('stalled', stalledHandler);
        audio.addEventListener('pause', pausedHandler);
        audio.addEventListener('ended', stalledHandler);
    }
    function audioErr(msg, err, repeat=true) {
        console.warn(msg)
        console.warn(err)
        if(repeat) stalledHandler()
    }
    
    playPauseButton.addEventListener('click', function() {
    
        if (playPauseButton.classList.contains('pause') || playPauseButton.classList.contains('loading')) {
            playPauseButton.classList.add('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.remove('loading');
            audioStop()
        } 
        else if (!playPauseButton.classList.contains('loading')) {
            audioStart(true)
        }
    });
    
    if(useMediaButtons) {
        navigator.mediaSession.setActionHandler('play', function() {
            audioStart(true)
        });
        navigator.mediaSession.setActionHandler('pause', function() {
            audioStop()  
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.remove('loading');
            playPauseButton.classList.add('play')
        });
    }

    playPauseButton.classList.remove('play-loading')
    playPauseButton.classList.add('play')
});