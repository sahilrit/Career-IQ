"""Auth endpoints — thin wrappers over careeros_auth.AuthService."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from careeros_api.dependencies import Context, get_auth_service
from careeros_api.email import app_base_url, send_email
from careeros_api.schemas import (
    LoginRequest,
    MeResponse,
    MessageResponse,
    ResetConfirmRequest,
    ResetRequest,
    SignupRequest,
    TokenResponse,
)
from careeros_auth import (
    AccountLockedError,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    PasswordPolicyError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(body: SignupRequest) -> TokenResponse:
    try:
        _, token = get_auth_service().sign_up(
            email=body.email, password=body.password, full_name=body.full_name
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered") from error
    except PasswordPolicyError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "; ".join(error.violations)
        ) from error
    return TokenResponse(token=token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    try:
        token = get_auth_service().log_in(email=body.email, password=body.password)
    except AccountLockedError as error:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "account temporarily locked"
        ) from error
    except InvalidCredentialsError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "email or password is incorrect"
        ) from error
    return TokenResponse(token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(context: Context) -> MessageResponse:
    # The bearer token is the session token; revoke it.
    # (Re-read from the store-free path isn't available, so log out everywhere
    # for this user — safe and simple for the API surface.)
    get_auth_service().log_out_everywhere(context.account.user.id)
    return MessageResponse(message="logged out")


@router.post("/reset/request", response_model=MessageResponse)
def request_reset(body: ResetRequest) -> MessageResponse:
    # Always the same response, so we never reveal which emails exist.
    token = get_auth_service().request_password_reset(body.email)
    if token:
        link = f"{app_base_url()}/reset?token={token}"
        send_email(
            to=body.email,
            subject="Reset your CareerOS password",
            body=(
                "We received a request to reset your CareerOS password.\n\n"
                f"Reset it here (link expires in 1 hour):\n{link}\n\n"
                "If you didn't request this, you can safely ignore this email."
            ),
        )
    return MessageResponse(message="if that email has an account, a reset link is on its way")


@router.post("/reset/confirm", response_model=MessageResponse)
def confirm_reset(body: ResetConfirmRequest) -> MessageResponse:
    try:
        get_auth_service().reset_password(body.token, body.new_password)
    except PasswordPolicyError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "; ".join(error.violations)
        ) from error
    except InvalidCredentialsError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "reset link is invalid or expired"
        ) from error
    return MessageResponse(message="password reset")


@router.get("/me", response_model=MeResponse)
def me(context: Context) -> MeResponse:
    account = context.account
    return MeResponse(
        user_id=account.user.id,
        email=account.user.email,
        full_name=account.user.full_name,
        workspace_id=account.workspace_id,
        role=account.role.value,
        is_admin=context.is_admin,
    )
