# WhisperX SRT Cleaner

Remove artificial subtitles that WhisperX incorrectly generates during silence.

## Quick Start

```bash
python clean_whisperx_output.py input.srt --output cleaned.srt
```

## The purpose of cleaning your WhisperX output

Whisper and WhisperX produce junk subtitles that are purely imaginary. There is no matching dialogue, no audio cue to create such a subtitle, beyond the existence of silence.

### Why is it a problem?

The presence of a junk subtitle takes you out of the experience.

It's an interruption that reminds you the TV show isn't really happening, the movie scene is fiction, akin to a moment of bad acting or a boom mic being visible in the shot.

### What do these junk subtitles look like?

In French media it looks like this:

- Sous-titrage ST' 501
- sous-titrage par Amara.org
- sous-titrage fr
- Sous-titrage FR 2021
- Sous-titrage Société Radio-Canada
- Sous-titrage MFP
- Abonnez-vous
- Merci d'avoir regardé cette vidéo !
- Merci à tous 

None of these texts are actually in the speech being transcribed. 

Why is it there?

Because in Whisper's training data was improperly cleaned. This is the best explanation.

### How do I use this script?

Modify the junk_patterns.py array to contain a RegEx pattern for your own target language's junk subtitle content.

If you are not a programmer (or even if you are) you will likely need ChatGPT or Claude to write them for you. You give ChatGPT the text you wish to remove from all of your subtitle files and say, "Give me a RegEx that covers this case." You then put whatever RegEx GPT gives you as a replacement for the ones that are presently there. You must build up your own set of them over time.

(If you are using WhisperX for French media, you can leave the phony subtitle patterns as is.)

Once you have a collection of subtitles you wish to remove, you then place the script in your subtitle production pipeline.

It goes like this:

1. You use FFmpeg to take the .wav file out of the source video.
2. You use WhisperX on that .wav file to generate a .srt.
3. Here you use the clean_whipserx_output.py script on that output .srt.
4. You use the cleaner script's output as the content you put back into the original video.

