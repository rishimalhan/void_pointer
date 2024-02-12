#! /usr/bin/python3.8

import numpy as np


def bytes_to_chunks(byte_array, chunk_size, dtype=np.float32):
    element_size = np.dtype(dtype).itemsize
    buffer_size = len(byte_array)

    # Ensure the buffer size is a multiple of the element size
    if buffer_size % element_size != 0:
        # Trim the buffer to make it fit, this will remove the last few bytes:
        byte_array = byte_array[: buffer_size - (buffer_size % element_size)]

    # Now convert the buffer to a numpy array
    audio_np = np.frombuffer(byte_array, dtype=dtype)

    # Calculate the total number of chunks
    total_chunks = len(audio_np) // chunk_size

    # Initialize a list to hold the chunks
    chunks = []

    for i in range(total_chunks):
        # Calculate the start and end of the current chunk
        start = i * chunk_size
        end = start + chunk_size

        if end >= audio_np.shape[0]:
            continue

        # Slice the byte_array to get the current chunk and convert to a NumPy array
        chunk = audio_np[start:end]

        # Ensure the chunk is the expected size, otherwise it's a partial chunk and should be ignored or handled differently
        if chunk.shape[0] == chunk_size:
            chunks.append(chunk)

    return chunks
