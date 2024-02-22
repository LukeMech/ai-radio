document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlayingImageWait = document.getElementById('currently-playing-image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    const additional = document.getElementById('currently-playing-ev');
    currentlyPlayingTitle.innerHTML = '...'
    currentlyPlayingAuthor.innerHTML = '...'

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
        // args.duration, args.time (how many already played)
    });
    socket.on('disconnect', () => {
        currentlyPlayingTitle.innerHTML = '...'
        currentlyPlayingAuthor.innerHTML = '...'
        currentlyPlayingImage.classList.add('hidden')
        currentlyPlayingImageWait.classList.remove('hidden')
        additional.innerHTML = ''
    });
})