import pandas as pd
import os
from datetime import datetime, timedelta
from inventory_system import CSVExpirationManager
from config import email_config

class CSVExpirationProcessor:
    def __init__(self):
        self.csv_manager = CSVExpirationManager()
        self.upload_folder = 'uploads'
        self.ensure_upload_folder()

    def ensure_upload_folder(self):
        """Create uploads folder if it doesn't exist"""
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
            print(f"✅ Created upload folder: {self.upload_folder}")

    def create_sample_csv(self, filename="sample_inventory_with_expiry.csv"):
        """Create a sample CSV file with expiration dates for testing"""
        try:
            sample_data = {
                'product_id': [
                    'P001', 'P002', 'P003', 'P004', 'P005', 'P006', 'P007', 'P008', 'P009', 'P010'
                ],
                'product_name': [
                    'Fresh Milk 1L', 'Whole Wheat Bread', 'Greek Yogurt', 'Cheddar Cheese', 
                    'Free Range Eggs', 'Organic Butter', 'Fresh Orange Juice', 'Salmon Fillet',
                    'Chicken Breast', 'Mixed Vegetables'
                ],
                'current_stock': [15, 8, 12, 25, 45, 6, 20, 18, 30, 40],
                'ideal_stock_level': [50, 30, 35, 40, 60, 20, 45, 25, 50, 60],
                'expiration_date': [
                    # Mix of expired, expiring soon, and normal dates
                    (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),   # Expiring soon
                    (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),   # Expired
                    (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),   # Expiring soon  
                    (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d'),  # This month
                    (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'),  # This month
                    (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),   # Expired
                    (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),   # Expiring soon
                    (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),   # Expiring very soon
                    (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),  # Normal
                    (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')   # This month
                ],
                'category': [
                    'Dairy', 'Bakery', 'Dairy', 'Dairy', 'Dairy', 'Dairy', 
                    'Beverages', 'Seafood', 'Meat', 'Vegetables'
                ],
                'supplier': [
                    'Local Dairy Farm', 'City Bakery', 'Organic Foods Co', 'Cheese Masters',
                    'Farm Fresh Ltd', 'Organic Foods Co', 'Fresh Juice Co', 'Ocean Fresh',
                    'Quality Meats', 'Garden Fresh'
                ]
            }

            df = pd.DataFrame(sample_data)
            file_path = os.path.join(self.upload_folder, filename)
            df.to_csv(file_path, index=False)
            
            print(f"✅ Created sample CSV file: {file_path}")
            print(f"📊 Sample contains {len(df)} products with various expiration statuses:")
            print("   - Some expired products (for testing alerts)")
            print("   - Products expiring within 7 days")
            print("   - Products expiring within 30 days") 
            print("   - Products with normal expiration dates")
            
            return file_path
            
        except Exception as e:
            print(f"❌ Error creating sample CSV: {e}")
            return None

    def process_uploaded_csv(self, file_path):
        """Process uploaded CSV and return expiration analysis"""
        try:
            # Configure email system
            self.csv_manager.email_system.configure_email(
                email_config['smtp_server'],
                email_config['smtp_port'],
                email_config['sender_email'],
                email_config['sender_password'],
                email_config['recipient_emails']
            )

            # Load CSV file
            success = self.csv_manager.load_csv_file(file_path)
            if not success:
                return None, "Failed to load CSV file"

            # Get expiration analysis
            expired_products = self.csv_manager.get_expired_products_from_csv()
            expiring_soon = self.csv_manager.get_expiring_soon_from_csv(7)
            expiring_month = self.csv_manager.get_expiring_soon_from_csv(30)
            all_with_expiry = self.csv_manager.get_products_with_expiration()
            summary = self.csv_manager.generate_csv_expiration_summary()

            analysis_result = {
                'file_processed': True,
                'file_path': file_path,
                'total_products': summary['total_products'],
                'products_with_expiry': summary['products_with_expiry'],
                'expired_products': expired_products,
                'expiring_soon': expiring_soon,
                'expiring_month': expiring_month,
                'all_with_expiry': all_with_expiry,
                'summary': summary
            }

            return analysis_result, "CSV processed successfully"

        except Exception as e:
            error_msg = f"Error processing CSV: {str(e)}"
            print(f"❌ {error_msg}")
            return None, error_msg

    def send_expiration_alerts_for_csv(self, file_path):
        """Send expiration alerts for specific CSV file"""
        try:
            # Load and process CSV
            success = self.csv_manager.load_csv_file(file_path)
            if not success:
                return False, "Failed to load CSV file"

            # Configure email
            self.csv_manager.email_system.configure_email(
                email_config['smtp_server'],
                email_config['smtp_port'],
                email_config['sender_email'],
                email_config['sender_password'],
                email_config['recipient_emails']
            )

            # Send alerts
            success, results = self.csv_manager.send_csv_expiration_alerts()
            return success, results

        except Exception as e:
            return False, f"Error sending alerts: {str(e)}"

    def validate_csv_format(self, file_path):
        """Validate CSV file format and provide feedback"""
        try:
            df = pd.read_csv(file_path)
            
            validation_result = {
                'valid': True,
                'total_rows': len(df),
                'columns_found': list(df.columns),
                'issues': [],
                'suggestions': []
            }

            # Check required columns
            required_cols = ['product_id', 'product_name', 'current_stock']
            optional_cols = ['ideal_stock_level', 'expiration_date']
            
            missing_required = [col for col in required_cols if col not in df.columns]
            missing_optional = [col for col in optional_cols if col not in df.columns]

            if missing_required:
                validation_result['valid'] = False
                validation_result['issues'].append(f"Missing required columns: {missing_required}")

            if missing_optional:
                validation_result['suggestions'].append(f"Consider adding optional columns for better functionality: {missing_optional}")

            # Check expiration date format
            if 'expiration_date' in df.columns:
                expiry_sample = df['expiration_date'].dropna().head(5)
                validation_result['expiry_date_samples'] = expiry_sample.tolist()
                
                # Try to parse dates
                date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                unparseable_dates = []
                
                for date_str in expiry_sample:
                    if pd.notna(date_str) and str(date_str).strip() != '':
                        parsed = False
                        for fmt in date_formats:
                            try:
                                datetime.strptime(str(date_str).strip(), fmt)
                                parsed = True
                                break
                            except ValueError:
                                continue
                        
                        if not parsed:
                            unparseable_dates.append(str(date_str))

                if unparseable_dates:
                    validation_result['issues'].append(f"Some expiration dates couldn't be parsed: {unparseable_dates}")
                    validation_result['suggestions'].append("Use date format: YYYY-MM-DD (e.g., 2025-12-31)")

            return validation_result

        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'issues': [f"Failed to read CSV file: {str(e)}"],
                'suggestions': ["Ensure file is a valid CSV format"]
            }

def test_csv_processor():
    """Test function for CSV expiration processor"""
    print("🧪 Testing CSV Expiration Processor")
    print("=" * 60)
    
    processor = CSVExpirationProcessor()
    
    # Create sample CSV
    sample_file = processor.create_sample_csv()
    if not sample_file:
        print("❌ Failed to create sample file")
        return

    # Validate CSV format
    print(f"\n📋 Validating CSV format...")
    validation = processor.validate_csv_format(sample_file)
    if validation['valid']:
        print("✅ CSV format is valid")
        print(f"📊 Rows: {validation['total_rows']}")
        print(f"📝 Columns: {validation['columns_found']}")
    else:
        print("❌ CSV validation issues found:")
        for issue in validation['issues']:
            print(f"   - {issue}")

    # Process CSV
    print(f"\n🔍 Processing CSV for expiration analysis...")
    analysis, message = processor.process_uploaded_csv(sample_file)
    
    if analysis:
        print("✅ CSV processed successfully!")
        print(f"📊 Total products: {analysis['total_products']}")
        print(f"📅 Products with expiry dates: {analysis['products_with_expiry']}")
        print(f"🔴 Expired products: {len(analysis['expired_products'])}")
        print(f"🟡 Expiring soon (≤7 days): {len(analysis['expiring_soon'])}")
        print(f"🔵 Expiring this month (≤30 days): {len(analysis['expiring_month'])}")
        
        # Send test alert
        print(f"\n📧 Sending expiration alerts...")
        success, results = processor.send_expiration_alerts_for_csv(sample_file)
        if success:
            if isinstance(results, list):
                for alert_type, count, success, message in results:
                    status = "✅" if success else "❌"
                    print(f"{status} {alert_type}: {count} products - {message}")
            else:
                print(f"✅ {results}")
        else:
            print(f"❌ Failed to send alerts: {results}")
    else:
        print(f"❌ Failed to process CSV: {message}")

if __name__ == "__main__":
    test_csv_processor()
