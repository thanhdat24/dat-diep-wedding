OPTIONAL LOCAL MUSIC

Website currently uses the music URL configured in js/config.js.
For the most reliable Vercel deployment, put your MP3 here as:

assets/audio/wedding.mp3

Then change js/config.js:

track: "assets/audio/wedding.mp3",

Using a local MP3 avoids depending on an external audio host.
