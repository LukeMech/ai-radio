document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlayingImageWait = document.getElementById('currently-playing-image-wait');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');
    currentlyPlayingTitle.innerHTML = '...'
    currentlyPlayingAuthor.innerHTML = '...'

    socket.on('trackChange', args => {
        currentlyPlayingTitle.innerHTML = args.title
        currentlyPlayingAuthor.innerHTML = args.author
        currentlyPlayingImage.src = args.thunbnail
        if(!args.thunbnail) currentlyPlayingImage.src = '/static/radio.ico' 
        currentlyPlayingImageWait.classList.add('hidden')
        currentlyPlayingImage.classList.remove('hidden')
        // args.duration, args.time (how many already played)
    });
    socket.on('disconnect', () => {
        currentlyPlayingTitle.innerHTML = '...'
        currentlyPlayingAuthor.innerHTML = '...'
        currentlyPlayingImage.classList.add('hidden')
        currentlyPlayingImageWait.classList.remove('hidden')
    });
})