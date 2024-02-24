// When main script loaded
document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlayingImageWait = document.getElementById('currently-playing-image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    const additional = document.getElementById('currently-playing-ev');
    const timerElement = document.getElementById("currently-playing-timer");
    const playPauseButton = document.getElementById('play-pause-button');
    let duration = -1, playtime = -1, currentUpdateInterval;

    // Function for changing from seconds to pretty format
    function formatDuration(durationInSeconds) {
        durationInSeconds = Math.floor(durationInSeconds);
        const minutes = Math.floor(durationInSeconds / 60);
        const seconds = durationInSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }   
    // Update timer element
    function updateTimer() {
        timerElement.textContent = formatDuration(duration - playtime);
        playtime++;
    }

    // When server reported song change
    socket.on('trackChange', async args => {
        clearInterval(currentUpdateInterval); // Stop timer
        currentlyPlayingImage.src = socket.io.uri + '/' + args.thumbnail // Set image
        currentlyPlayingImageWait.classList.add('hidden')
        currentlyPlayingTitle.innerHTML = args.title
        currentlyPlayingAuthor.innerHTML = args.author
        currentlyPlayingTitle.classList.remove('hidden')
        currentlyPlayingAuthor.classList.remove('hidden')

        additional.classList.remove('hidden')
        // Eurovision song detected
        if(args.additional.ev) {
            const year = args.additional.ev.split(';')[0]
            const countryISO = args.additional.ev.split(';')[1]
            additional.innerHTML = languageStrings.eurovision + ' ' + year + '<br>' + languageStrings[countryISO]
        }
        // New song detected
        else if(args.additional.n) additional.innerHTML = languageStrings.new
        // Else hide additional
        else additional.classList.add('hidden')

        // Update timer
        duration = args.duration
        playtime = args.time
        updateTimer()
        currentUpdateInterval = setInterval(updateTimer, 1000)

        // Check connection status by fetching image
        let status = {ok: false}
        try {status = await fetch(currentlyPlayingImage.src, { method: 'HEAD' })} catch (e) {}
        if(!status.ok) return socket.disconnect() // Disconnect if url proabably changed
    });

    // When disconnected
    socket.on('disconnect', () => {
        clearInterval(currentUpdateInterval) // Stop timer
        timerElement.textContent = ''
        currentlyPlayingTitle.innerHTML = ''
        currentlyPlayingAuthor.innerHTML = ''
        currentlyPlayingTitle.classList.add('hidden')
        currentlyPlayingAuthor.classList.add('hidden')
        currentlyPlayingImage.src = ''
        currentlyPlayingImageWait.classList.remove('hidden')
        additional.innerHTML = languageStrings.connecting
        additional.classList.remove('hidden')
    });

    document.querySelector('body').dispatchEvent(new Event('allLoaded'));  // Everything loaded!
})
