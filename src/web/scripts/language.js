var currentLanguage = '', languageStrings = '';

const warn = document.getElementById('WARN');
async function fetchStrings(language) {
    currentLanguage = language
    languageStrings = await fetch(`languages/${language}.json`).then(response => response.json())

    warn.innerHTML = languageStrings.currentWarning
    
    document.querySelector('body').dispatchEvent(new Event('languagesLoaded'));
}

fetch(`languages/supported.json`).then(response => response.json()).then(supportedLanguages => {
    lang = navigator.language
    if (supportedLanguages.includes(lang)) fetchStrings(lang); // Fetch strings
    else fetchStrings("en")
})