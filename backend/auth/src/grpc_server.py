import asyncio
import logging
from concurrent import futures

import grpc

from common.auth import verify_supabase_access_token
from .db.profiles import get_profile
from common.grpc import auth_pb2, auth_pb2_grpc

logger = logging.getLogger("auth.grpc")


class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    def VerifyToken(self, request, context):
        token = request.token
        if not token:
            return auth_pb2.VerifyTokenResponse(is_valid=False)

        # Handle "Bearer " prefix if sent
        if token.startswith("Bearer "):
            token = token[len("Bearer ") :]

        payload = verify_supabase_access_token(token)
        if not payload:
            logger.warning("JWT verification failed")
            return auth_pb2.VerifyTokenResponse(is_valid=False)

        user_id = payload.get("sub")
        if not user_id:
            return auth_pb2.VerifyTokenResponse(is_valid=False)

        # Get user's role from DB profile
        try:
            profile = get_profile(user_id)
            role = profile.get("role", "operator")
        except Exception:
            role = "operator"

        return auth_pb2.VerifyTokenResponse(
            is_valid=True,
            user_id=user_id,
            role=role,
        )

    def GetUserProfile(self, request, context):
        user_id = request.user_id
        try:
            profile = get_profile(user_id)
            return auth_pb2.GetUserProfileResponse(
                user_id=profile.get("id", user_id),
                full_name=profile.get("display_name", ""),
                role=profile.get("role", "operator"),
                created_at=profile.get("created_at", ""),
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Profile not found: {exc}")
            return auth_pb2.GetUserProfileResponse()


async def serve_grpc(port: int = 50051):
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    logger.info(f"Starting gRPC server on port {port}")
    await server.start()
    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info("gRPC server cancelled, stopping")
        await server.stop(grace=0)
