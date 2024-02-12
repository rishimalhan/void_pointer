import numpy as np


def bytes_to_chunks(byte_array, chunk_size, dtype=np.int16):
    """
    Splits the byte array into chunks of the specified size and converts
    each chunk into a NumPy array.

    Parameters:
    - byte_array: The byte array containing the audio data.
    - chunk_size: The size of each chunk in bytes.
    - dtype: The NumPy data type to use for the conversion, default is np.int16.

    Returns:
    - A list of NumPy arrays, each representing a chunk of the original byte array.
    """

    # Calculate the number of elements per chunk. dtype().itemsize gives the size in bytes of each item.
    elements_per_chunk = chunk_size // np.dtype(dtype).itemsize

    # Calculate the total number of chunks
    total_chunks = len(byte_array) // chunk_size

    # Initialize a list to hold the chunks
    chunks = []

    for i in range(total_chunks):
        # Calculate the start and end of the current chunk
        start = i * chunk_size
        end = start + chunk_size

        # Slice the byte_array to get the current chunk and convert to a NumPy array
        chunk = np.frombuffer(byte_array[start:end], dtype=dtype)

        # Ensure the chunk is the expected size, otherwise it's a partial chunk and should be ignored or handled differently
        if chunk.size == elements_per_chunk:
            chunks.append(chunk)

    return chunks
