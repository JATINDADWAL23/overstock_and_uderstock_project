from flask import Flask, render_template_string, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
from inventory_system import EmailNotificationSystem, CSVExpirationManager
from csv_expiration_processor import CSVExpirationProcessor
from config import email_config

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize systems
csv_processor = CSVExpirationProcessor()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Your existing routes...

@app.route('/csv-expiration-dashboard')
def csv_expiration_dashboard():
    """CSV Expiration Management Dashboard"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📅 CSV Expiration Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .card { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 8px; }
            .upload-card { background-color: #e3f2fd; border-color: #2196f3; }
            .sample-card { background-color: #fff8e1; border-color: #ff9800; }
            .btn { display: inline-block; padding: 12px 25px; margin: 8px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .btn-success { background: #28a745; }
            .btn-warning { background: #ffc107; color: black; }
            .btn-danger { background: #dc3545; }
            .file-input { margin: 10px 0; }
            h1 { color: #333; margin-bottom: 30px; }
            .info-box { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📅 CSV Expiration Management Dashboard</h1>
            
            <div class="card upload-card">
                <h3>📤 Upload Your CSV File</h3>
                <p>Upload your inventory CSV file to check for expiring products and send alerts.</p>
                
                <form action="/upload-csv" method="post" enctype="multipart/form-data">
                    <div class="file-input">
                        <input type="file" name="csv_file" accept=".csv" required>
                    </div>
                    <button type="submit" class="btn btn-success">📤 Upload & Analyze CSV</button>
                </form>
                
                <div class="info-box">
                    <strong>📋 Required CSV Columns:</strong>
                    <ul>
                        <li><code>product_id</code> - Unique product identifier</li>
                        <li><code>product_name</code> - Name of the product</li>
                        <li><code>current_stock</code> - Current stock quantity</li>
                        <li><code>ideal_stock_level</code> - Target stock level (optional)</li>
                        <li><code>expiration_date</code> - Product expiry date (YYYY-MM-DD format)</li>
                    </ul>
                </div>
            </div>

            <div class="card sample-card">
                <h3>📋 Sample Data & Testing</h3>
                <p>Don't have a CSV file? Create sample data for testing the expiration alert system.</p>
                
                <a href="/create-sample-csv" class="btn btn-warning">📋 Create Sample CSV</a>
                <a href="/download-csv-template" class="btn">📥 Download CSV Template</a>
            </div>

            <div class="card">
                <h3>📊 Recent CSV Files</h3>
                <p>Process previously uploaded CSV files.</p>
                <a href="/list-csv-files" class="btn">📂 View Uploaded Files</a>
            </div>

            <div class="card">
                <h3>⚙️ Quick Actions</h3>
                <a href="/test-csv-processor" class="btn">🧪 Test CSV Processor</a>
                <a href="/validate-csv-format" class="btn">✅ Validate CSV Format</a>
                <a href="/" class="btn" style="background: #6c757d;">← Back to Main Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    """Handle CSV file upload and processing"""
    try:
        if 'csv_file' not in request.files:
            return '''
            <h1>❌ No File Selected</h1>
            <p>Please select a CSV file to upload.</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''

        file = request.files['csv_file']
        if file.filename == '':
            return '''
            <h1>❌ No File Selected</h1>
            <p>Please select a CSV file to upload.</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the uploaded CSV
            analysis, message = csv_processor.process_uploaded_csv(file_path)
            
            if analysis:
                return generate_csv_analysis_report(analysis, filename)
            else:
                return f'''
                <h1>❌ CSV Processing Failed</h1>
                <p><strong>Error:</strong> {message}</p>
                <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
                '''
        else:
            return '''
            <h1>❌ Invalid File Type</h1>
            <p>Please upload a valid CSV file.</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''

    except Exception as e:
        return f'''
        <h1>❌ Upload Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
        '''

def generate_csv_analysis_report(analysis, filename):
    """Generate HTML report for CSV analysis"""
    expired_count = len(analysis['expired_products'])
    expiring_soon_count = len(analysis['expiring_soon'])
    expiring_month_count = len(analysis['expiring_month'])
    
    # Create detailed tables
    expired_table = create_product_table(analysis['expired_products'], 'expired')
    expiring_table = create_product_table(analysis['expiring_soon'], 'expiring-soon')
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>📊 CSV Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; }}
            .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
            .stat-card {{ flex: 1; padding: 20px; border-radius: 8px; text-align: center; }}
            .expired {{ background-color: #ffebee; border: 2px solid #f44336; }}
            .expiring {{ background-color: #fff8e1; border: 2px solid #ff9800; }}
            .normal {{ background-color: #e8f5e8; border: 2px solid #4caf50; }}
            .btn {{ display: inline-block; padding: 12px 25px; margin: 8px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            .btn-danger {{ background: #dc3545; }}
            .btn-warning {{ background: #ffc107; color: black; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .expired-row {{ background-color: #ffcccc; }}
            .expiring-row {{ background-color: #fff3cd; }}
            h1, h2 {{ color: #333; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 CSV Expiration Analysis Report</h1>
            <p><strong>File:</strong> {filename}</p>
            <p><strong>Analyzed on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="summary">
                <div class="stat-card expired">
                    <h3>🔴 EXPIRED</h3>
                    <h2>{expired_count}</h2>
                    <p>Products</p>
                </div>
                <div class="stat-card expiring">
                    <h3>🟡 EXPIRING SOON</h3>
                    <h2>{expiring_soon_count}</h2>
                    <p>Within 7 days</p>
                </div>
                <div class="stat-card normal">
                    <h3>📅 TOTAL WITH EXPIRY</h3>
                    <h2>{analysis['products_with_expiry']}</h2>
                    <p>Out of {analysis['total_products']}</p>
                </div>
            </div>

            <h2>🚨 Action Required</h2>
            <div style="margin: 20px 0;">
                <a href="/send-csv-alerts/{filename}" class="btn btn-danger">📧 Send Expired Products Alert</a>
                <a href="/send-csv-expiring-alerts/{filename}" class="btn btn-warning">📧 Send Expiring Products Alert</a>
                <a href="/download-csv-report/{filename}" class="btn">📥 Download Full Report</a>
            </div>

            {expired_table}
            {expiring_table}

            <h2>📈 Summary Statistics</h2>
            <ul>
                <li>Total Products in CSV: {analysis['total_products']}</li>
                <li>Products with Expiration Dates: {analysis['products_with_expiry']}</li>
                <li>Expired Products: {expired_count}</li>
                <li>Expiring Soon (≤7 days): {expiring_soon_count}</li>
                <li>Expiring This Month (≤30 days): {expiring_month_count}</li>
            </ul>

            <div style="margin-top: 40px;">
                <a href="/csv-expiration-dashboard" class="btn">← Back to CSV Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    '''

def create_product_table(products, table_type):
    """Create HTML table for products"""
    if not products:
        return f'<p>✅ No {table_type} products found.</p>'
    
    title = "🔴 EXPIRED PRODUCTS" if table_type == 'expired' else "🟡 EXPIRING SOON"
    row_class = 'expired-row' if table_type == 'expired' else 'expiring-row'
    
    table = f'''
    <h2>{title} ({len(products)})</h2>
    <table>
        <tr>
            <th>Product ID</th>
            <th>Product Name</th>
            <th>Current Stock</th>
            <th>Expiration Date</th>
            <th>Days to Expire</th>
            <th>Recommended Action</th>
        </tr>
    '''
    
    for product in products:
        days = product['days_to_expire']
        days_display = f"{abs(days)} days ago" if days < 0 else f"{days} days"
        
        table += f'''
        <tr class="{row_class}">
            <td>{product['product_id']}</td>
            <td>{product['product_name']}</td>
            <td>{product['current_stock']:.0f}</td>
            <td>{product['expiration_date']}</td>
            <td>{days_display}</td>
            <td>{product['action']}</td>
        </tr>
        '''
    
    table += '</table>'
    return table

@app.route('/create-sample-csv')
def create_sample_csv():
    """Create sample CSV file for testing"""
    try:
        sample_file = csv_processor.create_sample_csv()
        if sample_file:
            return f'''
            <h1>✅ Sample CSV Created Successfully!</h1>
            <p><strong>File:</strong> {sample_file}</p>
            <p>Sample CSV contains products with various expiration statuses for testing.</p>
            
            <div style="margin: 20px 0;">
                <a href="/process-csv/{os.path.basename(sample_file)}" style="display: inline-block; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">📊 Process Sample CSV</a>
                <a href="/csv-expiration-dashboard" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; margin-left: 10px;">← Back to Dashboard</a>
            </div>
            '''
        else:
            return '''
            <h1>❌ Failed to Create Sample CSV</h1>
            <p>There was an error creating the sample file.</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''
    except Exception as e:
        return f'''
        <h1>❌ Error Creating Sample CSV</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
        '''

@app.route('/process-csv/<filename>')
def process_existing_csv(filename):
    """Process an existing CSV file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            return '''
            <h1>❌ File Not Found</h1>
            <p>The specified CSV file was not found.</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''
        
        analysis, message = csv_processor.process_uploaded_csv(file_path)
        if analysis:
            return generate_csv_analysis_report(analysis, filename)
        else:
            return f'''
            <h1>❌ Processing Failed</h1>
            <p><strong>Error:</strong> {message}</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''
    except Exception as e:
        return f'''
        <h1>❌ Processing Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
        '''

@app.route('/send-csv-alerts/<filename>')
def send_csv_alerts(filename):
    """Send alerts for specific CSV file"""
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        success, results = csv_processor.send_expiration_alerts_for_csv(file_path)
        
        if success:
            html = f'''
            <h1>✅ Expiration Alerts Sent Successfully!</h1>
            <p><strong>File:</strong> {filename}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>📧 Alert Results:</h3>
            '''
            
            if isinstance(results, list):
                for alert_type, count, email_success, message in results:
                    status_icon = "✅" if email_success else "❌"
                    html += f'<p>{status_icon} <strong>{alert_type.replace("_", " ").title()}:</strong> {count} products - {message}</p>'
            else:
                html += f'<p>ℹ️ {results}</p>'
            
            html += '''
            <div style="margin-top: 30px;">
                <a href="/csv-expiration-dashboard" style="display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">← Back to Dashboard</a>
            </div>
            '''
            return html
        else:
            return f'''
            <h1>❌ Failed to Send Alerts</h1>
            <p><strong>Error:</strong> {results}</p>
            <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
            '''
            
    except Exception as e:
        return f'''
        <h1>❌ Alert Error</h1>
        <p><strong>Error:</strong> {str(e)}</p>
        <a href="/csv-expiration-dashboard">← Back to Dashboard</a>
        '''

# Add to your main route
@app.route('/')
def dashboard():
    return '''
    <html>
    <head>
        <title>Inventory Management System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 8px; }
            .btn { display: inline-block; padding: 12px 25px; margin: 8px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .btn-success { background: #28a745; }
            .btn-warning { background: #ffc107; color: black; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏢 Inventory Management System</h1>
            
            <div class="card">
                <h3>📊 Stock Management</h3>
                <p>Manage stock levels and send alerts for critical inventory.</p>
                <a href="/debug-email" class="btn">🧪 Test Email System</a>
            </div>

            <div class="card">
                <h3>📅 CSV Expiration Management</h3>
                <p>Upload your CSV files to check for expiring products and send automated alerts.</p>
                <a href="/csv-expiration-dashboard" class="btn btn-success">📤 Upload CSV & Check Expiration</a>
                <a href="/create-sample-csv" class="btn btn-warning">📋 Create Sample CSV</a>
            </div>

            <div class="card">
                <h3>⚙️ System Status</h3>
                <p>✅ Email System: Configured</p>
                <p>✅ CSV Processor: Ready</p>
                <p>✅ Expiration Alerts: Active</p>
            </div>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    # Ensure upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    print("🚀 Starting Inventory Management System with CSV Expiration Support...")
    print("📍 Main Dashboard: http://127.0.0.1:5000")
    print("📍 CSV Expiration Dashboard: http://127.0.0.1:5000/csv-expiration-dashboard")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)
