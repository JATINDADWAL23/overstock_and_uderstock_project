import re
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField
from wtforms.validators import DataRequired, Email
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, io, base64, time, json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
from threading import Thread
import json
import os
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-secret-key-for-forms'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULTS_FOLDER'] = 'static/results'

# Email config - replace with your email and app password
SENDER_EMAIL = "jatindadwal56@gmail.com"
SENDER_PASSWORD = "qekrgjxielyfyadc"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Forms
class FileUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[FileRequired(), FileAllowed(['csv'])])

class EmailForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

def get_receiver_email():
    try:
        with open('receiver_email.txt') as f:
            email = f.read().strip()
            return email if email else None
    except Exception:
        return None

def send_email_async(func, *args):
    Thread(target=func, args=args).start()

def add_upload_history(filename, product_count, upload_time):
    entry = {
        "filename": filename,
        "products": product_count,
        "uploaded_at": upload_time
    }
    try:
        if os.path.exists('upload_history.json'):
            with open('upload_history.json', 'r') as f:
                history = json.load(f)
        else:
            history = []
        history.insert(0, entry)  # newest on top
        with open('upload_history.json', 'w') as f:
            json.dump(history, f)
    except Exception as e:
        print("Upload history log error:", e)

def load_history():
    try:
        with open('upload_history.json', 'r') as f:
            return json.load(f)
    except:
        return []

def calculate_file_hash(filepath):
    """Calculate SHA-256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def is_duplicate_file(file_hash):
    """Check if a file with this hash has been uploaded before"""
    try:
        with open('file_hashes.json', 'r') as f:
            hashes = json.load(f)
            return file_hash in hashes
    except:
        return False

def save_file_hash(file_hash, filename, timestamp):
    """Save file hash to prevent duplicate uploads"""
    try:
        if os.path.exists('file_hashes.json'):
            with open('file_hashes.json', 'r') as f:
                hashes = json.load(f)
        else:
            hashes = {}
        
        hashes[file_hash] = {
            'filename': filename,
            'timestamp': timestamp
        }
        
        with open('file_hashes.json', 'w') as f:
            json.dump(hashes, f)
    except Exception as e:
        print(f"Error saving file hash: {e}")

def save_results(results):
    """Save analysis results to a JSON file"""
    try:
        timestamp = str(int(time.time()))
        results_file = os.path.join(app.config['RESULTS_FOLDER'], f'results_{timestamp}.json')
        
        # Ensure directory exists
        os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
        
        # Save the results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Update latest results pointer
        with open('latest_results.txt', 'w') as f:
            f.write(timestamp)
            
        print(f"✅ Results saved to: {results_file}")
        return results_file
        
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return None

def load_results():
    """Load the most recent analysis results"""
    try:
        results_folder = app.config['RESULTS_FOLDER']
        if not os.path.exists(results_folder):
            return None
            
        result_files = [f for f in os.listdir(results_folder) if f.startswith('results_') and f.endswith('.json')]
        if not result_files:
            return None
            
        latest_file = max(result_files, key=lambda x: int(x.split('_')[1].split('.')[0]))
        with open(os.path.join(results_folder, latest_file), 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return None

def analyze_data_with_ai(df):
    """Analyze inventory data and provide AI-enhanced recommendations"""
    try:
        # Convert columns to appropriate types
        df['current_stock'] = pd.to_numeric(df['current_stock'], errors='coerce')
        df['ideal_stock_level'] = pd.to_numeric(df['ideal_stock_level'], errors='coerce')
        
        recommendations = []
        expiry_alerts = []
        
        for _, row in df.iterrows():
            current = row['current_stock']
            ideal = row['ideal_stock_level']
            ratio = current / ideal if ideal > 0 else 0
            
            # Determine status and priority
            if ratio <= 0.25:
                status = 'critical_understock'
                priority = 'CRITICAL'
            elif ratio <= 0.75:
                status = 'understock'
                priority = 'HIGH'
            elif ratio <= 1.25:
                status = 'optimal'
                priority = 'LOW'
            else:
                status = 'overstock'
                priority = 'MEDIUM'
            
            # Calculate order quantity
            if ratio < 1:
                order_quantity = int(ideal - current)
            else:
                order_quantity = 0
            
            # Generate AI-enhanced action message
            if status == 'critical_understock':
                action = f"URGENT: Order {order_quantity} units immediately to prevent stockout"
            elif status == 'understock':
                action = f"Order {order_quantity} units to maintain optimal inventory"
            elif status == 'optimal':
                action = "Stock levels are optimal. Monitor regularly."
            else:
                action = f"Consider reducing stock by {int(current - ideal)} units"
            
            # Check expiry date if available
            expiry_date = row.get('expiry_date', None)
            days_left = ''
            if expiry_date:
                try:
                    expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
                    today = datetime.now()
                    days_remaining = (expiry - today).days
                    
                    if days_remaining <= 0:
                        days_left = 'Expired'
                        expiry_alerts.append(row)
                    elif days_remaining <= 30:
                        days_left = str(days_remaining)
                        expiry_alerts.append(row)
                except:
                    pass
            
            recommendations.append({
                'product_id': row['product_id'],
                'product_name': row['product_name'],
                'current_stock': int(current),
                'ideal_stock': int(ideal),
                'stock_ratio': round(ratio, 2),
                'status': status,
                'priority': priority,
                'action': action,
                'order_quantity': order_quantity,
                'expiry_date': expiry_date if expiry_date else '',
                'days_left': days_left
            })
        
        return recommendations, expiry_alerts
        
    except Exception as e:
        print(f"Error in analyze_data_with_ai: {e}")
        return [], []
def get_inventory_alert_email_html(critical, understock, overstock, analysis_time):
    """Generate beautiful HTML for inventory alert emails"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{
          background: #f8fafc;
          font-family: 'Segoe UI', Arial, sans-serif;
          margin: 0;
          padding: 20px;
        }}
        .container {{
          background: #ffffff;
          border-radius: 16px;
          box-shadow: 0 4px 25px rgba(96,130,182,0.15);
          max-width: 600px;
          margin: 0 auto;
          overflow: hidden;
        }}
        .header {{
          text-align: center;
          padding: 30px 20px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }}
        .header h1 {{
          margin: 0;
          font-size: 28px;
          font-weight: 700;
        }}
        .content {{
          padding: 30px;
        }}
        .alert-section {{
          margin: 25px 0;
          border-radius: 12px;
          padding: 20px;
          border-left: 5px solid;
        }}
        .critical {{
          background: #fff5f5;
          border-left-color: #dc3545;
        }}
        .warning {{
          background: #fffbf0;
          border-left-color: #fd7e14;
        }}
        .info {{
          background: #f0f9ff;
          border-left-color: #0ea5e9;
        }}
        .section-title {{
          font-size: 18px;
          font-weight: 600;
          margin-bottom: 15px;
          color: #1f2937;
        }}
        .item {{
          padding: 12px 0;
          border-bottom: 1px solid rgba(0,0,0,0.05);
        }}
        .product-name {{
          font-weight: 600;
          color: #1f2937;
        }}
        .footer {{
          text-align: center;
          padding: 20px;
          background: #f8fafc;
          color: #6b7280;
          font-size: 14px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>📦 InventoryPro Alert</h1>
          <p>Critical stock changes detected</p>
        </div>
        <div class="content">
          {f'''
          <div class="alert-section critical">
            <div class="section-title">🚨 Critical Understock ({len(critical)} items)</div>
            {''.join([f'<div class="item"><div class="product-name">{item["product_name"]}</div><div>{item["action"]}</div></div>' for item in critical])}
          </div>
          ''' if critical else ''}
          
          {f'''
          <div class="alert-section warning">
            <div class="section-title">⚠️ Understock ({len(understock)} items)</div>
            {''.join([f'<div class="item"><div class="product-name">{item["product_name"]}</div><div>Current: <strong>{item["current_stock"]}</strong> | Ideal: <strong>{item["ideal_stock_level"]}</strong></div></div>' for item in understock])}
          </div>
          ''' if understock else ''}
          
          {f'''
          <div class="alert-section info">
            <div class="section-title">📦 Overstock ({len(overstock)} items)</div>
            {''.join([f'<div class="item"><div class="product-name">{item["product_name"]}</div><div>Current: <strong>{item["current_stock"]}</strong> | Ideal: <strong>{item["ideal_stock_level"]}</strong></div></div>' for item in overstock])}
          </div>
          ''' if overstock else ''}
        </div>
        <div class="footer">
          Generated by <strong>InventoryPro</strong> on {analysis_time}
        </div>
      </div>
    </body>
    </html>
    """

def get_expiry_alert_email_html(expiry_items, analysis_time):
    """Generate beautiful HTML for expiry alert emails"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{
          background: #f8fafc;
          font-family: 'Segoe UI', Arial, sans-serif;
          margin: 0;
          padding: 20px;
        }}
        .container {{
          background: #ffffff;
          border-radius: 16px;
          box-shadow: 0 4px 25px rgba(96,130,182,0.15);
          max-width: 600px;
          margin: 0 auto;
          overflow: hidden;
        }}
        .header {{
          text-align: center;
          padding: 30px 20px;
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          color: white;
        }}
        .header h1 {{
          margin: 0;
          font-size: 28px;
          font-weight: 700;
        }}
        .content {{
          padding: 30px;
        }}
        .expiry-item {{
          padding: 20px;
          margin: 15px 0;
          border-radius: 12px;
          border-left: 5px solid;
        }}
        .expired {{
          background: #fef2f2;
          border-left-color: #dc2626;
        }}
        .expiring {{
          background: #fffbeb;
          border-left-color: #f59e0b;
        }}
        .product-name {{
          font-size: 18px;
          font-weight: 600;
          color: #1f2937;
          margin-bottom: 8px;
        }}
        .footer {{
          text-align: center;
          padding: 20px;
          background: #f8fafc;
          color: #6b7280;
          font-size: 14px;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h1>⏰ InventoryPro Expiry Alert</h1>
          <p>Products expiring soon</p>
        </div>
        <div class="content">
          {''.join([
            f'''<div class="expiry-item {'expired' if item['days_left'] == 'Expired' else 'expiring'}">
              <div class="product-name">{item['product_name']}</div>
              <div>Expiry Date: <strong>{item['expiry_date']}</strong></div>
              <div>
                {'<span style="color:#dc2626;font-weight:bold;">EXPIRED</span>' if item['days_left'] == 'Expired' else f'<span style="color:#f59e0b;font-weight:bold;">{item["days_left"]} days remaining</span>'}
              </div>
              <div>Stock: <strong>{item['current_stock']} units</strong></div>
            </div>'''
            for item in expiry_items
          ])}
        </div>
        <div class="footer">
          Generated by <strong>InventoryPro</strong> on {analysis_time}
        </div>
      </div>
    </body>
    </html>
    """

def send_inventory_alert(recommendations, receiver_email):
    try:
        critical = [r for r in recommendations if 'critical' in r['status']]
        understock = [r for r in recommendations if r['status'] == 'understock']
        overstock = [r for r in recommendations if r['status'] == 'overstock']

        if not critical and not understock and not overstock:
            print("No inventory alerts to send.")
            return True

        subject = "🚨 InventoryPro Alert - Critical Stock Changes"
        analysis_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Use the beautiful HTML template
        html_content = get_inventory_alert_email_html(critical, understock, overstock, analysis_time)

        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print(f"✅ Beautiful inventory alert email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending inventory alert email: {e}")
        return False


def send_expiry_alert(expiry_items, receiver_email):
    try:
        if not expiry_items:
            print("No expiry alerts to send.")
            return True
            
        subject = "⏰ InventoryPro Alert - Products Expiring Soon"
        analysis_time = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Use the beautiful HTML template
        html_content = get_expiry_alert_email_html(expiry_items, analysis_time)

        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print(f"✅ Beautiful expiry alert email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending expiry alert email: {e}")
        return False


def create_chart(recommendations):
    try:
        plt.figure(figsize=(12, 6))
        data = recommendations[:8]
        products = [item['product_name'][:12] for item in data]
        current = [item['current_stock'] for item in data]
        ideal = [item.get('ideal_stock_level', item.get('ideal_stock', 0)) for item in data]

        x = range(len(products))
        width = 0.35
        plt.bar([i - width/2 for i in x], current, width, label='Current Stock', color='#FF6B6B', alpha=0.8)
        plt.bar([i + width/2 for i in x], ideal, width, label='Ideal Stock', color='#4ECDC4', alpha=0.8)
        plt.xlabel('Products', fontweight='bold')
        plt.ylabel('Stock Quantity', fontweight='bold')
        plt.title('Current vs Ideal Stock Levels', fontsize=16, fontweight='bold')
        plt.xticks(x, products, rotation=45, ha='right')
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        return f"data:image/png;base64,{image_data}"
    except Exception as e:
        print(f"Chart error: {e}")
        plt.close()
        return None

def analyze_data(df):
    """AI-powered analysis that calculates ideal stock automatically and compares to previous upload."""
    results = []
    expiry_alerts = []
    now = datetime.today().date()

    # Load historical data for comparison
    try:
        with open('inventory_history.json', 'r') as f:
            historical_data = json.load(f)
    except Exception:
        historical_data = []
    is_first_upload = len(historical_data) == 0

    for idx, row in df.iterrows():
        try:
            current_stock = float(row['current_stock'])
            product_id = str(row['product_id'])
            product_name = str(row['product_name'])

            # AI calculates ideal stock based on product type and history
            if is_first_upload:
                name_lower = product_name.lower()
                if any(word in name_lower for word in ['milk', 'bread', 'egg', 'yogurt']):
                    ideal_stock = int(current_stock * 2.0)
                elif any(word in name_lower for word in ['rice', 'oil', 'sugar', 'flour']):
                    ideal_stock = int(current_stock * 1.8)
                elif any(word in name_lower for word in ['fruit', 'vegetable', 'meat', 'fish', 'cheese']):
                    ideal_stock = int(current_stock * 1.3)
                else:
                    ideal_stock = int(current_stock * 1.5)
                trend = "New Product"
            else:
                prev_history = [rec for rec in historical_data if rec['product_id'] == product_id]
                if prev_history:
                    avg_stock = sum([rec['current_stock'] for rec in prev_history]) / len(prev_history)
                    recent_stocks = [rec['current_stock'] for rec in prev_history[-3:]]
                    older_stocks = [rec['current_stock'] for rec in prev_history[:-3]]
                    recent_avg = sum(recent_stocks) / len(recent_stocks) if recent_stocks else avg_stock
                    older_avg = sum(older_stocks) / len(older_stocks) if older_stocks else avg_stock
                    if recent_avg > older_avg * 1.1:
                        ideal_stock = int(avg_stock * 1.4)
                        trend = "Growing ↗"
                    elif recent_avg < older_avg * 0.9:
                        ideal_stock = int(avg_stock * 1.1)
                        trend = "Declining ↘"
                    else:
                        ideal_stock = int(avg_stock * 1.2)
                        trend = "Stable →"
                else:
                    name_lower = product_name.lower()
                    if any(word in name_lower for word in ['milk', 'bread', 'egg', 'yogurt']):
                        ideal_stock = int(current_stock * 2.0)
                    elif any(word in name_lower for word in ['rice', 'oil', 'sugar', 'flour']):
                        ideal_stock = int(current_stock * 1.8)
                    elif any(word in name_lower for word in ['fruit', 'vegetable', 'meat', 'fish', 'cheese']):
                        ideal_stock = int(current_stock * 1.3)
                    else:
                        ideal_stock = int(current_stock * 1.5)
                    trend = "New Product"

            # Calculate status
            ratio = current_stock / ideal_stock if ideal_stock > 0 else 0
            if ratio < 0.3:
                status = "critical_understock"
                priority = "CRITICAL"
                action = f"URGENT: Order {int(ideal_stock - current_stock)} units now"
            elif ratio < 0.7:
                status = "understock"
                priority = "HIGH"
                action = f"Reorder {int(ideal_stock - current_stock)} units soon"
            elif ratio > 2.0:
                status = "critical_overstock"
                priority = "CRITICAL"
                action = f"Reduce {int(current_stock - ideal_stock)} units"
            elif ratio > 1.3:
                status = "overstock"
                priority = "MEDIUM"
                action = f"Consider reducing {int(current_stock - ideal_stock)} units"
            else:
                status = "optimal"
                priority = "LOW"
                action = "Stock level is good"

            # Handle expiry dates
            expiry_date_str = ""
            days_left_text = ""
            for col in ['expiry_date', 'Expiry', 'expiry']:
                if col in df.columns and pd.notnull(row[col]):
                    expiry_date_str = str(row[col]).strip()
                    break

            expiry_obj = None
            if expiry_date_str:
                try:
                    expiry_obj = datetime.strptime(expiry_date_str, '%d-%m-%Y').date()
                except:
                    try:
                        expiry_obj = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    except:
                        expiry_obj = None
                if expiry_obj:
                    delta = (expiry_obj - now).days
                    if delta >= 0:
                        days_left_text = str(delta)
                        if delta <= 7:
                            expiry_alerts.append({
                                'product_id': product_id,
                                'product_name': product_name,
                                'current_stock': int(current_stock),
                                'expiry_date': expiry_obj.strftime('%Y-%m-%d'),
                                'days_left': days_left_text
                            })
                    else:
                        days_left_text = "Expired"

            results.append({
                'product_id': product_id,
                'product_name': product_name,
                'current_stock': int(current_stock),
                'ideal_stock_level': int(ideal_stock),
                'status': status,
                'priority': priority,
                'action': action,
                'expiry_date': expiry_obj.strftime('%Y-%m-%d') if expiry_obj else '',
                'days_left': days_left_text,
                'trend': trend
            })
        except Exception as e:
            print(f"Error processing row {idx}: {e}")

        # Save current data for next comparison
        try:
            historical_data.append({
                'product_id': product_id,
                'product_name': product_name,
                'current_stock': current_stock,
                'upload_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            # Keep last 100 records
            if len(historical_data) > 100:
                historical_data = historical_data[-100:]
            with open('inventory_history.json', 'w') as f:
                json.dump(historical_data, f)
        except Exception as e:
            print(f"Error saving history: {e}")

    return results, expiry_alerts

def get_all_analyses():
    """Get list of all previous analyses"""
    try:
        results_folder = app.config['RESULTS_FOLDER']
        if not os.path.exists(results_folder):
            return []
            
        files = [f for f in os.listdir(results_folder) if f.startswith('results_') and f.endswith('.json')]
        files.sort(reverse=True)  # Latest first
        
        analyses = []
        for filename in files:
            try:
                filepath = os.path.join(results_folder, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)

                timestamp = filename.split('_')[1].split('.')[0]
                readable_date = datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                
                analyses.append({
                    'filename': filename,
                    'timestamp': readable_date,
                    'total_products': len(data.get('recommendations', [])),
                    'critical_count': len([r for r in data.get('recommendations', []) if 'critical' in r.get('status', '')]),
                    'source_file': data.get('filename', 'Unknown')
                })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                
        return analyses
    except Exception as e:
        print(f"Error getting analyses: {e}")
        return []

@app.route('/previous-analyses')
def previous_analyses():
    """Show list of all previous analyses"""
    analyses = get_all_analyses()
    return render_template('previous_analyses.html', analyses=analyses)

@app.route('/previous-analyses/<filename>')
def view_previous_analysis(filename):
    """View specific previous analysis"""
    try:
        filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            return render_template('results.html', result=data, is_previous=True)
        else:
            flash('Analysis not found!', 'error')
            return redirect(url_for('previous_analyses'))
    except Exception as e:
        flash(f'Error loading analysis: {str(e)}', 'error')
        return redirect(url_for('previous_analyses'))
@app.route('/delete-analysis/<filename>', methods=['POST'])
def delete_analysis(filename):
    """Delete a specific analysis file"""
    try:
        filepath = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            flash('✅ Analysis deleted successfully!', 'success')
        else:
            flash('❌ Analysis file not found!', 'error')
    except Exception as e:
        flash(f'❌ Error deleting analysis: {str(e)}', 'error')
    
    return redirect(url_for('previous_analyses'))

@app.route('/clear-all-analyses', methods=['POST'])
def clear_all_analyses():
    """Delete all analysis files"""
    try:
        results_folder = app.config['RESULTS_FOLDER']
        if os.path.exists(results_folder):
            files = [f for f in os.listdir(results_folder) if f.startswith('results_') and f.endswith('.json')]
            for file in files:
                os.remove(os.path.join(results_folder, file))
            
            # Also clear latest_results.txt
            if os.path.exists('latest_results.txt'):
                os.remove('latest_results.txt')
                
            flash(f'✅ All {len(files)} analyses cleared successfully!', 'success')
        else:
            flash('❌ No analyses found to clear!', 'info')
    except Exception as e:
        flash(f'❌ Error clearing analyses: {str(e)}', 'error')
    
    return redirect(url_for('previous_analyses'))

@app.route('/')
def index():
    email = get_receiver_email()
    return render_template('index.html', receiver_email=email)

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form = FileUploadForm()
    if form.validate_on_submit():
        try:
            file = form.file.data
            filename = secure_filename(file.filename)
            timestamp = int(time.time())
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
            file.save(filepath)
            
            # Check for duplicate files
            file_hash = calculate_file_hash(filepath)
            if is_duplicate_file(file_hash):
                os.remove(filepath)
                flash('⚠️ This file has already been uploaded! Showing previous analysis.', 'warning')
                return redirect(url_for('results'))
            
            # Save file hash to prevent future duplicates
            save_file_hash(file_hash, filename, timestamp)
            
            df = pd.read_csv(filepath)
            
            # Use AI-enhanced analysis
            recommendations, expiry_alerts = analyze_data(df)


            chart = create_chart(recommendations)
            
            summary = {
                'total_products': len(recommendations),
                'critical_count': len([r for r in recommendations if 'critical' in r['status']]),
                'understock_count': len([r for r in recommendations if r['status'] == 'understock']),
                'overstock_count': len([r for r in recommendations if r['status'] == 'overstock']),
                'optimal_count': len([r for r in recommendations if r['status'] == 'optimal'])
            }
            
            results = {
                'recommendations': recommendations,
                'chart': chart,
                'summary': summary,
                'filename': filename,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Save the results
            save_results(results)
            
            # Send email notifications if configured
            receiver_email = get_receiver_email()
            if receiver_email:
                send_email_async(send_inventory_alert, recommendations, receiver_email)
                if expiry_alerts:
                    send_email_async(send_expiry_alert, expiry_alerts, receiver_email)
                flash('🤖 AI Analysis complete! Email alert sent.', 'success')
            else:
                flash('🤖 AI Analysis complete! Configure email to receive alerts.', 'info')
            
            # Clean up and redirect
            os.remove(filepath)
            return redirect(url_for('results'))
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
    
    return render_template('upload.html', form=form, history=load_history())


@app.route('/results')
def results():
    result_data = load_results()
    if not result_data:
        flash("No results!", "danger")
        return redirect(url_for('index'))
    return render_template('results.html', result=result_data)

@app.route('/sample-data')
def use_sample_data():
    try:
        sample_df = pd.DataFrame([
            {'product_id': 'P001', 'product_name': 'Fresh Apples', 'current_stock': 45, 'ideal_stock_level': 100, 'expiry_date': '21-08-2025'},
            {'product_id': 'P002', 'product_name': 'Bananas', 'current_stock': 180, 'ideal_stock_level': 120, 'expiry_date': '21-08-2025'}
        ])
        recommendations, expiry_alerts = analyze_data(sample_df)

        chart = create_chart(recommendations)
        summary = {
            'total_products': len(recommendations),
            'critical_count': len([r for r in recommendations if 'critical' in r['status']]),
            'understock_count': len([r for r in recommendations if r['status'] == 'understock']),
            'overstock_count': len([r for r in recommendations if r['status'] == 'overstock']),
            'optimal_count': len([r for r in recommendations if r['status'] == 'optimal'])
        }
        results = {
            'recommendations': recommendations,
            'chart': chart,
            'summary': summary,
            'filename': 'sample_data.csv',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        save_results(results)
        receiver_email = get_receiver_email()
        if receiver_email:
            send_email_async(send_inventory_alert, recommendations, receiver_email)
            if expiry_alerts:
                send_email_async(send_expiry_alert, expiry_alerts, receiver_email)
            flash('Sample data analyzed! Email alert sent.', 'success')
        else:
            flash('Sample data analyzed! Configure email to receive alerts.', 'info')
        return redirect(url_for('results'))
    except Exception as e:
        flash(f'Sample data error: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/set-email', methods=['GET', 'POST'])
def set_email():
    form = EmailForm()
    if form.validate_on_submit():
        with open('receiver_email.txt', 'w') as f:
            f.write(form.email.data)
        flash('Email saved!', 'success')
        return redirect(url_for('index'))
    current_email = get_receiver_email()
    if current_email and not form.email.data:
        form.email.data = current_email
    return render_template('set_email.html', form=form)

@app.route('/test-email')
def test_email():
    receiver_email = get_receiver_email()
    if not receiver_email:
        flash('Configure receiver email first!', 'warning')
        return redirect(url_for('set_email'))
    test_recommendations = [
        {
            'product_name': 'Test Product',
            'current_stock': 10,
            'ideal_stock_level': 100,
            'status': 'critical_understock',
            'action': 'URGENT: Order 90 units now'
        }
    ]
    success = send_inventory_alert(test_recommendations, receiver_email)
    if success:
        flash(f'Test email sent successfully to {receiver_email}!', 'success')
    else:
        flash('Failed to send test email. Check email configuration.', 'error')
    return redirect(url_for('index'))

@app.route('/clear-session')
def clear_session():
    session.clear()
    flash('Session cleared!', 'info')
    return redirect(url_for('index'))

@app.route('/clear-results')
def clear_results():
    try:
        if os.path.exists('latest_results.txt'):
            os.remove('latest_results.txt')
        flash('Results cleared!', 'info')
    except Exception:
        pass
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
