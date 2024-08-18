The ninja game from DaFluffyPotato

- [video](https://www.youtube.com/watch?v=2gABYM5M0ww)

Additional changes were made to make it run in the browser.

- All the audio files were converted from .wav to .ogg
- Asyncio sleep was inserted in the main loop.
- Moved the screen to global scope and added a press any key screen before loading the audio.

```
python -m pygbag --PYBUILD 3.12 --template noctx.tmpl .
```
