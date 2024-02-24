var socket;
const awsApiLink = 'https://raw.githubusercontent.com/LukeMech/ai-radio-host/main/src/awsfun.url';

document.querySelector('body').addEventListener('languagesLoaded', () => {
    const sessionIDText = document.getElementById('session-id');
    const additional = document.getElementById('currently-playing-ev');
    sessionIDText.innerHTML = languageStrings.connecting
    additional.innerHTML = languageStrings.connecting

    const playPauseButton = document.getElementById('play-pause-button');
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
    const isFirefox = navigator.userAgent.includes("Firefox");
    const useMediaButtons = ('mediaSession' in navigator)
    let serverLOADED, paused, stopping, starting
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
        reconnection: false,
        autoConnect: false,
        extraHeaders: {
            "id": id
        }
    });

    const handleDisconnect = () => {
        setTimeout(() => getApiLink(awsApiLink).then(resp => connectWithRetry(resp)), 10000);

        serverLOADED=false
        console.log('Disconnected from server, retrying in 10secs...');
        sessionIDText.innerHTML = languageStrings.connecting
        return
    }
    
    socket.on('connect', () => {
        serverLOADED=true
        console.log('Authorized via websocket');
        sessionIDText.innerHTML = languageStrings.sessionID + ": " + id
    });
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleDisconnect);
    // Handle first load when just connected
    socket.on('trackChange', () => {
        serverLOADED=true
        if(playPauseButton.classList.contains('loading')) {
            audioStart() 
        }
    })

    async function getApiLink(url) {
        let response = {ok: false}
        try {response = await fetch(url, {cache: 'reload'})} catch (e) {}
        if (!response.ok) return console.error("Can't fetch link to AWS");
        return await response.text();
    }

    let n=0;
    async function connectWithRetry(url) { 

        let response = {ok: false}
        try {response = await fetch(url, {cache: 'reload'})} catch (e) {}
        if (!response.ok) {
            setTimeout(() => getApiLink(awsApiLink).then(resp => connectWithRetry(resp)), 10000); // Retry in 20s
            return console.error("Can't fetch link from AWS, retrying in 10secs...");
        }
        const data = await response.text();
        // const data = 'https://7c518bb813a8db.lhr.life'

        // Be sure server is online (without it, cors can start block and boom, whole page needs reload)
        console.log(data)
        let check = {ok: false}

        try {check = await fetch(data + '/' + n, {cache: 'no-store'})} catch(e) {}
        if(!check.ok) {
            setTimeout(() => getApiLink(awsApiLink).then(resp => connectWithRetry(resp)), 10000); // Retry in 10s
            n+=1
            return console.log('Server offline, retrying in 10secs...')
        }

        socket.io.uri = data;
        socket.connect()
    }
    
    getApiLink(awsApiLink).then(resp => connectWithRetry(resp))

    const loadedDataHandler = () => {
        if (audio.readyState >= 2) {
            audio.play();
        }
        if (audio.readyState > 2) {
            starting = false
            if(useMediaButtons) {
                navigator.mediaSession.metadata = mediaPlayingMetadata
                navigator.mediaSession.playbackState = 'playing'
            }
            playPauseButton.classList.remove('loading');
            playPauseButton.classList.add('pause');
        }
    };
    const errorHandler = () => {
        audioErr('Loading audio failed')
    };
    const stalledHandler = () => {
        audioStop()
        playPauseButton.classList.remove('play')
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        setTimeout(() => {
            if(paused) return
            audioStart()
        }, 500);
    };
    const pausedAndWaitingHandler = async () => {
        paused = true
        playPauseButton.classList.remove('pause')
        playPauseButton.classList.add('loading')
        const checkIfShouldResume = setInterval(() => {
            if(!audio.paused) {
                clearInterval(checkIfShouldResume)
                audioStop()
                paused = false
                audioStart()
            }
        }, 200);
    }
    
    function audioStop() {
        if(stopping) return
        stopping = true
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
        setTimeout(() => {
            starting = false
            stopping = false
        }, 500);
    }
    function audioStart() {
        if(starting) return
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
        if (stopping) {
            return setTimeout(() => {
                audioStart()
            }, 500);
        }
        starting = true
        if(!isMobile || isFirefox) audio.src = ''
        audio = new Audio(socket.io.uri + '/listen?id=' + id);
        if (!audio.canPlayType('audio/mpeg')) {
            return audioErr('Type not currently supported', '', false)
        }
        if(useMediaButtons) {
            navigator.mediaSession.metadata = loadingMetadata
            navigator.mediaSession.playbackState = 'playing'
        }
        audio.addEventListener("loadeddata", loadedDataHandler);
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
            audioStart()
        }
        else if (!serverLOADED) {
            playPauseButton.classList.remove('play')
            playPauseButton.classList.remove('pause')
            playPauseButton.classList.add('loading')
        }
    });
    
    if(useMediaButtons) {
        navigator.mediaSession.setActionHandler('play', function() {
            audioStart()
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