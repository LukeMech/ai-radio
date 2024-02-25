// Link to file containing AWS link returning server link
const awsApiLink = 'https://raw.githubusercontent.com/LukeMech/ai-radio-host/main/src/awsfun.url';

var socket // Declare global variable
// When everything loaded and site is ready
document.querySelector('body').addEventListener('allLoaded', () => {
    const playPauseButton = document.getElementById('play-pause-button');
    playPauseButton.classList.remove('loading')
    playPauseButton.classList.add('play')
});

// When languages loaded
document.querySelector('body').addEventListener('languagesLoaded', () => {
    const sessionIDText = document.getElementById('session-id');
    sessionIDText.innerHTML = "Web"+": "+version
    const connStatus = document.getElementById('connStatus');
    const playPauseButton = document.getElementById('play-pause-button');
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isFirefox = navigator.userAgent.includes("Firefox");
    const useMediaButtons = ('mediaSession' in navigator)
    let serverLOADED, paused, stopping, starting
    let audio={paused:true}
    
    // Generate connection session ID
    function generateid() {
        return Math.random().toString(36).substring(2, 15)
    }
    const id = generateid()
    
    // Metadata for audio player
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
        reconnection: false,
        autoConnect: false,
        extraHeaders: {
            "id": id
        }
    });

    // Disconnection function
    const handleDisconnect = () => {
        if(!serverLOADED) return  // If something else already handling before disconnection

        connStatus.classList.remove('established')
        connStatus.classList.add('problem')
        serverLOADED=false
        console.log('Disconnected from server, retrying in 10secs...');
        sessionIDText.innerHTML = "Web"+": "+version

        if(!audio.paused || starting) stalledHandler()  // If audio wants to be loaded, abort

        // Connection retry in 10secs
        setTimeout(() => getNextLink(awsApiLink).then(localhostlink => getNextLink(localhostlink).then(link => connectWithRetry(link))), 10000);
    }
    
    // On connection
    socket.on('connect', () => {
        connStatus.classList.remove('problem')
        connStatus.classList.add('established')
        serverLOADED=true
        console.log('Authorized via websocket')
    });
    socket.on('serverVersion', v => {
        sessionIDText.innerHTML = "Web"+": "+version+" | " + "Backend"+": "+v + "<br>" + languageStrings.sessionID+": "+id
    })

    // Disconnection handlers
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleDisconnect);

    // Track change
    socket.on('trackChange', () => {
        connStatus.classList.remove('problem')
        connStatus.classList.add('established')
        serverLOADED=true

        if(playPauseButton.classList.contains('loading')) audioStart() // If audio wants to be played, play it!
    })

    socket.on('urlChanged', url => connectWithRetry(url, true))

    // Fetch and return next link, text from request
    async function getNextLink(url) {
        let response = {ok: false}
        try {response = await fetch(url, {cache: 'reload'})} catch (e) {}
        if (!response.ok) return console.error("Can't fetch link " + url);
        return await response.text();
    }

    // Try connection
    async function connectWithRetry(url, firstDisconnect=false) { 

        // Be sure server is online before trying socket connection
        let check = {ok: false}
        try {check = await fetch(url + '/' + generateid(), {cache: 'no-store'})} catch(e) {}
        if(!check.ok) {
            if(firstDisconnect) return socket.disconnect()  // If it was server sending link but it doesnt work (pretty uncommon, but still possible)

            // Else if it's standard check -> nope, offline -> retry
            setTimeout(() => getNextLink(awsApiLink).then(localhostlink => getNextLink(localhostlink).then(link => connectWithRetry(link))), 10000); // Retry in 10s
            return console.log('Server offline, retrying in 10secs...')
        }

        // If it's server url request
        if(firstDisconnect) {
            serverLOADED=false 
            socket.disconnect()
            if(!audio.paused || starting) stalledHandler()  // Restart audio stream if it's playing
        }

        // Connect!
        socket.io.uri = url;
        socket.connect()
    }
    
    getNextLink(awsApiLink).then(localhostlink => getNextLink(localhostlink).then(link => connectWithRetry(link)))  // Start connection on first load

    // When audio data is loaded by the browser
    const loadedDataHandler = () => {
        if (audio.readyState > 2) {
            // Audio loaded more than just first chunk
            if(useMediaButtons) {
                navigator.mediaSession.metadata = mediaPlayingMetadata
                navigator.mediaSession.playbackState = 'playing'
            }
            playPauseButton.classList.remove('loading');
            playPauseButton.classList.add('pause');
        }
    };

    // When there was error playing audio
    const errorHandler = () => {
        audioErr('Loading audio failed')
    };

    // If audio have problem loading, retry connection
    const stalledHandler = () => {
        playPauseButton.classList.add('loading')
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        audioStop()
        setTimeout(() => {
            if(paused) return
            audioStart()
        }, 500);
    };

    // User switched audio, so it automatically paused, handle it stopping stream and re-start stream when user returns
    const pausedAndWaitingHandler = async () => {
        paused = true
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        
        // Every 300ms check if user ended other audio
        const checkIfShouldResume = setInterval(() => {
            if(!audio.paused) {
                clearInterval(checkIfShouldResume)
                audioStop()
                paused = false
                audioStart()
            }
        }, 300);
    }

    // Audio stopping
    function audioStop() {
        // If already stopping stop execution
        if(stopping) return
        stopping = true
        if(useMediaButtons) {
            navigator.mediaSession.metadata = mediaStoppedMetadata
            navigator.mediaSession.playbackState = 'paused'
        }
        try {
            // Clear all audio info, send stop stream command to server
            socket.emit('musicstop', id)
            audio.removeEventListener("pause", pausedAndWaitingHandler);
            audio.removeEventListener("loadeddata", loadedDataHandler);
            audio.removeEventListener("error", errorHandler);
            audio.removeEventListener("stalled", stalledHandler);
            audio.removeEventListener("ended", stalledHandler);
            audio.pause();
        }
        catch (err) {}
        setTimeout(() => {
            starting = false
            stopping = false
        }, 500);
    }

    // Audio starting
    function audioStart() {
        if(starting) return    // If it's already starting stop execution

        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')

        // If server not connected, stop execution (it will be resumed on connection, look up to socket.on('trackChange')
        if (!serverLOADED) {
            if(useMediaButtons) {
                navigator.mediaSession.metadata = connectingMetadata
                navigator.mediaSession.playbackState = 'playing'
            }
            return
        }
        // If audio now is not yet stopped fully
        if (stopping) {
            return setTimeout(() => {
                audioStart()
            }, 500);
        }

        starting = true    // Audio starting
        if(!isMobile || isFirefox) audio.src = ''  // Added it to make sure stream is restarted

        audio = new Audio(socket.io.uri + '/listen?id=' + id);
        if (!audio.canPlayType('audio/mpeg')) return audioErr('Type not currently supported', '', false) // Can't really play audio here
        
        if(useMediaButtons) {
            navigator.mediaSession.metadata = loadingMetadata
            navigator.mediaSession.playbackState = 'playing'
        }
        // Add event listeners for audio
        audio.addEventListener("loadeddata", loadedDataHandler);
        audio.addEventListener('stalled', stalledHandler);
        audio.addEventListener('pause', pausedAndWaitingHandler);
        audio.addEventListener('ended', stalledHandler);

        audio.play()
        starting = false
    }

    // Error playing, repeat for trying to restore stream
    function audioErr(msg, err, repeat=true) {
        console.warn(msg)
        console.warn(err)
        if(repeat) stalledHandler()
    }
    
    // When play/pause clicked
    playPauseButton.addEventListener('click', function() {
        // If it's started or starting
        if (playPauseButton.classList.contains('pause') || playPauseButton.classList.contains('loading')) {
            playPauseButton.classList.add('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.remove('loading');
            audioStop()
        } 
        // If it's paused and server is fully loaded
        else if (!playPauseButton.classList.contains('loading') && serverLOADED) {
            audioStart()
        }
        // When it's paused but server not yet started (see socketio.on('connect'), it will detect class and start play when can)
        else if (!serverLOADED) {
            playPauseButton.classList.remove('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.add('loading')
        }
    });
    
    // If media controls are supported
    if(useMediaButtons) {
        // Audio paused or loading
        navigator.mediaSession.setActionHandler('play', function() {
            audioStart()
        });
        // Audio playing
        navigator.mediaSession.setActionHandler('pause', function() {
            audioStop()  
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.remove('loading');
            playPauseButton.classList.add('play')
        });
    }

    document.querySelector('body').dispatchEvent(new Event('mainLoaded'));  // Script loaded!
});
