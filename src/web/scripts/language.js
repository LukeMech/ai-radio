var currentLanguage, languageStrings // Declare global variables
// Fetch strings based on language
async function fetchStrings(language) {
    currentLanguage = language
    languageStrings = await fetch(`languages/${language}.json`).then(response => response.json())

    // Loaded!
    document.querySelector('body').dispatchEvent(new Event('languagesLoaded'));
}

// Check if language is supported, then fetch strings
fetch(`languages/supported.json`).then(response => response.json()).then(supportedLanguages => {
    lang = navigator.language
    if (supportedLanguages.includes(lang)) fetchStrings(lang); // Fetch strings
    else fetchStrings("en")
})