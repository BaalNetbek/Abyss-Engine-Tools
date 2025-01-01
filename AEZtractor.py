'''
AEZtractor - functions for unpacking and repacking .aez files. 
res.aez files can be found GoF3D Symbian and Zeebo versions. GoF2 for Meego and mabey some other Abyss Engine games.

You can use it directly running the this .py file after uncommenting bottom instructions.
'''

import os
import struct
import zlib

def unpack_aez(input_file = 'res.aez', verbose = False):
    with open(input_file, 'rb') as f:
        while True:
            if verbose: print("\ncurnt adr: ",hex(f.tell()))
            try:
                path_size = struct.unpack('B', f.read(1))[0]
            except struct.error as e:
                break
            if verbose: print("path size: ", path_size)
            file_path = f.read(path_size).decode('utf-8')
            if verbose: print("path size: ", file_path) 

            uncompressed_size = struct.unpack('<I', f.read(4))[0]
            if verbose: print("file size: ", uncompressed_size)
            compressed_size = struct.unpack('<i', f.read(4))[0]
            
            if compressed_size != -1:
                if verbose: 
                    print("comp size: ", compressed_size)
                    print("comp ratio: ", round(compressed_size/uncompressed_size, 2))
                unk = f.read(10)
                compressed_data = f.read(compressed_size-10)
                file_data = zlib.decompress(compressed_data, -zlib.MAX_WBITS)
            else:
                file_data = f.read(uncompressed_size)
            file_path = os.getcwd()+file_path
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if verbose: print(file_path)
            with open(file_path, 'wb') as out_f:
                out_f.write(file_data)
    return None
    
def pack_aez(input_dir = os.getcwd()+"/data", output_file = "new_res.aez", verbose=False):
    with open(output_file, 'wb') as f:
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, input_dir)
                rel_path = '/' + os.path.basename(input_dir) + '/' + rel_path.replace('\\', '/')

                f.write(struct.pack('B', len(rel_path)))
                f.write(rel_path.encode('utf-8'))
                file_size = os.path.getsize(file_path)
                f.write(struct.pack('<I', file_size))

                # Mark uncompressed files with 0xffffffff
                f.write(struct.pack('<i', -1))

                with open(file_path, 'rb') as in_f:
                    f.write(in_f.read())

                if verbose:
                    print(f"Packed: {rel_path} ({file_size} bytes)")

        # Write end-of-archive marker (path size and file size both 0)
        f.write(struct.pack('BB', 0, 0))
    return None

# Example uses:
"""unpack res.aez if it is in the same directory as the script"""
#unpack_aez('res.aez') 

"""pack the folder data in script's current directory to a new archive"""
#pack_aez('data', "new_res.aez") 

"""excacly the same calling the function without arguments"""
#pack_aez()
