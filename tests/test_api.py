import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture()
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def activities_state():
    """Save and restore the in-memory activities state for each test."""
    orig = copy.deepcopy(app_module.activities)
    try:
        yield
    finally:
        # Restore the original activities state
        app_module.activities.clear()
        app_module.activities.update(orig)


def test_get_activities(client):
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    # basic sanity check that sample activity exists
    assert "Chess Club" in data
    assert isinstance(data["Chess Club"].get("participants"), list)


def test_signup_adds_participant(client):
    email = "tester@example.com"
    activity = "Chess Club"
    url = f"/activities/{quote(activity)}/signup?email={quote(email)}"

    resp = client.post(url)
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")

    # Verify the participant was added
    listing = client.get("/activities").json()
    assert email in listing[activity]["participants"]


def test_unregister_removes_participant(client):
    email = "remover@example.com"
    activity = "Chess Club"
    signup_url = f"/activities/{quote(activity)}/signup?email={quote(email)}"
    delete_url = f"/activities/{quote(activity)}/participants?email={quote(email)}"

    # Ensure participant exists first
    r = client.post(signup_url)
    assert r.status_code == 200

    # Now remove
    r = client.delete(delete_url)
    assert r.status_code == 200
    body = r.json()
    assert "Removed" in body.get("message", "")

    listing = client.get("/activities").json()
    assert email not in listing[activity]["participants"]
