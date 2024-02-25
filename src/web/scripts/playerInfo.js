// When main script loaded
document.querySelector('body').addEventListener('mainLoaded', () => {
    const nextInQueue = document.getElementById('next-in-queue');
    nextInQueue.innerHTML = languageStrings.nextInQueue + ':'
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlaying = document.getElementById('currently-playing-info');
    const imagesWait = document.getElementsByClassName('image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    const additional = document.getElementById('currently-playing-additional');
    const timerElement = document.getElementById("currently-playing-timer");
    const player = document.getElementById('player');
    const queueBox = document.getElementById('queue-box');
    const queueDiv = document.getElementById('queue-elements');
    const queueElementConstructor = `
        <div id="{i}" style="transition: opacity 1s ease-in-out, height 0.5s ease-in-out; height: 0px; opacity: 0">
            <div class="player-info">
                <div class="images">
                    <img src={img}>
                </div>
                <div class="text-info" >
                    <b><p class="title">{title}</p></b>
                    <p class="author">{author}</p>
                </div>
            </div>
            <p class="timer">{duration}</p>
        </div>
    `;
    let duration = -1, playtime = -1, currentUpdateInterval, updatingQueue;

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
        console.log(updatingQueue)
        while(updatingQueue) {
            await new Promise(r => setTimeout(r, 300));
            args.time+=0.3
        }
        updatingQueue = true;
        clearInterval(currentUpdateInterval); // Stop timer
        let ph = 90
        // If should refresh queue
        const shouldRefresh = currentlyPlayingImage.classList.contains('hidden') ? false : true
        
        player.style.opacity = 0
        
        let playerInfo
        if(shouldRefresh) {
            playerInfo = document.getElementById(0)
            // Hide first in queue
            playerInfo.style.height = 0
            playerInfo.style.opacity = 0
            for (let i = 1; i <= queueDiv.childElementCount; i++) {
                try {
                    const el = document.getElementById(i)
                    el.id = i - 1
                } catch (e) {}
            }
        }

        await new Promise(r => setTimeout(r, 900));
        args.time+=0.9

        if(shouldRefresh) playerInfo.remove()
       
        currentlyPlayingImage.src = socket.io.uri + '/' + args.thumbnail // Set image
        currentlyPlayingImage.classList.remove('hidden')
        imagesWait[0].classList.add('hidden')
        currentlyPlayingTitle.innerHTML = args.title
        currentlyPlayingAuthor.innerHTML = args.author
        currentlyPlaying.classList.remove('hidden')

        additional.classList.remove('hidden')
        // Eurovision song detected
        if(args.additional.ev) {
            const year = args.additional.ev.split(';')[0]
            const countryISO = args.additional.ev.split(';')[1]
            additional.innerHTML = languageStrings.eurovision + ' ' + year + '<br>' + languageStrings[countryISO]
            ph+=55
        }
        // New song detected
        else if(args.additional.n) {
            additional.innerHTML = languageStrings.new
            ph+=35
        }
        // Else hide additional
        else additional.classList.add('hidden')
            
        // Show player again
        player.style.height = ph + 'px'
        player.style.opacity = 1

        // Update timer
        duration = args.duration
        playtime = args.time
        updateTimer()
        currentUpdateInterval = setInterval(updateTimer, 1000)

        await new Promise(r => setTimeout(r, 800));
        updatingQueue = false
    });

    socket.on('queueChange', async args => {
        console.log(updatingQueue)
        while(updatingQueue) {
            await new Promise(r => setTimeout(r, 300));
        }
        updatingQueue = true
        queueBox.classList.remove('hidden')
        queueConstruct = a => {
            const constr = queueElementConstructor
                                .replace('{i}', a)
                                .replace('{img}', socket.io.uri + '/' + args[a].thumbnail)
                                .replace('{title}', args[a].title)
                                .replace('{author}', args[a].author)
                                .replace('{duration}', formatDuration(args[a].duration));
            queueDiv.innerHTML += constr
        }
        let i = 0
        args.forEach(() => {
            queueConstruct(i)
            i++
        });
        i=0
        await new Promise(r => setTimeout(r, 100));
        args.forEach(() => {
            const anim = document.getElementById(i)
            anim.style.opacity = 1
            anim.style.height = '100px'
            i++
        })
        i=0
        await new Promise(r => setTimeout(r, 1000));
        // Make sure queue is up to date
        queueDiv.innerHTML = ''
        args.forEach(() => {
            queueConstruct(i)
            const doc = document.getElementById(i)
            doc.style.opacity = 1
            doc.style.height = '100px'
            i++
        })
        updatingQueue = false
    })

    // When disconnected
    socket.on('disconnect', () => {
        clearInterval(currentUpdateInterval) // Stop timer
        timerElement.textContent = ''
        currentlyPlaying.classList.add('hidden')
        currentlyPlayingImage.src = ''
        currentlyPlayingImage.classList.add('hidden')
        imagesWait[0].classList.remove('hidden')
        additional.classList.add('hidden')
        queueBox.classList.add('hidden')
        queueDiv.innerHTML = ''
    });

    document.querySelector('body').dispatchEvent(new Event('allLoaded'));  // Everything loaded!
})
