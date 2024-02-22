document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlayingImageWait = document.getElementById('currently-playing-image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    const additional = document.getElementById('currently-playing-ev');
    const timerElement = document.getElementById("currently-playing-timer");

    currentlyPlayingTitle.innerHTML = '...'
    currentlyPlayingAuthor.innerHTML = '...'
    timerElement.innerHTML = '...'
    let duration = -1, playtime = -1;

    function formatDuration(durationInSeconds) {
        durationInSeconds = Math.floor(durationInSeconds);
        const minutes = Math.floor(durationInSeconds / 60);
        const seconds = durationInSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }   
    function updateTimer(intervalId) {
        if (duration > playtime || duration == -1) {
            clearInterval(intervalId);
            timerElement.textContent = "...";
        }
        timerElement.textContent = formatDuration(playtime) + ' / ' + duration;
        playtime++;
    }

    function updateTimerInterval() {
        updateTimer(null)
        const intervalId = setInterval(function() {
            updateTimer(intervalId);
        }, 1000);
    }

    socket.on('trackChange', args => {
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
        currentlyPlayingImage.src = args.thumbnail
        if(!args.thumbnail) currentlyPlayingImage.src = '/static/radio.ico' 
        currentlyPlayingImageWait.classList.add('hidden')
        currentlyPlayingImage.classList.remove('hidden')
        
        duration = formatDuration(args.duration)
        playtime = args.time
        updateTimerInterval()
    });
    socket.on('disconnect', () => {
        currentlyPlayingTitle.innerHTML = '...'
        currentlyPlayingAuthor.innerHTML = '...'
        currentlyPlayingImage.classList.add('hidden')
        currentlyPlayingImageWait.classList.remove('hidden')
        additional.innerHTML = ''
        duration = -1
    });
})