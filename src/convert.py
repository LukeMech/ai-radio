from pydub import AudioSegment
import os

def m4a_to_mp3(m4a_file, mp3_file):
    # Load the M4A file
    audio = AudioSegment.from_file(m4a_file, format="m4a")

    # Export the audio to MP3 format
    audio.export(mp3_file, format="mp3")

if __name__ == "__main__":
    # Specify the input M4A file and output MP3 file
    input_m4a_file = "test.m4a"
    output_mp3_file = "test.mp3"

    # Convert M4A to MP3
    m4a_to_mp3(input_m4a_file, output_mp3_file)

    print("Conversion complete.")
