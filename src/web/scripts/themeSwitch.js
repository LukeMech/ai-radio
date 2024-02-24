const toggleSwitch = document.querySelector('#theme-switch input[type="checkbox"]');

// If browser supports matchMedia and user prefers light mode
let prefersLightMode
if(window.matchMedia) prefersLightMode = window.matchMedia("(prefers-color-scheme: light)");

// Detect color scheme
function detectColorScheme(){
    let theme
    //matchMedia method not supported -> local storage is used to override OS theme settings
    if(!window.matchMedia) {
        if(localStorage.getItem("theme")){
            if(localStorage.getItem("theme") == "light") theme = "light";
            else theme = "dark";
        }
    } 
    else if (prefersLightMode.matches) theme = "light" // Prefers light theme
    else theme = "dark"

    // Set a 'data-theme' attribute
    if (theme=="light") {
         document.documentElement.setAttribute("data-theme", "light");
         toggleSwitch.checked = true; 
    }
    else {
        document.documentElement.setAttribute("data-theme", "dark");
        toggleSwitch.checked = true; 
    }
}

// Detect on launch
detectColorScheme();

// Function that changes the theme, and sets a localStorage variable to track the theme
function switchTheme() {
    // Is in light mode, changing to dark
    if (document.documentElement.getAttribute('data-theme') == "light") {
        localStorage.setItem('theme', 'dark');
        document.documentElement.setAttribute('data-theme', 'dark');
        toggleSwitch.checked = true;
    } 
    // Now in dark mode
    else {
        localStorage.setItem('theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
        toggleSwitch.checked = false;
    }
}

toggleSwitch.addEventListener('change', switchTheme) // Listener for changing themes by button
prefersLightMode.addEventListener('change', detectColorScheme) // Listener for changing themes by OS