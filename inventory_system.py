import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailNotificationSystem:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = ""
        self.sender_password = ""
        self.recipient_emails = []
        self.is_configured = False

    def configure_email(self, smtp_server, smtp_port, sender_email, sender_password, recipient_emails):
        self.smtp_server = smtp_server
        self.smtp_port = int(smtp_port)
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_emails = recipient_emails if isinstance(recipient_emails, list) else [recipient_emails]
        self.is_configured = True
        print(f"✅ Email configured: {sender_email} → {recipient_emails}")

    def send_stock_alert(self, alert_type, product_data, summary_stats=None):
        if not self.is_configured:
            print("❌ Email not configured")
            return False, "Email not configured"

        try:
            print(f"📧 Attempting to send {alert_type} email...")
            print(f"🔗 Server: {self.smtp_server}:{self.smtp_port}")
            print(f"👤 From: {self.sender_email}")
            print(f"📬 To: {self.recipient_emails}")

            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(self.recipient_emails)

            subjects = {
                "critical": "🚨 CRITICAL STOCK ALERT - Immediate Action Required",
                "overstock": "📦 OVERSTOCK ALERT - Inventory Review Needed", 
                "understock": "⚠️ UNDERSTOCK ALERT - Reorder Required",
                "expiring": "⏰ EXPIRATION ALERT - Products Expiring Soon",
                "expired": "🔴 EXPIRED PRODUCTS ALERT - Immediate Removal Required"
            }
            msg['Subject'] = subjects.get(alert_type, "📊 Inventory Status Report")

            html_body = self._create_email_body(alert_type, product_data, summary_stats)
            msg.attach(MIMEText(html_body, 'html'))

            print("🔗 Connecting to Gmail SMTP server...")
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)
                print("🔐 Starting TLS encryption...")
                server.starttls(context=context)
                print(f"🔑 Logging in as {self.sender_email}...")
                server.login(self.sender_email, self.sender_password)
                print(f"📤 Sending email to {self.recipient_emails}...")
                text = msg.as_string()
                server.sendmail(self.sender_email, self.recipient_emails, text)

            print("✅ Email sent successfully!")
            return True, "Email sent successfully"

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"❌ SMTP Authentication failed: {str(e)}"
            print(error_msg)
            return False, "Authentication failed - Use Gmail App Password"
        except Exception as e:
            error_msg = f"❌ Email sending failed: {str(e)}"
            print(error_msg)
            return False, error_msg

    def _create_email_body(self, alert_type, product_data, summary_stats):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f'''
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .expired {{ background-color: #ffcccc; }}
                .expiring-soon {{ background-color: #fff3cd; }}
                .expiring-month {{ background-color: #d1ecf1; }}
                .critical {{ color: #d32f2f; font-weight: bold; }}
                .warning {{ color: #f57c00; }}
                .info {{ color: #1976d2; }}
                .header {{ background-color: #e3f2fd; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Inventory Management Report - CSV Data</h2>
                <p><strong>Generated on:</strong> {current_time}</p>
                <p><strong>Source:</strong> Uploaded CSV File</p>
            </div>
        '''

        # Alert type specific headers
        if alert_type == "critical":
            html += '<h3 class="critical">🚨 CRITICAL STOCK ALERT</h3><p><strong>Immediate action required!</strong> Products with critically low stock levels from your CSV data.</p>'
        elif alert_type == "overstock":
            html += '<h3 class="warning">📦 OVERSTOCK ALERT</h3><p>Products that are overstocked based on your CSV data.</p>'
        elif alert_type == "understock":
            html += '<h3 class="warning">⚠️ UNDERSTOCK ALERT</h3><p>Products that need restocking based on your CSV data.</p>'
        elif alert_type == "expiring":
            html += '<h3 class="warning">⏰ EXPIRATION ALERT</h3><p><strong>Products from your CSV are expiring soon!</strong> Immediate attention required.</p>'
        elif alert_type == "expired":
            html += '<h3 class="critical">🔴 EXPIRED PRODUCTS ALERT</h3><p><strong>Critical!</strong> Products from your CSV have already expired and need immediate removal.</p>'

        # Table with expiration date column
        html += '''
        <table>
        <tr>
            <th>Product ID</th>
            <th>Product Name</th>
            <th>Current Stock</th>
            <th>Ideal/Target Stock</th>
            <th>Stock Ratio</th>
            <th>Expiration Date</th>
            <th>Days to Expire</th>
            <th>Expiry Status</th>
            <th>Recommended Action</th>
            <th>Order Quantity</th>
        </tr>
        '''

        for product in product_data:
            # Handle expiration date
            expiry_date = product.get('expiration_date', 'N/A')
            days_to_expire = 'N/A'
            expiry_status = 'Unknown'
            row_class = ''

            if expiry_date != 'N/A' and expiry_date and str(expiry_date).strip() != '':
                try:
                    # Handle multiple date formats
                    if isinstance(expiry_date, str):
                        # Try different date formats
                        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                        exp_date = None
                        
                        for fmt in date_formats:
                            try:
                                exp_date = datetime.strptime(expiry_date.strip(), fmt)
                                break
                            except ValueError:
                                continue
                        
                        if exp_date is None:
                            raise ValueError("Invalid date format")
                        
                        formatted_date = exp_date.strftime('%Y-%m-%d')
                    else:
                        exp_date = expiry_date
                        formatted_date = exp_date.strftime('%Y-%m-%d')

                    days_to_expire = (exp_date - datetime.now()).days
                    
                    # Set row styling and status based on expiration
                    if days_to_expire < 0:
                        row_class = 'expired'
                        expiry_status = f'EXPIRED ({abs(days_to_expire)} days ago)'
                        days_display = f"{abs(days_to_expire)} days ago"
                    elif days_to_expire == 0:
                        row_class = 'expired'
                        expiry_status = 'EXPIRES TODAY'
                        days_display = 'Today'
                    elif days_to_expire <= 7:
                        row_class = 'expiring-soon'
                        expiry_status = 'EXPIRING SOON'
                        days_display = f"{days_to_expire} days"
                    elif days_to_expire <= 30:
                        row_class = 'expiring-month'
                        expiry_status = 'EXPIRING THIS MONTH'
                        days_display = f"{days_to_expire} days"
                    else:
                        expiry_status = 'NORMAL'
                        days_display = f"{days_to_expire} days"
                    
                    expiry_date = formatted_date
                    days_to_expire = days_display
                except Exception as e:
                    expiry_date = f'Invalid Date: {expiry_date}'
                    expiry_status = 'DATE ERROR'
                    print(f"⚠️ Date parsing error for {product.get('product_name', 'Unknown')}: {e}")

            html += f'''
            <tr class="{row_class}">
                <td>{product.get('product_id', 'N/A')}</td>
                <td>{product.get('product_name', 'N/A')}</td>
                <td>{product.get('current_stock', 0):.0f}</td>
                <td>{product.get('ideal_stock_level', 0):.0f}</td>
                <td>{product.get('stock_ratio', 0):.2f}</td>
                <td>{expiry_date}</td>
                <td>{days_to_expire}</td>
                <td><strong>{expiry_status}</strong></td>
                <td>{product.get('action', 'No action specified')}</td>
                <td>{product.get('order_quantity', 0):.0f}</td>
            </tr>
            '''

        html += '</table>'

        # Legend
        html += '''
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h4>📅 Expiry Status Color Legend:</h4>
            <ul style="list-style-type: none; padding: 0;">
                <li style="background-color: #ffcccc; padding: 8px; margin: 5px 0; border-radius: 3px;">🔴 <strong>EXPIRED</strong> - Immediate removal required</li>
                <li style="background-color: #fff3cd; padding: 8px; margin: 5px 0; border-radius: 3px;">🟡 <strong>EXPIRING SOON (≤7 days)</strong> - Urgent action needed</li>
                <li style="background-color: #d1ecf1; padding: 8px; margin: 5px 0; border-radius: 3px;">🔵 <strong>EXPIRING THIS MONTH (≤30 days)</strong> - Plan clearance/discount</li>
                <li style="padding: 8px; margin: 5px 0;">⚪ <strong>NORMAL</strong> - Good expiration timeline</li>
            </ul>
        </div>
        '''

        # Summary statistics
        if summary_stats:
            html += f'''
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4>📈 CSV Data Summary Statistics:</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                    <div style="min-width: 200px;">
                        <strong>📦 Inventory Stats:</strong>
                        <ul>
                            <li>Total Products: {summary_stats.get('total_products', 0)}</li>
                            <li>Critical Stock Items: {summary_stats.get('critical_items', 0)}</li>
                            <li>Overstocked Items: {summary_stats.get('overstocked_items', 0)}</li>
                        </ul>
                    </div>
                    <div style="min-width: 200px;">
                        <strong>📅 Expiration Stats:</strong>
                        <ul>
                            <li>Expired Products: {summary_stats.get('expired_products', 0)}</li>
                            <li>Expiring Soon (≤7 days): {summary_stats.get('expiring_soon', 0)}</li>
                            <li>Expiring This Month (≤30 days): {summary_stats.get('expiring_month', 0)}</li>
                        </ul>
                    </div>
                </div>
            </div>
            '''

        html += '''
        <div style="margin-top: 30px; padding: 15px; background-color: #f0f0f0; border-radius: 5px; text-align: center;">
            <p><em>This report is generated from your uploaded CSV file. Please verify all data and take appropriate actions for expired and expiring products.</em></p>
        </div>
        </body></html>
        '''
        return html


class CSVExpirationManager:
    def __init__(self):
        self.products_df = None
        self.file_path = None
        self.email_system = EmailNotificationSystem()

    def load_csv_file(self, csv_file_path):
        """Load inventory data from CSV file with expiration dates"""
        try:
            if not os.path.exists(csv_file_path):
                print(f"❌ File not found: {csv_file_path}")
                return False

            # Load CSV with error handling
            self.products_df = pd.read_csv(csv_file_path)
            self.file_path = csv_file_path
            
            print(f"✅ Loaded CSV file: {csv_file_path}")
            print(f"📊 Found {len(self.products_df)} products")
            print(f"📋 Columns: {list(self.products_df.columns)}")
            
            # Validate required columns
            required_cols = ['product_id', 'product_name', 'current_stock']
            missing_cols = [col for col in required_cols if col not in self.products_df.columns]
            
            if missing_cols:
                print(f"⚠️ Missing required columns: {missing_cols}")
                print("💡 Expected columns: product_id, product_name, current_stock, ideal_stock_level, expiration_date")
                return False

            # Check for expiration_date column
            if 'expiration_date' not in self.products_df.columns:
                print("⚠️ No 'expiration_date' column found. Adding empty expiration dates.")
                self.products_df['expiration_date'] = None

            # Check for ideal_stock_level column
            if 'ideal_stock_level' not in self.products_df.columns:
                print("⚠️ No 'ideal_stock_level' column found. Setting default values.")
                self.products_df['ideal_stock_level'] = self.products_df['current_stock'] * 1.5

            # Clean and validate data
            self._clean_data()
            
            return True

        except Exception as e:
            print(f"❌ Error loading CSV file: {e}")
            return False

    def _clean_data(self):
        """Clean and validate the loaded data"""
        try:
            # Remove rows with missing essential data
            initial_count = len(self.products_df)
            self.products_df = self.products_df.dropna(subset=['product_id', 'product_name'])
            
            if len(self.products_df) < initial_count:
                print(f"⚠️ Removed {initial_count - len(self.products_df)} rows with missing essential data")

            # Convert numeric columns
            numeric_cols = ['current_stock', 'ideal_stock_level']
            for col in numeric_cols:
                if col in self.products_df.columns:
                    self.products_df[col] = pd.to_numeric(self.products_df[col], errors='coerce').fillna(0)

            # Clean expiration dates
            if 'expiration_date' in self.products_df.columns:
                self.products_df['expiration_date'] = self.products_df['expiration_date'].astype(str)
                self.products_df['expiration_date'] = self.products_df['expiration_date'].replace(['nan', 'None', 'NaT', ''], None)

            print("✅ Data cleaned and validated")

        except Exception as e:
            print(f"❌ Error cleaning data: {e}")

    def get_products_with_expiration(self):
        """Get all products that have expiration dates"""
        if self.products_df is None:
            return []

        products_with_expiry = []
        
        for _, row in self.products_df.iterrows():
            if pd.notna(row.get('expiration_date')) and str(row.get('expiration_date')).strip() not in ['', 'None', 'nan']:
                products_with_expiry.append(row.to_dict())

        print(f"📅 Found {len(products_with_expiry)} products with expiration dates")
        return products_with_expiry

    def check_expiring_products_from_csv(self, days_ahead=30):
        """Check for products expiring within specified days from CSV data"""
        if self.products_df is None:
            print("❌ No CSV data loaded")
            return []

        expiring_products = []
        current_date = datetime.now()

        for _, product in self.products_df.iterrows():
            expiry_date = product.get('expiration_date')
            
            if pd.notna(expiry_date) and str(expiry_date).strip() not in ['', 'None', 'nan']:
                try:
                    # Handle multiple date formats
                    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
                    exp_date = None
                    
                    for fmt in date_formats:
                        try:
                            exp_date = datetime.strptime(str(expiry_date).strip(), fmt)
                            break
                        except ValueError:
                            continue
                    
                    if exp_date is None:
                        print(f"⚠️ Invalid date format for {product.get('product_name', 'Unknown')}: {expiry_date}")
                        continue

                    days_to_expire = (exp_date - current_date).days

                    if days_to_expire <= days_ahead:
                        stock_ratio = (product.get('current_stock', 0) / 
                                     max(product.get('ideal_stock_level', 1), 1))
                        
                        # Determine action based on expiration and stock
                        if days_to_expire < 0:
                            action = f"🚨 REMOVE IMMEDIATELY - Expired {abs(days_to_expire)} days ago"
                            order_qty = 0
                        elif days_to_expire == 0:
                            action = "🔴 EXPIRES TODAY - Remove or discount heavily"
                            order_qty = 0
                        elif days_to_expire <= 7:
                            action = "🟡 URGENT - Discount/clearance sale needed immediately"
                            order_qty = max(0, product.get('ideal_stock_level', 0) - product.get('current_stock', 0))
                        else:
                            action = "🔵 MONITOR - Plan clearance sale if needed"
                            order_qty = max(0, product.get('ideal_stock_level', 0) - product.get('current_stock', 0))

                        expiring_products.append({
                            'product_id': product.get('product_id', 'Unknown'),
                            'product_name': product.get('product_name', 'Unknown'),
                            'current_stock': product.get('current_stock', 0),
                            'ideal_stock_level': product.get('ideal_stock_level', 0),
                            'stock_ratio': stock_ratio,
                            'expiration_date': exp_date.strftime('%Y-%m-%d'),
                            'days_to_expire': days_to_expire,
                            'action': action,
                            'order_quantity': order_qty
                        })

                except Exception as e:
                    print(f"❌ Error processing expiration for {product.get('product_name', 'Unknown')}: {e}")
                    continue

        return expiring_products

    def get_expired_products_from_csv(self):
        """Get products that have already expired from CSV"""
        expiring = self.check_expiring_products_from_csv(days_ahead=-1)
        return [p for p in expiring if p['days_to_expire'] < 0]

    def get_expiring_soon_from_csv(self, days=7):
        """Get products expiring within specified days from CSV"""
        expiring = self.check_expiring_products_from_csv(days_ahead=days)
        return [p for p in expiring if 0 <= p['days_to_expire'] <= days]

    def generate_csv_expiration_summary(self):
        """Generate summary statistics for CSV expiration data"""
        if self.products_df is None:
            return {}

        total_products = len(self.products_df)
        products_with_expiry = len(self.get_products_with_expiration())
        expired = len(self.get_expired_products_from_csv())
        expiring_soon = len(self.get_expiring_soon_from_csv(7))
        expiring_month = len(self.get_expiring_soon_from_csv(30)) - expiring_soon

        # Calculate stock-related stats
        if 'ideal_stock_level' in self.products_df.columns:
            self.products_df['stock_ratio'] = (self.products_df['current_stock'] / 
                                             self.products_df['ideal_stock_level'].replace(0, 1))
            critical_items = len(self.products_df[self.products_df['stock_ratio'] < 0.2])
            overstocked_items = len(self.products_df[self.products_df['stock_ratio'] > 1.5])
        else:
            critical_items = 0
            overstocked_items = 0

        return {
            'total_products': total_products,
            'products_with_expiry': products_with_expiry,
            'expired_products': expired,
            'expiring_soon': expiring_soon,
            'expiring_month': expiring_month,
            'critical_items': critical_items,
            'overstocked_items': overstocked_items,
            'file_path': self.file_path
        }

    def send_csv_expiration_alerts(self):
        """Send email alerts for CSV expiration data"""
        if not self.email_system.is_configured:
            return False, "Email system not configured"

        try:
            results = []
            
            # Get expired products
            expired_products = self.get_expired_products_from_csv()
            if expired_products:
                summary = self.generate_csv_expiration_summary()
                success, message = self.email_system.send_stock_alert('expired', expired_products, summary)
                results.append(('expired', len(expired_products), success, message))
                print(f"📧 Expired products alert: {message}")

            # Get products expiring soon
            expiring_soon = self.get_expiring_soon_from_csv(7)
            if expiring_soon:
                summary = self.generate_csv_expiration_summary()
                success, message = self.email_system.send_stock_alert('expiring', expiring_soon, summary)
                results.append(('expiring_soon', len(expiring_soon), success, message))
                print(f"📧 Expiring soon alert: {message}")

            if not results:
                return True, "No expiration alerts needed - all products are within normal expiration range"

            return True, results

        except Exception as e:
            error_msg = f"Error sending CSV expiration alerts: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
