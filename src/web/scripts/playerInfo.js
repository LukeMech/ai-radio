// When main script loaded
document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const imagesWait = document.getElementsByClassName('image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    const additional = document.getElementById('currently-playing-additional');
    const timerElement = document.getElementById("currently-playing-timer");
    const nextInQueue = document.getElementById('next-in-queue');
    nextInQueue.innerHTML = languageStrings.nextInQueue + ':'
    const queueBox = document.getElementById('queue-box');
    const queueDiv = document.getElementById('queue-elements');
    const queueElementConstructor = `
        <div class="player-info">
            <div class="images">
                <img src={img}>
            </div>
            <div class="text-info">
                <b><p class="title">{title}</p></b>
                <p class="author">{author}</p>
            </div>
        </div>
        <p class="timer">{duration}</p>
    `;
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
        imagesWait[0].classList.add('hidden')
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
    });

    socket.on('queueChange', args => {
        queueDiv.innerHTML = ""
        queueBox.classList.add('hidden')
        args.forEach(el => {
            const construct = queueElementConstructor
                                .replace('{img}', socket.io.uri + '/' + el.thumbnail)
                                .replace('{title}', el.title)
                                .replace('{author}', el.author)
                                .replace('{duration}', formatDuration(el.duration));
            queueDiv.innerHTML += construct
        });
        queueBox.classList.remove('hidden')
    });

    // When disconnected
    socket.on('disconnect', () => {
        clearInterval(currentUpdateInterval) // Stop timer
        timerElement.textContent = ''
        currentlyPlayingTitle.classList.add('hidden')
        currentlyPlayingAuthor.classList.add('hidden')
        currentlyPlayingImage.src = ''
        imagesWait[0].classList.remove('hidden')
        additional.classList.add('hidden')
        queueBox.classList.add('hidden')
    });

    document.querySelector('body').dispatchEvent(new Event('allLoaded'));  // Everything loaded!
})
