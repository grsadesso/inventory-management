"""
Tests for purchase order API endpoints.
"""
import pytest


@pytest.fixture
def backlog_item_id(client):
    """ID of an existing backlog item without a purchase order."""
    items = client.get("/api/backlog").json()
    return next(i["id"] for i in items if not i["has_purchase_order"])


@pytest.fixture
def po_payload(backlog_item_id):
    """Valid purchase order payload."""
    return {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Supply",
        "quantity": 100,
        "unit_cost": 12.5,
        "expected_delivery_date": "2025-11-01",
        "notes": "Rush",
    }


class TestPurchaseOrderEndpoints:
    """Test suite for purchase-order endpoints."""

    def test_create_purchase_order(self, client, po_payload):
        """Test creating a purchase order."""
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["status"] == "Pending"
        assert po["created_date"]
        for key, value in po_payload.items():
            assert po[key] == value

    def test_create_without_notes(self, client, po_payload):
        """Test that notes are optional."""
        del po_payload["notes"]
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 201
        assert response.json()["notes"] is None

    def test_get_purchase_order_by_backlog_item(self, client, po_payload):
        """Test fetching the created purchase order."""
        created = client.post("/api/purchase-orders", json=po_payload).json()

        response = client.get(f"/api/purchase-orders/{po_payload['backlog_item_id']}")
        assert response.status_code == 200
        assert response.json() == created

    def test_get_purchase_order_not_found(self, client, backlog_item_id):
        """Test fetching a PO for a backlog item that has none."""
        response = client.get(f"/api/purchase-orders/{backlog_item_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_for_unknown_backlog_item(self, client, po_payload):
        """Test that an unknown backlog item is rejected with 404."""
        po_payload["backlog_item_id"] = "nonexistent-999"
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_duplicate_purchase_order_rejected(self, client, po_payload):
        """Test that a second PO for the same backlog item returns 409."""
        assert client.post("/api/purchase-orders", json=po_payload).status_code == 201
        response = client.post("/api/purchase-orders", json=po_payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_ids_are_unique(self, client):
        """Test that POs for different backlog items get different ids."""
        items = client.get("/api/backlog").json()[:2]
        ids = set()
        for item in items:
            payload = {
                "backlog_item_id": item["id"], "supplier_name": "S", "quantity": 1,
                "unit_cost": 1, "expected_delivery_date": "2025-11-01",
            }
            ids.add(client.post("/api/purchase-orders", json=payload).json()["id"])
        assert len(ids) == 2

    @pytest.mark.parametrize("field,value", [
        ("quantity", 0),
        ("quantity", -5),
        ("quantity", "many"),
        ("unit_cost", -1),
        ("supplier_name", ""),
    ])
    def test_validation_errors(self, client, po_payload, field, value):
        """Test that invalid values are rejected with 422."""
        po_payload[field] = value
        assert client.post("/api/purchase-orders", json=po_payload).status_code == 422

    @pytest.mark.parametrize("field", ["backlog_item_id", "supplier_name", "quantity", "unit_cost", "expected_delivery_date"])
    def test_missing_required_field(self, client, po_payload, field):
        """Test that each required field is enforced."""
        del po_payload[field]
        assert client.post("/api/purchase-orders", json=po_payload).status_code == 422

    def test_backlog_flips_has_purchase_order(self, client, po_payload):
        """Test that /api/backlog reports the new PO."""
        target = po_payload["backlog_item_id"]

        def flag():
            items = client.get("/api/backlog").json()
            return next(i for i in items if i["id"] == target)["has_purchase_order"]

        assert flag() is False
        client.post("/api/purchase-orders", json=po_payload)
        assert flag() is True

    def test_state_does_not_leak_between_tests(self, client, backlog_item_id):
        """Test that POs from earlier tests were removed by the restore fixture."""
        assert client.get(f"/api/purchase-orders/{backlog_item_id}").status_code == 404
