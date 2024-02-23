document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlayingImageWait = document.getElementById('currently-playing-image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    const additional = document.getElementById('currently-playing-ev');
    const timerElement = document.getElementById("currently-playing-timer");
    const playPauseButton = document.getElementById('play-pause-button');

    currentlyPlayingTitle.innerHTML = '...'
    currentlyPlayingAuthor.innerHTML = '...'
    let duration = -1, playtime = -1, currentUpdateInterval;

    function formatDuration(durationInSeconds) {
        durationInSeconds = Math.floor(durationInSeconds);
        const minutes = Math.floor(durationInSeconds / 60);
        const seconds = durationInSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }   
    function updateTimer() {
        timerElement.textContent = languageStrings.nexttrackin + ': '+ formatDuration(duration - playtime);
        playtime++;
    }

    socket.on('trackChange', args => {
        clearInterval(currentUpdateInterval);
        currentlyPlayingTitle.innerHTML = args.title
        currentlyPlayingAuthor.innerHTML = args.author
        // Eurovision song detected
        additional.classList.remove('hidden')
        if(args.additional.ev) {
            const year = args.additional.ev.split(';')[0]
            const countryISO = args.additional.ev.split(';')[1]
            additional.innerHTML = languageStrings.eurovision + ' ' + year + '<br>' + languageStrings[countryISO]
        }
        // New song detected
        else if(args.additional.n) {
            additional.innerHTML = languageStrings.new
        }
        else additional.classList.add('hidden')
        currentlyPlayingImage.src = serverUrl + '/' + args.thumbnail
        currentlyPlayingImageWait.classList.add('hidden')
        currentlyPlayingImage.classList.remove('hidden')
        
        duration = args.duration
        playtime = args.time
        updateTimer()
        currentUpdateInterval = setInterval(updateTimer, 1000);
    });

    socket.on('disconnect', () => {
        clearInterval(currentUpdateInterval)
        currentlyPlayingTitle.innerHTML = ''
        currentlyPlayingAuthor.innerHTML = ''
        currentlyPlayingImage.classList.add('hidden')
        currentlyPlayingImageWait.classList.remove('hidden')
        additional.innerHTML = '...'
        timerElement.textContent = ''
    });

    playPauseButton.classList.remove('loading')
    playPauseButton.classList.add('play')
})
