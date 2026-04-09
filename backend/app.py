"""
Legacy Flask Application Entry Point
Maintained for backward compatibility - imports from main.py
"""

# Import the Flask app from main.py for backward compatibility
from main import app

# Re-export helper functions for backward compatibility
from controllers.drug_controller import query_drug, validate_and_get_drug, find_drug_id_by_name

# Note: All routes are now in controller files in the controllers/ directory
# - Health routes: controllers/health_controller.py
# - Drug routes: controllers/drug_controller.py
# - Order routes: controllers/order_controller.py
# - Approval routes: controllers/approval_controller.py

if __name__ == '__main__':
    # Run the app (same as main.py)
    from main import Config
    import os

    if not os.path.exists(Config.DATABASE_PATH):
        print('请先运行: python3 init_db.py')
        exit(1)

    app.run(host=Config.HOST, port=Config.PORT, debug=True, use_reloader=True)