import pandas as pd
from datetime import datetime, timedelta

def create_csv_template():
    """Create a CSV template file for users to follow"""
    template_data = {
        'product_id': ['P001', 'P002', 'P003'],
        'product_name': ['Example Product 1', 'Example Product 2', 'Example Product 3'],
        'current_stock': [25, 50, 10],
        'ideal_stock_level': [100, 75, 30],
        'expiration_date': [
            '2025-12-31',  # YYYY-MM-DD format
            '2025-09-15',
            '2025-08-25'
        ],
        'category': ['Food', 'Beverages', 'Dairy'],
        'supplier': ['Supplier A', 'Supplier B', 'Supplier C']
    }
    
    df = pd.DataFrame(template_data)
    df.to_csv('uploads/inventory_template.csv', index=False)
    print("✅ Created CSV template: uploads/inventory_template.csv")

if __name__ == "__main__":
    create_csv_template()
