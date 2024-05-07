'''
AEZtractor - functions for unpacking and repacking .aez files. 
I know of only one which is res.aez packing assets of GoF3D symbian version.

You can use it directly running the this .py file after uncommenting bottom instructions.
'''

import os
import struct

def unpack_aez(input_file = 'res.aez', verbose = False):
    with open(input_file, 'rb') as f:
        while True:
            if verbose: print("\ncurnt adr: ",hex(f.tell()))
            path_size_byte = f.read(1)
            path_size = int.from_bytes(path_size_byte, byteorder='little', signed=False)
            if verbose: print("path size: ", path_size)
            file_path = f.read(path_size).decode('utf-8')
            if verbose: print("path size: ", file_path) 
            file_size_bytes = f.read(4)
            file_size = int.from_bytes(file_size_bytes, byteorder='little', signed=False)
            if verbose: print("file size: ", file_size)
            const_bytes = f.read(4)
            
            if(path_size == 0 and file_size == 0):
                break

            file_data = f.read(file_size)
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

                # Write path size
                path_size = len(rel_path)
                f.write(struct.pack('B', path_size))

                # Write path
                f.write(rel_path.encode('utf-8'))

                # Write file size
                file_size = os.path.getsize(file_path)
                f.write(struct.pack('<I', file_size))

                # Write constant bytes (4 bytes)
                f.write(b'\xFF\xFF\xFF\xFF')

                # Write file data
                with open(file_path, 'rb') as in_f:
                    f.write(in_f.read())

                if verbose:
                    print(f"Packed: {rel_path} ({file_size} bytes)")

        # Write end-of-archive marker (path size and file size both 0)
        f.write(struct.pack('BB', 0, 0))

    return None

# Example uses:

#unpack_aez('res.aez') 
#will unpack res.aez if it is in the same directory as the script


#will pack the folder data in script's current directory to a new archive
#pack_aez('data', "new_res.aez") 

#excacly the same calling the function without arguments
#pack_aez()
