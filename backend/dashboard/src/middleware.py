import grpc
from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from common.grpc import auth_pb2, auth_pb2_grpc


def auth_error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


class GrpcAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_service_addr: str = "auth:50051"):
        super().__init__(app)
        self.auth_service_addr = auth_service_addr

    async def dispatch(self, request: Request, call_next):
        # Let CORS middleware answer preflight requests before auth is enforced.
        if request.method == "OPTIONS":
            return await call_next(request)

        # Expose health endpoints without authentication.
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return auth_error(
                status.HTTP_401_UNAUTHORIZED,
                "Missing Authorization header",
            )

        token = auth_header
        if token.startswith("Bearer "):
            token = token[7:]

        try:
            async with grpc.aio.insecure_channel(self.auth_service_addr) as channel:
                stub = auth_pb2_grpc.AuthServiceStub(channel)
                response = await stub.VerifyToken(auth_pb2.VerifyTokenRequest(token=token))

                if not response.is_valid:
                    return auth_error(
                        status.HTTP_401_UNAUTHORIZED,
                        "Invalid token verified by gRPC Auth",
                    )

                request.state.user_id = response.user_id
                request.state.role = response.role

        except grpc.RpcError as exc:
            detail = exc.details() if hasattr(exc, "details") else str(exc)
            return auth_error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                f"Auth gRPC service unavailable: {detail}",
            )

        return await call_next(request)