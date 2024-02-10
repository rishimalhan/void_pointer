import grpc
import ndarray_pb2
import ndarray_pb2_grpc
import numpy as np


async def run():
    async with grpc.aio.insecure_channel("localhost:50051") as channel:
        stub = ndarray_pb2_grpc.NdarrayServiceStub(channel)
        # Create a NumPy ndarray and serialize it to bytes
        ndarray = np.array([1, 2, 3], dtype=np.float32)
        ndarray_bytes = ndarray.tobytes()
        response = await stub.SendNdarray(
            ndarray_pb2.NdarrayRequest(ndarray=ndarray_bytes)
        )
        print("Server response:", response.message)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
