import httpx
import pytest

from main import QUESTION_DOMAINS, app

pytestmark = pytest.mark.anyio


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as session:
        yield session


def answer_map(value: str) -> dict[str, str]:
    return {question_id: value for question_id in QUESTION_DOMAINS}


async def test_health_and_security_headers(client: httpx.AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "2.0.0"}
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


async def test_v2_full_established_assessment(client: httpx.AsyncClient):
    response = await client.post(
        "/v2/analyze", json={"answers": answer_map("established")}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["score"] == 100
    assert payload["maturity"] == "Evidence-Led Execution"
    assert payload["priorities"] == []
    assert len(payload["domains"]) == 6


async def test_v2_rejects_incomplete_or_unknown_catalog(client: httpx.AsyncClient):
    response = await client.post(
        "/v2/analyze", json={"answers": {"unknown": "partial"}}
    )
    assert response.status_code == 422


async def test_not_applicable_is_excluded(client: httpx.AsyncClient):
    answers = answer_map("established")
    answers["strategy-outcomes"] = "not-applicable"
    response = await client.post("/v2/analyze", json={"answers": answers})
    assert response.status_code == 200
    strategy = next(
        item for item in response.json()["domains"] if item["id"] == "strategy"
    )
    assert strategy["score"] == 100
    assert strategy["applicable"] == 3


async def test_legacy_endpoint_requires_exactly_ten_booleans(
    client: httpx.AsyncClient,
):
    valid = await client.post("/analyze", json={"answers": [True] * 10})
    assert valid.status_code == 200
    assert valid.json()["score"] == 100

    invalid = await client.post("/analyze", json={"answers": [True] * 9})
    assert invalid.status_code == 422
