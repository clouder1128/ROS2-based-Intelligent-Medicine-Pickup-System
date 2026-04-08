"""
Backend integration tests - requires backend service running
"""
import os
import pytest
import json
import time

# Mark as integration test (slow, requires external service)
pytestmark = pytest.mark.integration

@pytest.fixture(scope="module")
def backend_available():
    """Check if backend is available before running tests"""
    import services.pharmacy_client as drug_db
    health = drug_db.health_check()
    return health.get('backend_available', False)

@pytest.mark.skipif(
    not os.getenv('RUN_INTEGRATION_TESTS'),
    reason="Integration tests disabled (set RUN_INTEGRATION_TESTS=1 to run)"
)
class TestBackendIntegration:
    """Integration tests with real backend"""

    def test_backend_connection(self):
        """Test basic connection to backend"""
        import services.pharmacy_client as drug_db
        health = drug_db.health_check()
        assert health['backend_available'] == True
        print(f"Backend health: {health}")

    def test_drug_queries(self, backend_available):
        """Test drug query functions"""
        if not backend_available:
            pytest.skip("Backend not available")

        import services.pharmacy_client as drug_db
        import tools.medical

        # Test getting all drugs
        all_drugs = drug_db.get_all_drugs()
        assert isinstance(all_drugs, list)
        print(f"Found {len(all_drugs)} drugs in backend")

        if all_drugs:
            # Test query by name
            first_drug = all_drugs[0]
            drug_by_name = drug_db.query_drug_by_name(first_drug.get('name', ''))
            assert drug_by_name is not None
            assert drug_by_name['drug_id'] == first_drug['drug_id']

    def test_approval_workflow(self, backend_available):
        """Test complete approval workflow"""
        if not backend_available:
            pytest.skip("Backend not available")

        import tools.medical

        # Create approval
        approval_id = tools.medical.submit_approval(
            patient_name="Integration Test Patient",
            advice="Integration test advice",
            patient_age=25,
            symptoms="Test symptoms"
        )

        assert approval_id is not None
        assert approval_id.startswith('AP-')
        print(f"Created approval: {approval_id}")

        # Note: Approval query would need approval API client in drug_db
        # which we haven't implemented yet

    def test_inventory_functions(self, backend_available):
        """Test inventory-related functions"""
        if not backend_available:
            pytest.skip("Backend not available")

        import tools.inventory
        import json

        # Test stock report (should work even without transactions)
        report_json = tools.inventory.get_stock_report()
        report = json.loads(report_json)
        assert 'current_stock_summary' in report
        assert 'drugs' in report

        print(f"Stock report generated: {report['current_stock_summary']}")