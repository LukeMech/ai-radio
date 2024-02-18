from pydub import AudioSegment
import os

def m4a_to_mp3(in_file, out_file):
    # Load the M4A file
    audio = AudioSegment.from_file(in_file, format="mp3")

    # Export the audio to MP3 format
    audio.export(out_file, format="wav")

if __name__ == "__main__":
    # Specify the input M4A file and output MP3 file
    in_file = "test.mp3"
    out_file = "test.wav"

    # Convert M4A to MP3
    m4a_to_mp3(in_file, out_file)

    print("Conversion complete.")
