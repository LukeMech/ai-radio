document.querySelector('body').addEventListener('mainLoaded', () => {
    const currentlyPlayingHello = document.getElementById('currently-playing');
    const currentlyPlayingTitle = document.getElementById('currently-playing-title');
    const currentlyPlayingAuthor = document.getElementById('currently-playing-author');
    currentlyPlayingHello.innerHTML = languageStrings.nowPlaying

    socket.on('trackChange', args => {
        currentlyPlayingTitle.innerHTML = args.title
        currentlyPlayingAuthor.innerHTML = args.author
        // args.duration, args.time (how many already played)
    });
    socket.on('disconnect', () => {
        currentlyPlayingTitle.innerHTML = '...'
        currentlyPlayingAuthor.innerHTML = '...'
    });
})