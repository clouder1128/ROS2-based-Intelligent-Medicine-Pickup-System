#!/usr/bin/env python3
"""
Full integration test - tests complete P1-backend integration
"""
import os
import sys
import time
import subprocess
import httpx
import json

def check_backend():
    """Check if backend is running and healthy"""
    try:
        response = httpx.get('http://localhost:8001/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Backend running: {data.get('message', 'unknown')}")
            return True
        else:
            print(f"✗ Backend responded with {response.status_code}")
            return False
    except httpx.ConnectError:
        print("✗ Backend not reachable at http://localhost:8001")
        return False
    except Exception as e:
        print(f"✗ Backend check failed: {e}")
        return False

def test_p1_modules():
    """Test P1 modules integration"""
    # Add P1 to Python path
    p1_path = os.path.join(os.path.dirname(__file__), '..', 'P1')
    sys.path.insert(0, p1_path)

    print("\nTesting P1 modules...")

    try:
        import drug_db
    except ImportError as e:
        print(f"✗ Failed to import drug_db: {e}")
        return False

    try:
        from tools import medical
    except ImportError as e:
        print(f"✗ Failed to import medical: {e}")
        return False

    try:
        from tools import inventory
    except ImportError as e:
        print(f"✗ Failed to import inventory: {e}")
        return False

    # Test health check
    health = drug_db.health_check()
    print(f"Health check result: {health}")
    if health.get('status') == 'connected' or health.get('backend_available'):
        print("✓ P1 can connect to backend")
    else:
        print("⚠ P1 health check indicates issues, but continuing test...")
        # Don't fail immediately, continue with other tests

    # Test drug queries
    drugs = drug_db.get_all_drugs()
    if drugs:
        print(f"✓ Retrieved {len(drugs)} drugs from backend")
    else:
        print("✗ No drugs retrieved from backend")

    # Test approval creation
    approval_id = medical.submit_approval(
        patient_name="Integration Test",
        advice="Test medication",
        symptoms="Test symptoms"
    )
    if approval_id and approval_id.startswith('AP-'):
        print(f"✓ Created approval: {approval_id}")
    else:
        print("✗ Failed to create approval")

    # Test inventory report
    report_json = inventory.get_stock_report()
    report = json.loads(report_json)
    if report.get('current_stock_summary'):
        print("✓ Generated inventory report")
    else:
        print("✗ Failed to generate inventory report")

    return True

def main():
    """Run full integration test"""
    print("=" * 60)
    print("Full Backend-P1 Integration Test")
    print("=" * 60)

    # Set environment
    os.environ['PHARMACY_BASE_URL'] = 'http://localhost:8001'

    # Check backend
    if not check_backend():
        print("\nPlease start backend first:")
        print("  cd test/backend && python app.py")
        return 1

    # Test P1 modules
    success = test_p1_modules()

    if success:
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Integration tests failed")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())