#! /usr/bin/python3.8

import numpy as np


def contains_non_numbers(arr):
    # Check for NaN and Inf in arrays that support such operations
    if arr.dtype.kind in "fc":  # f: floating-point, c: complex floating-point
        if np.isnan(arr).any() or np.isinf(arr).any():
            return True

    # Check for non-numeric types in object arrays
    if arr.dtype == object:
        for x in arr:
            if not isinstance(x, (int, float, complex, np.number)):
                return True

    return False


def filter_numeric_elements(arr):
    # For arrays of numeric types, filter out NaN and Inf values
    if arr.dtype.kind in "fc":  # Floating-point or complex floating-point
        filtered_arr = arr[np.isfinite(arr)]
        return filtered_arr

    # For object arrays, filter out non-numeric types
    elif arr.dtype == object:
        numeric_elements = [
            x
            for x in arr
            if isinstance(x, (int, float, complex, np.number)) and not np.isnan(x)
        ]
        return np.array(numeric_elements, dtype=object)

    # If none of the above, return the array as is
    return arr


def bytes_to_chunks(byte_array, chunk_size, dtype=np.float32):
    element_size = np.dtype(dtype).itemsize
    buffer_size = len(byte_array)

    # Ensure the buffer size is a multiple of the element size
    if buffer_size % element_size != 0:
        # Trim the buffer to make it fit, this will remove the last few bytes:
        byte_array = byte_array[: buffer_size - (buffer_size % element_size)]

    # Now convert the buffer to a numpy array
    audio_np = np.frombuffer(byte_array, dtype=dtype)

    audio_np = filter_numeric_elements(audio_np)

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
            chunks.append(chunk.reshape((chunk.shape[0], 1)))

    return chunks
