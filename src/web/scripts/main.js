var socket;
const awsApi = 'https://raw.githubusercontent.com/LukeMech/ai-radio-host/main/src/awsfun.url';

document.querySelector('body').addEventListener('languagesLoaded', () => {
    const sessionIDText = document.getElementById('session-id');
    sessionIDText.innerHTML = languageStrings.connecting

    const playPauseButton = document.getElementById('play-pause-button');
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isFirefox = navigator.userAgent.includes("Firefox");
    const useMediaButtons = ('mediaSession' in navigator)
    let serverLOADED, stalled, paused, linkNum = -1
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
                { src: "radio.ico" }
            ]
        });
        mediaStoppedMetadata = new MediaMetadata({
            title: languageStrings.stopped,
            artist: 'LukeMech | AI Radio | 2024',
            artwork: [
                { src: "radio.ico" }
            ]
        });
        loadingMetadata = new MediaMetadata({
            title: languageStrings.loading,
            artist: 'LukeMech | AI Radio | 2024',
            artwork: [
                { src: "radio.ico" }
            ]
        })
        connectingMetadata = new MediaMetadata({
            title: languageStrings.connecting,
            artist: 'LukeMech | AI Radio | 2024',
            artwork: [
                { src: "radio.ico" }
            ]
        })
    }
    
    // Connect to WebSocket
    
    socket = io({
        extraHeaders: {
            "id": id,
        }
    });
    
    socket.on('connect', () => {
        serverLOADED=true
        console.log('Authorized via websocket');
        sessionIDText.innerHTML = languageStrings.sessionID + ": " + id
    });
    socket.on('disconnect', () => {
        serverLOADED=false
        console.log('Disconnected from server');
        sessionIDText.innerHTML = languageStrings.connecting
    });
    // Handle first load when just connected
    socket.on('trackChange', () => {
        serverLOADED=true
        if(playPauseButton.classList.contains('loading')) {
            audioStart() 
        }
    })

    function connectWithRetry(url) { 
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error("Can't fetch link from AWS");
                }
                return response.text();
            })
            .then(data => {
                serverUrl = data;
                socket.io.uri = data;
            })
            .catch(() => {
                console.error("Can't fetch link from AWS");
            });
    }
    
    socket.on('connect_error', () => {
        setTimeout(() => connectWithRetry(awsApi), 20000);
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
        if(paused) return
        stalled = true
        audioStop()
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        setTimeout(() => {
            stalled = false
            audioStart()
        }, 500);
    };
    const pausedAndWaitingHandler = async () => {
        if(stalled) return
        paused = true
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        audioStop()

        const waitForPlay = () => {
            return new Promise(resolve => {
                const checkPaused = () => {
                    if (!audio.paused) {
                        resolve(); // Resolve the promise when audio.paused becomes false
                    } else {
                        setTimeout(checkPaused, 500);
                    }
                };
                checkPaused(); // Start checking immediately
            });
        };

        await waitForPlay();

        // Aaaaand exec function
        paused = false
        stalledHandler()
    }
    
    function audioStop() {
        if(useMediaButtons) {
            navigator.mediaSession.metadata = mediaStoppedMetadata
            navigator.mediaSession.playbackState = 'paused'
        }
        try {
            socket.emit('musicstop', id)
            audio.removeEventListener("pause", pausedAndWaitingHandler);
            audio.removeEventListener("loadeddata", loadedDataHandler);
            audio.removeEventListener("error", errorHandler);
            audio.removeEventListener("stalled", stalledHandler);
            audio.removeEventListener("ended", stalledHandler);
            audio.pause();
        }
        catch (err) {}
    }
    function audioStart() {
        if (!serverLOADED) {
            playPauseButton.classList.remove('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.add('loading')
            if(useMediaButtons) {
                navigator.mediaSession.metadata = connectingMetadata
                navigator.mediaSession.playbackState = 'playing'
            }
            return
        }
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        if(!isMobile || isFirefox) audio.src = ''
        audio = new Audio(serverUrl + '/listen?id=' + id);
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
        audio.addEventListener('pause', pausedAndWaitingHandler);
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
        else if (!playPauseButton.classList.contains('loading') && serverLOADED) {
            audioStart(true)
        }
        else if (!serverLOADED) {
            playPauseButton.classList.remove('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.add('loading')
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

    document.querySelector('body').dispatchEvent(new Event('mainLoaded'));
});