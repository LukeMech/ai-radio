const toggleSwitch = document.querySelector('#theme-switch input[type="checkbox"]');
const prefersLightMode = window.matchMedia("(prefers-color-scheme: light)"); // OS setting

// Function that changes/refreshes the theme, and sets a localStorage variable to track the theme
function refreshTheme(doNotSwitch=false) {
    document.documentElement.removeAttribute('data-theme-auto');
    // Is in light mode, changing to dark
    if ((!doNotSwitch && localStorage.getItem('theme') == "light") || (doNotSwitch && localStorage.getItem('theme') == "dark")) {
        localStorage.setItem('theme', 'dark');
        document.documentElement.setAttribute('data-theme', 'dark');
    } 
    // Now in dark mode
    else if ((!doNotSwitch && localStorage.getItem('theme') == "dark") || (doNotSwitch && localStorage.getItem('theme') == "auto")) {
        // Move to auto
        localStorage.setItem('theme', 'auto');
        document.documentElement.setAttribute('data-theme-auto', true);
        // If OS is in light mode, match
        if (prefersLightMode.matches) document.documentElement.setAttribute('data-theme', 'light');
        // If OS is in dark mode, match
        else document.documentElement.setAttribute('data-theme', 'dark');
    }
    // Now in auto mode
    else {
        // Move to light
        localStorage.setItem('theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
    }
    console.log(localStorage.getItem('theme'))
}

refreshTheme(true)
toggleSwitch.addEventListener('change', () => refreshTheme()) // Listener for changing themes by button
prefersLightMode.addEventListener('change', () => refreshTheme(true)) // Listener for changing themes by OS