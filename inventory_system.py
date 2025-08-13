import pandas as pd
import numpy as np
from datetime import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        self.smtp_port = int(smtp_port)  # Ensure port is integer
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
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ", ".join(self.recipient_emails)
            
            # Set subject based on alert type
            subjects = {
                "critical": "🚨 CRITICAL STOCK ALERT - Immediate Action Required",
                "overstock": "📦 OVERSTOCK ALERT - Inventory Review Needed", 
                "understock": "⚠️ UNDERSTOCK ALERT - Reorder Required"
            }
            msg['Subject'] = subjects.get(alert_type, "📊 Inventory Status Report")
            
            # Create HTML body
            html_body = self._create_email_body(alert_type, product_data, summary_stats)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send using Gmail SMTP with proper error handling
            print("🔗 Connecting to Gmail SMTP server...")
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.set_debuglevel(1)  # Enable detailed debugging
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
            print("💡 SOLUTION: Use Gmail App Password instead of regular password!")
            print("💡 Steps: 1) Enable 2FA on Gmail 2) Generate App Password 3) Use App Password here")
            return False, "Authentication failed - Use Gmail App Password, not regular password"
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"❌ Recipients refused: {str(e)}"
            print(error_msg)
            return False, "Invalid recipient email addresses"
            
        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"❌ SMTP Server disconnected: {str(e)}"
            print(error_msg)
            return False, "SMTP server connection failed"
            
        except smtplib.SMTPConnectError as e:
            error_msg = f"❌ SMTP Connection error: {str(e)}"
            print(error_msg)
            return False, "Cannot connect to SMTP server - check network/firewall"
            
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
                body {{ 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 0; 
                    padding: 20px; 
                    background-color: #f8fafc; 
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto; 
                    background: white; 
                    border-radius: 12px; 
                    overflow: hidden; 
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                }}
                .header {{ 
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); 
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0 0; opacity: 0.9; }}
                
                .alert-section {{ 
                    padding: 20px 30px; 
                    margin: 0; 
                }}
                .alert-critical {{ 
                    background: #fef2f2; 
                    border-left: 5px solid #dc2626; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 0 8px 8px 0; 
                }}
                .alert-warning {{ 
                    background: #fffbeb; 
                    border-left: 5px solid #d97706; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 0 8px 8px 0; 
                }}
                .alert-overstock {{ 
                    background: #f0f9ff; 
                    border-left: 5px solid #0ea5e9; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 0 8px 8px 0; 
                }}
                
                .table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 20px 0; 
                    border-radius: 8px; 
                    overflow: hidden; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                }}
                .table th {{ 
                    background: #f8fafc; 
                    padding: 15px 12px; 
                    text-align: left; 
                    font-weight: 600; 
                    color: #374151; 
                    border-bottom: 2px solid #e5e7eb; 
                }}
                .table td {{ 
                    padding: 12px; 
                    border-bottom: 1px solid #f3f4f6; 
                    color: #374151; 
                }}
                .table tr:nth-child(even) {{ background: #f9fafb; }}
                .table tr:hover {{ background: #f3f4f6; }}
                
                .summary {{ 
                    background: #f0f9ff; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px; 
                    border: 1px solid #e0f2fe; 
                }}
                .summary h4 {{ 
                    color: #0369a1; 
                    margin: 0 0 15px 0; 
                }}
                .summary ul {{ 
                    margin: 0; 
                    padding-left: 20px; 
                }}
                .summary li {{ 
                    margin-bottom: 8px; 
                    color: #374151; 
                }}
                
                .footer {{ 
                    background: #f8fafc; 
                    padding: 20px 30px; 
                    text-align: center; 
                    border-top: 1px solid #e5e7eb; 
                    color: #6b7280; 
                }}
                .footer p {{ margin: 5px 0; }}
                
                .action-required {{ 
                    color: #dc2626; 
                    font-weight: 600; 
                }}
                .restock-needed {{ 
                    color: #d97706; 
                    font-weight: 600; 
                }}
                .optimal {{ 
                    color: #059669; 
                    font-weight: 600; 
                }}
                .overstocked {{ 
                    color: #0ea5e9; 
                    font-weight: 600; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Inventory Management Alert</h1>
                    <p>Generated on: {current_time}</p>
                </div>
                
                <div class="alert-section">
        '''
        
        # Add alert-specific content
        if alert_type == "critical":
            html += '''
                    <div class="alert-critical">
                        <h3 style="margin: 0 0 10px 0; color: #dc2626;">🚨 CRITICAL STOCK ALERT</h3>
                        <p style="margin: 0;"><strong>Immediate action required!</strong> The following products have critically low stock levels and need urgent restocking.</p>
                    </div>
            '''
        elif alert_type == "overstock":
            html += '''
                    <div class="alert-overstock">
                        <h3 style="margin: 0 0 10px 0; color: #0ea5e9;">📦 OVERSTOCK ALERT</h3>
                        <p style="margin: 0;">The following products are overstocked and may require inventory reduction or promotional activities.</p>
                    </div>
            '''
        elif alert_type == "understock":
            html += '''
                    <div class="alert-warning">
                        <h3 style="margin: 0 0 10px 0; color: #d97706;">⚠️ UNDERSTOCK ALERT</h3>
                        <p style="margin: 0;">The following products need restocking to maintain optimal inventory levels.</p>
                    </div>
            '''
        
        # Add product table
        html += '''
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Product ID</th>
                                <th>Product Name</th>
                                <th>Current Stock</th>
                                <th>Ideal Stock</th>
                                <th>Stock Ratio</th>
                                <th>Recommended Action</th>
                                <th>Order Quantity</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for product in product_data:
            # Determine action class for styling
            action = product.get('action', '')
            action_class = 'optimal'
            if 'URGENT' in action or 'CRITICAL' in action:
                action_class = 'action-required'
            elif 'RESTOCK' in action:
                action_class = 'restock-needed'
            elif 'OVERSTOCK' in action:
                action_class = 'overstocked'
            
            html += f'''
                            <tr>
                                <td><strong>{product.get('product_id', 'N/A')}</strong></td>
                                <td>{product.get('product_name', 'N/A')}</td>
                                <td style="text-align: center;">{product.get('current_stock', 0):.0f}</td>
                                <td style="text-align: center;">{product.get('ideal_stock_level', 0):.0f}</td>
                                <td style="text-align: center;">{product.get('stock_ratio', 0):.2f}</td>
                                <td class="{action_class}">{product.get('action', 'No action specified')}</td>
                                <td style="text-align: center;">{product.get('order_quantity', 0):.0f}</td>
                            </tr>
            '''
        
        html += '''
                        </tbody>
                    </table>
        '''
        
        # Add summary statistics if provided
        if summary_stats:
            html += '''
                    <div class="summary">
                        <h4>📊 Summary Statistics</h4>
                        <ul>
            '''
            for key, value in summary_stats.items():
                formatted_key = key.replace('_', ' ').title()
                html += f'<li><strong>{formatted_key}:</strong> {value}</li>'
            html += '''
                        </ul>
                    </div>
            '''
        
        html += '''
                </div>
                
                <div class="footer">
                    <p><strong>This is an automated message from the Inventory Management System.</strong></p>
                    <p>Please take appropriate action based on the recommendations above.</p>
                    <p style="margin-top: 15px; font-size: 12px;">Generated by Inventory Management Pro v2.1</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html

class DataProcessor:
    def prepare_data(self, data):
        """Fast data preparation for small datasets"""
        data = data.copy()
        
        # Basic data cleaning (simplified)
        data['current_stock'] = pd.to_numeric(data['current_stock'], errors='coerce').fillna(0)
        data['ideal_stock_level'] = pd.to_numeric(data['ideal_stock_level'], errors='coerce').fillna(0)
        
        # Quick calculations
        data['stock_ratio'] = data['current_stock'] / (data['ideal_stock_level'] + 0.01)
        data['stock_variance'] = data['current_stock'] - data['ideal_stock_level']
        
        return data

class InventoryOptimizer:
    def optimize_inventory(self, row):
        """Fast optimization for single product"""
        current_stock = float(row['current_stock'])
        ideal_stock = float(row['ideal_stock_level'])
        status = str(row['status']).lower()
        
        # Quick ratio calculation
        stock_ratio = current_stock / ideal_stock if ideal_stock > 0 else 0
        shortage = ideal_stock - current_stock
        
        # Fast action determination
        if status in ['critical', 'out of stock'] or stock_ratio < 0.3:
            action, order_qty = "🚨 URGENT RESTOCK", max(shortage * 1.2, 0)
        elif stock_ratio < 0.5:
            action, order_qty = "⚠️ RESTOCK NEEDED", max(shortage, 0)
        elif stock_ratio < 0.8:
            action, order_qty = "📈 RESTOCK RECOMMENDED", max(shortage * 0.8, 0)
        elif stock_ratio > 1.5:
            action, order_qty = "📦 OVERSTOCKED", 0
        else:
            action, order_qty = "✅ OPTIMAL", 0
            
        # Estimate days of stock (handle division by zero)
        daily_demand = ideal_stock / 30 if ideal_stock > 0 else 1
        days_stock = current_stock / daily_demand if daily_demand > 0 else 999
        
        # Cap days_stock to reasonable maximum to avoid infinity in templates
        days_stock = min(days_stock, 999)
        
        return {
            'product_id': row['product_id'],
            'product_name': row['product_name'],
            'current_stock': current_stock,
            'ideal_stock_level': ideal_stock,
            'stock_ratio': stock_ratio,
            'stock_variance': shortage,
            'current_status': row['status'],
            'action': action,
            'order_quantity': order_qty,
            'days_of_stock': days_stock
        }

class AlertSystem:
    def __init__(self, email_system=None):
        self.email_system = email_system
        self.email_enabled = False
        
    def enable_email_notifications(self, email_system):
        self.email_system = email_system
        self.email_enabled = True
        print("📧 Email notifications enabled")
    
    def check_alerts(self, optimization):
        """Quick alert generation"""
        alerts = []
        ratio = optimization['stock_ratio'] 
        name = optimization['product_name']
        status = optimization['current_status'].lower()
        
        if ratio < 0.3 or status == 'critical':
            alerts.append(f"🚨 CRITICAL: {name} needs immediate attention!")
        elif ratio < 0.5:
            alerts.append(f"⚠️ LOW: {name} below optimal levels")
        elif ratio > 1.5:
            alerts.append(f"📦 OVERSTOCK: {name} exceeds ideal levels")
            
        return alerts
    
    def send_bulk_alerts(self, recommendations):
        """Send email alerts if configured"""
        if not self.email_enabled or not self.email_system:
            print("⚠️ Email notifications disabled - skipping email alerts")
            return
            
        print("📧 Processing email alerts...")
        critical, under, over = [], [], []
        
        for rec in recommendations.values():
            ratio = rec['stock_ratio']
            if ratio < 0.3: 
                critical.append(rec)
            elif ratio < 0.5: 
                under.append(rec)  
            elif ratio > 1.5: 
                over.append(rec)
        
        # Create summary statistics
        summary_stats = {
            'total_products': len(recommendations),
            'critical_items': len(critical),
            'understock_items': len(under),
            'overstock_items': len(over),
            'optimal_items': len(recommendations) - len(critical) - len(under) - len(over)
        }
        
        # Send emails for each category
        if critical: 
            print(f"📧 Sending critical alert for {len(critical)} products")
            self.email_system.send_stock_alert("critical", critical, summary_stats)
        if under: 
            print(f"📧 Sending understock alert for {len(under)} products")
            self.email_system.send_stock_alert("understock", under, summary_stats)
        if over: 
            print(f"📧 Sending overstock alert for {len(over)} products")
            self.email_system.send_stock_alert("overstock", over, summary_stats)

class InventoryManagementSystem:
    def __init__(self):
        self.data_processor = DataProcessor()
        self.inventory_optimizer = InventoryOptimizer()
        self.email_system = EmailNotificationSystem()
        self.alert_system = AlertSystem(self.email_system)
        
    def load_custom_data(self, filepath):
        """Load and validate CSV data"""
        data = pd.read_csv(filepath)
        required_cols = ['product_id', 'product_name', 'current_stock', 'ideal_stock_level', 'status']
        
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Missing column: {col}")
        return data
    
    def create_sample_data(self):
        """Create sample data for testing"""
        return pd.DataFrame({
            'product_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
            'product_name': ['Organic Rice 5kg', 'Olive Oil 1L', 'Whole Wheat Bread', 'Fresh Milk 1L', 'Brown Sugar 1kg'],
            'current_stock': [120, 30, 60, 15, 80],
            'ideal_stock_level': [100, 80, 60, 50, 75],
            'status': ['Overstock', 'Understock', 'In Stock', 'Critical', 'Good']
        })
    
    def run_analysis(self, data):
        """FAST analysis - optimized for small datasets"""
        print("🚀 Starting fast analysis...")
        
        # Step 1: Quick data preparation
        processed_data = self.data_processor.prepare_data(data)
        print(f"✅ Processed {len(processed_data)} products")
        
        # Step 2: Fast optimization (no complex forecasting)
        recommendations = {}
        alerts_all = []
        
        for _, row in processed_data.iterrows():
            # Quick optimization per product
            optimization = self.inventory_optimizer.optimize_inventory(row)
            recommendations[row['product_id']] = optimization
            
            # Quick alerts
            alerts = self.alert_system.check_alerts(optimization)
            alerts_all.extend(alerts)
        
        print(f"✅ Analysis complete! Generated {len(alerts_all)} alerts")
        
        # Return simplified results (no complex forecasting data)
        return {}, recommendations, alerts_all
