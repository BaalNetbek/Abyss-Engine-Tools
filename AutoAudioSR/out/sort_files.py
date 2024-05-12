import os
import shutil
import hashlib

script_dir = os.path.dirname(__file__)

# Navigate to the parent directory
parent_dir = os.path.dirname(script_dir)

# Define the sound list file path
sound_list_file = os.path.join(parent_dir, 'sound_list.txt')

# Read the sound list file
with open(sound_list_file, 'r') as f:
    mask = [os.path.splitext(os.path.basename(line.strip()))[0] for line in f.readlines()]

# Define the source directory
source_dir = script_dir

# Define the destination directory
dest_dir = os.path.join(script_dir, "sorted_out")

# Create the destination directory if it doesn't exist
os.makedirs(dest_dir, exist_ok=True)

# Function to calculate the SHA-256 hash of a file
def get_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)  # Read file in 64KB chunks
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

# Loop through each element in the mask list
for mask_element in mask:
    # Create a subdirectory for the current mask element
    mask_dir = os.path.join(dest_dir, mask_element)
    os.makedirs(mask_dir, exist_ok=True)

    # Dictionary to store file hashes in the destination directory
    dest_file_hashes = {}

    # Loop through all files in the source directory
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            # Check if the file name starts with the current mask element
            if file.startswith(mask_element):
                # Construct the source and destination file paths
                src_path = os.path.join(root, file)
                dest_file_path = os.path.join(mask_dir, file)

                # Calculate the file hash
                file_hash = get_file_hash(src_path)

                # Create a unique destination file path with the hash
                
                dest_file_path = dest_file_path.replace('.wav', f"_{file_hash[:8]}.wav")

                # Check if the file hash already exists in the destination directory
                if file_hash not in dest_file_hashes:
                    try:
                        # Copy the file to the destination directory
                        shutil.copy2(src_path, dest_file_path)
                        print(f"Copied {file} to {dest_file_path}")
                    except Exception as e:
                        print(f"Error copying {file}: {e}")

                    # Add the file hash and name to the dictionary
                    dest_file_hashes[file_hash] = dest_file_path
                else:
                    # File with the same hash already exists, skip copying
                    print(f"Skipped {file} (same hash as {os.path.basename(dest_file_hashes[file_hash])})")
