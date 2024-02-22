//determines if the user has a set theme
var theme="dark";    //default to dark

//identify the toggle switch HTML element
const toggleSwitch = document.querySelector('#theme-switch input[type="checkbox"]');

let prefersLightMode
if(window.matchMedia) {
    prefersLightMode = window.matchMedia("(prefers-color-scheme: light)");
}

function detectColorScheme(){
    if(!window.matchMedia) {
        //matchMedia method not supported
        //local storage is used to override OS theme settings
        if(localStorage.getItem("theme")){
            if(localStorage.getItem("theme") == "light"){
                theme = "light";
            }
            else {
                theme = "dark";
            }
        }
    } else if(prefersLightMode.matches) {
        //OS theme setting detected as light
        theme = "light";
    }
    else theme = "dark";
    //light theme preferred, set document with a `data-theme` attribute
    if (theme=="light") {
         document.documentElement.setAttribute("data-theme", "light");
         toggleSwitch.checked = true; 
    }
    else {
        document.documentElement.setAttribute("data-theme", "dark");
        toggleSwitch.checked = true; 
    }
}
detectColorScheme();

//function that changes the theme, and sets a localStorage variable to track the theme between page loads
function switchTheme() {
    if (theme == "light") {
        localStorage.setItem('theme', 'dark');
        document.documentElement.setAttribute('data-theme', 'dark');
        toggleSwitch.checked = true;
    } else {
        localStorage.setItem('theme', 'light');
        document.documentElement.setAttribute('data-theme', 'light');
        toggleSwitch.checked = false;
    }
}

//listener for changing themes
toggleSwitch.addEventListener('change', switchTheme);

prefersLightMode.addEventListener('change', detectColorScheme);