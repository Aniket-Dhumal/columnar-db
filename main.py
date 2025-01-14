import os
import json
from flask import Flask, request, jsonify
import struct
import io

app = Flask(__name__)

MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB

# Function to get the TLV data
def write_tlv(file, value):
    if isinstance(value, int):
        type_byte = 1  # Integer type
        value_bytes = struct.pack('i', value)
    elif isinstance(value, float):
        type_byte = 2  # Float type
        value_bytes = struct.pack('d', value)
    elif isinstance(value, str):
        type_byte = 3  # String type
        value_bytes = value.encode('utf-8')
    else:
        type_byte = 0  # Unknown type
        value_bytes = b''

    length = len(value_bytes)
    file.write(struct.pack('B', type_byte))  # Write type
    file.write(struct.pack('I', length))     # Write length
    file.write(value_bytes)                  # Write value

# Function to manage file writing and ensure size constraints
def write_to_file(key, value):
    filename = f"{key}.tlv"
    file_mode = 'ab' if os.path.exists(filename) else 'wb'
    
    with open(filename, file_mode) as file:
        write_tlv(file, value)

    # Check if file size exceeds limit
    if os.path.getsize(filename) >= MAX_FILE_SIZE:
        # Rename file when limit exceeded
        new_filename = f"{key}.v0.tlv"  # First version of the file
        os.rename(filename, new_filename)
        # Create a new file after renaming
        with open(f"{key}.tlv", 'wb') as new_file:
            write_tlv(new_file, value)

@app.route('/elastic/_bulk', methods=['PUT'])
def bulk_insert():
    data = request.get_json()
    
    for record in data:
        for key, value in record.items():
            write_to_file(key, value)
    
    return jsonify({"message": "Data inserted successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
