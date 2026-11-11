from app.main import create_app


def test_openapi_has_no_validation_error_noise() -> None:
    """FastAPI's default 422 responses are removed: our handlers return 400 ErrorResponse."""
    schema = create_app(":memory:").openapi()
    names = set(schema["components"]["schemas"])
    assert "ErrorResponse" in names
    assert not {"HTTPValidationError", "ValidationError"} & names
    for path in schema["paths"].values():
        for operation in path.values():
            assert "422" not in operation["responses"]


def test_every_operation_documents_error_response_as_default() -> None:
    schema = create_app(":memory:").openapi()
    ref = "#/components/schemas/ErrorResponse"
    for path in schema["paths"].values():
        for operation in path.values():
            default = operation["responses"]["default"]
            assert default["content"]["application/json"]["schema"]["$ref"] == ref
