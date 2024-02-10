from concurrent import futures
import grpc
import ndarray_pb2
import ndarray_pb2_grpc
import numpy as np


class NdarrayService(ndarray_pb2_grpc.NdarrayServiceServicer):
    async def SendNdarray(self, request, context):
        # Deserialize the ndarray from bytes
        ndarray = np.frombuffer(request.ndarray, dtype=np.float32)
        print("Received ndarray:", ndarray)
        return ndarray_pb2.NdarrayReply(message="Ndarray received")


# Create an async gRPC server
async def serve():
    server = grpc.aio.server()
    ndarray_pb2_grpc.add_NdarrayServiceServicer_to_server(NdarrayService(), server)
    listen_addr = "[::]:50051"
    server.add_insecure_port(listen_addr)
    print(f"Starting server on {listen_addr}")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    import asyncio

    asyncio.run(serve())
