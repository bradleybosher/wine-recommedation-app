"""Tests for backend.routes.inventory — /upload-inventory, /inventory."""

import json

import inventory as inventory_module


_VALID_TSV = (
    "iWine\tProducer\tWine\tVintage\tVarietal\tAppellation\tQuantity\n"
    "1\tDomaine A\tCuvée X\t2018\tPinot Noir\tBurgundy\t2\n"
    "2\tDomaine B\tCuvée Y\t2019\tChardonnay\tChablis\t1\n"
)


class TestUploadInventory:
    def test_happy_path_saves_bottles(self, client, auth_headers, registered_user):
        resp = client.post(
            "/upload-inventory",
            headers=auth_headers,
            files={"file": ("export.tsv", _VALID_TSV.encode(), "text/tab-separated-values")},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["count"] == 2

        # File should be written under the per-profile dir
        inv = inventory_module.load_inventory(registered_user["profile_id"])
        assert inv is not None
        assert len(inv["bottles"]) == 2

    def test_zero_quantity_rows_filtered_out(self, client, auth_headers, registered_user):
        tsv = (
            "iWine\tProducer\tWine\tVintage\tVarietal\tAppellation\tQuantity\n"
            "1\tDomaine A\tX\t2018\tPN\tBurgundy\t0\n"
            "2\tDomaine B\tY\t2019\tCH\tChablis\t1\n"
        )
        resp = client.post(
            "/upload-inventory",
            headers=auth_headers,
            files={"file": ("export.tsv", tsv.encode(), "text/tab-separated-values")},
        )
        assert resp.status_code == 200
        # Only the quantity>0 row should be persisted
        assert resp.json()["count"] == 1


class TestGetInventory:
    def test_empty_when_no_upload_yet(self, client, auth_headers):
        resp = client.get("/inventory", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["bottles"] == []

    def test_returns_uploaded_bottles(self, client, auth_headers):
        client.post(
            "/upload-inventory",
            headers=auth_headers,
            files={"file": ("export.tsv", _VALID_TSV.encode(), "text/tab-separated-values")},
        )
        resp = client.get("/inventory", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["bottles"]) == 2

    def test_profile_scoping_isolates_inventories(self, client, isolated_db, isolated_profiles_dir):
        """Two registered users must not see each other's inventory."""
        # Register alice
        alice = client.post(
            "/auth/register",
            json={"email": "alice@example.com", "password": "longpassword"},
        ).json()
        alice_headers = {
            "Authorization": f"Bearer {alice['accessToken']}",
            "X-Profile-Id": alice["profile"]["id"],
        }
        # Register bob
        bob = client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": "longpassword"},
        ).json()
        bob_headers = {
            "Authorization": f"Bearer {bob['accessToken']}",
            "X-Profile-Id": bob["profile"]["id"],
        }

        # Alice uploads — bob's inventory should remain empty
        client.post(
            "/upload-inventory",
            headers=alice_headers,
            files={"file": ("export.tsv", _VALID_TSV.encode(), "text/tab-separated-values")},
        )

        bob_inv = client.get("/inventory", headers=bob_headers).json()
        assert bob_inv["bottles"] == []

        # Bob can't read alice's by passing her X-Profile-Id (ownership check → 403)
        cross = client.get(
            "/inventory",
            headers={
                "Authorization": f"Bearer {bob['accessToken']}",
                "X-Profile-Id": alice["profile"]["id"],
            },
        )
        assert cross.status_code == 403
