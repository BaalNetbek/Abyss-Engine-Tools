import os

# Set the directory to search for .wav files
sound_dir = 'sound'

# Set the output file to write the absolute paths to
output_file = 'file_list.txt'

# Open the output file in write mode
with open(output_file, 'w') as f:
    # Iterate over all files in the sound directory
    for root, dirs, files in os.walk(sound_dir):
        for file in files:
            # Check if the file is a .wav file
            if file.endswith('.wav'):
                # Get the absolute path of the file
                abs_path = os.path.abspath(os.path.join(root, file))
                # Write the absolute path to the output file
                f.write(abs_path + '\n')