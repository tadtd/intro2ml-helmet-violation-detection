import grpc
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from common.grpc import auth_pb2, auth_pb2_grpc


class GrpcAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service_addr: str = "auth:50051"):
        super().__init__(app)
        self.auth_service_addr = auth_service_addr

    async def dispatch(self, request: Request, call_next):
        # Expose health endpoints without authentication
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header",
            )

        token = auth_header
        if token.startswith("Bearer "):
            token = token[7:]

        try:
            # We call the gRPC Auth service to verify the token
            async with grpc.aio.insecure_channel(self.auth_service_addr) as channel:
                stub = auth_pb2_grpc.AuthServiceStub(channel)
                response = await stub.VerifyToken(auth_pb2.VerifyTokenRequest(token=token))
                
                if not response.is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token verified by gRPC Auth",
                    )
                
                # Attach verified user details to request state
                request.state.user_id = response.user_id
                request.state.role = response.role
                
        except grpc.RpcError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Auth gRPC service unavailable: {exc.details() if hasattr(exc, 'details') else str(exc)}",
            )

        return await call_next(request)
