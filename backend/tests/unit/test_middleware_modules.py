from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.middleware.cors import setup_cors
from src.middleware.logging import RequestLoggingMiddleware
from src.middleware.error_handler import UnhandledErrorMiddleware, setup_exception_handlers
from src.middleware.auth import AuthenticationMiddleware


def make_app() -> FastAPI:
    app = FastAPI()

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    @app.get("/echo")
    def echo():
        return {"ok": True}

    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    setup_cors(app, ["http://localhost:3000"])  # deterministic for test
    app.add_middleware(UnhandledErrorMiddleware)
    setup_exception_handlers(app)
    return app


def test_middleware_stack_basic():
    app = make_app()
    client = TestClient(app)

    r = client.get("/echo")
    assert r.status_code == 200
    assert r.headers.get("x-request-id") is not None


def test_auth_middleware_extracts_token():
    app = make_app()
    client = TestClient(app)
    r = client.get("/echo", headers={"Authorization": "Bearer test-token"})
    assert r.status_code == 200


def test_error_middleware_handles_exceptions():
    app = make_app()
    client = TestClient(app)
    r = client.get("/boom")
    assert r.status_code == 500
    assert r.json().get("detail") == "Internal Server Error"

