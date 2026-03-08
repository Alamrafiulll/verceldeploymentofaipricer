import requests
import uuid
import time
import sys

BASE_URL = "http://localhost:8000/api"

def get_token(role):
    try:
        response = requests.post(f"{BASE_URL}/auth/dev-login", json={"role": role})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Login failed for {role}: {e}")
        if e.response:
            print(e.response.text)
        sys.exit(1)

def main():
    print("Starting E2E Workflow Test...")

    # 1. Login as Sales Manager (Creator)
    print("\n[1] Logging in as Sales Manager...")
    sales_token = get_token("sales")
    sales_headers = {"Authorization": f"Bearer {sales_token}"}
    print("    Success.")

    # 2. Create New Customer
    customer_name = f"Test Customer {uuid.uuid4().hex[:8]}"
    print(f"\n[2] Creating New Customer: {customer_name}...")
    cust_payload = {
        "name": customer_name,
        "tier": "core",
        "region": "North America"
    }
    resp = requests.post(f"{BASE_URL}/customers", json=cust_payload, headers=sales_headers)
    if resp.status_code != 201:
        print(f"    Failed to create customer: {resp.status_code} {resp.text}")
        sys.exit(1)
    customer = resp.json()
    customer_id = customer["id"]
    print(f"    Created Customer ID: {customer_id}")

    # 3. Get or Create a Product
    print("\n[3] Fetching a Product...")
    # Try fetching from sandbox
    resp = requests.get(f"{BASE_URL}/sandbox/products", headers=sales_headers)
    if resp.status_code == 404:
         # Fallback to /products if /sandbox/products doesn't exist (though code says it should be sandbox)
         resp = requests.get(f"{BASE_URL}/products", headers=sales_headers)
    
    # Always create a new product to ensure it has inventory/rules setup correctly
    # (Previous runs might have left broken products)
    print("    Creating a fresh sandbox product...")
    prod_payload = {
        "sku": f"PROD-{uuid.uuid4().hex[:6]}",
        "name": "Test Product A",
        "category": "Widgets",
        "base_cost": 50.0,
        "current_price": 100.0
    }
    resp = requests.post(f"{BASE_URL}/sandbox/products", json=prod_payload, headers=sales_headers)
    if resp.status_code != 201:
            print(f"    Failed to create product: {resp.status_code} {resp.text}")
            sys.exit(1)
    product = resp.json()
    print(f"    Created Sandbox Product: {product['name']} ({product['id']})")
    product_id = product["id"]
    
    # 4. Create Quote
    print("\n[4] Creating Quote...")
    quote_payload = {
        "customer_id": customer_id,
        "channel": "direct",
        "strategy_mode": "maximize_profit",
        "item": {
            "product_id": product_id,
            "quantity": 100,
            "requested_price": product["current_price"] * 0.8,  # 20% discount to trigger approval potentially
            "requested_discount": 20.0
        }
    }
    resp = requests.post(f"{BASE_URL}/quotes", json=quote_payload, headers=sales_headers)
    if resp.status_code != 201:
        print(f"    Failed to create quote: {resp.status_code} {resp.text}")
        sys.exit(1)
    quote = resp.json()
    quote_id = quote["id"]
    print(f"    Created Quote ID: {quote_id}")

    # 5. Generate Recommendation
    print("\n[5] Generating Recommendation...")
    resp = requests.post(f"{BASE_URL}/quotes/{quote_id}/recommend", headers=sales_headers)
    if resp.status_code != 200:
        print(f"    Failed to generate recommendation: {resp.status_code} {resp.text}")
        sys.exit(1)
    recommendation = resp.json()
    print("    Recommendation generated.")

    # 6. Request Approval
    print("\n[6] Requesting Approval...")
    approval_payload = {
        "requested_price": quote_payload["item"]["requested_price"],
        "requested_discount": quote_payload["item"]["requested_discount"],
        "justification": "Customer demands 20% off for bulk order."
    }
    resp = requests.post(f"{BASE_URL}/quotes/{quote_id}/request-approval", json=approval_payload, headers=sales_headers)
    if resp.status_code != 200:
        print(f"    Failed to request approval: {resp.status_code} {resp.text}")
        sys.exit(1)
    approval_resp = resp.json()
    print(f"    Approval Requested. Status: {approval_resp['status']}")

    # 7. Login as Approver (Sales Executive)
    print("\n[7] Logging in as Approver...")
    approver_token = get_token("approver")
    approver_headers = {"Authorization": f"Bearer {approver_token}"}
    print("    Success.")

    # 8. List Pending Approvals
    print("\n[8] Listing Pending Approvals...")
    resp = requests.get(f"{BASE_URL}/approvals?status=pending", headers=approver_headers)
    approvals = resp.json()
    target_approval = next((a for a in approvals if a["quote_id"] == quote_id), None)
    
    if not target_approval:
        print("    Approval request not found in pending list!")
        # Debug: list all pending
        print("    Pending approvals found:", [a["quote_id"] for a in approvals])
        sys.exit(1)
    
    approval_id = target_approval["id"]
    print(f"    Found Approval ID: {approval_id}")

    # 9. Approve Quote
    print("\n[9] Approving Quote...")
    decision_payload = {
        "decision_reason": "Approved for strategic relationship."
    }
    resp = requests.post(f"{BASE_URL}/approvals/{approval_id}/approve", json=decision_payload, headers=approver_headers)
    if resp.status_code != 200:
        print(f"    Failed to approve: {resp.status_code} {resp.text}")
        sys.exit(1)
    print("    Approved.")

    # 10. Verify Final Status
    print("\n[10] Verifying Quote Status...")
    resp = requests.get(f"{BASE_URL}/quotes/{quote_id}", headers=sales_headers)
    final_quote = resp.json()
    status = final_quote["status"]
    print(f"    Final Quote Status: {status}")

    if status == "approved":
        print("\nSUCCESS: Workflow completed successfully!")
    else:
        print(f"\nFAILURE: Quote status is {status}, expected 'approved'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
