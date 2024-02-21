document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    const currentlyPlayingImage = document.getElementById('currently-playing-image');

    socket.on('trackChange', args => {
        console.log(args)
        currentlyPlayingTitle.innerHTML = args.title
        currentlyPlayingAuthor.innerHTML = args.author
        currentlyPlayingImage.src = args.thunbnail
        if(!args.thunbnail) currentlyPlayingImage.src = '/static/radio.ico' 
        // args.duration, args.time (how many already played)
    });
    socket.on('disconnect', () => {
        currentlyPlayingTitle.innerHTML = '...'
        currentlyPlayingAuthor.innerHTML = '...'
        currentlyPlayingImage.src = '/static/radio.ico' 
    });
})