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

def send_inventory_alert(recommendations, receiver_email):
    try:
        critical = [r for r in recommendations if 'critical' in r['status']]
        understock = [r for r in recommendations if r['status'] == 'understock']
        overstock = [r for r in recommendations if r['status'] == 'overstock']

        if not critical and not understock and not overstock:
            print("No inventory alerts to send.")
            return True

        subject = "Inventory Alert - Critical Stock Levels"
        html = f"""<h2>Inventory Alert</h2>
        <p>Critical stock issues detected:</p>
        <h3>Critical ({len(critical)})</h3><ul>"""
        for item in critical:
            html += f"<li><b>{item['product_name']}</b>: {item['action']}</li>"
        html += "</ul>"

        if understock:
            html += f"<h3>Understock ({len(understock)})</h3><ul>"
            for item in understock:
                html += f"<li>{item['product_name']}: Current {item['current_stock']}, Ideal {item['ideal_stock_level']}</li>"
            html += "</ul>"

        if overstock:
            html += f"<h3>Overstock ({len(overstock)})</h3><ul>"
            for item in overstock:
                html += f"<li>{item['product_name']}: Current {item['current_stock']}, Ideal {item['ideal_stock_level']}</li>"
            html += "</ul>"

        html += f"<p>Report generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>"

        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print(f"Inventory alert email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Error sending inventory alert email: {e}")
        return False

def send_expiry_alert(expiry_items, receiver_email):
    try:
        if not expiry_items:
            print("No expiry alerts to send.")
            return True
        subject = "Expiry Alert - Products Expiring Soon"
        html = "<h2>Expiry Alert</h2><p>The following products expire within 7 days:</p><ul>"
        for item in expiry_items:
            html += f"<li><b>{item['product_name']}</b>: Expiry {item['expiry_date']} ({item['days_left']} days left), Stock: {item['current_stock']}</li>"
        html += "</ul>"
        html += f"<p>Report generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>"

        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print(f"Expiry alert email sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Error sending expiry alert email: {e}")
        return False

def create_chart(recommendations):
    try:
        plt.figure(figsize=(12, 6))
        data = recommendations[:8]
        products = [item['product_name'][:12] for item in data]
        current = [item['current_stock'] for item in data]
        ideal = [item['ideal_stock_level'] for item in data]

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
    results = []
    expiry_alerts = []
    now = datetime.today().date()

    for idx, row in df.iterrows():
        try:
            current = float(row['current_stock'])
            ideal = float(row['ideal_stock_level'])
            ratio = current / ideal if ideal > 0 else 0

            expiry_date_str = ""
            expiry_date = None
            days_left = None

            for col in ['expiry_date', 'Expiry', 'expiry']:
                if col in df.columns and pd.notnull(row[col]):
                    expiry_date_str = str(row[col]).strip()
                    break

            if expiry_date_str:
                try:
                    expiry_date = datetime.strptime(expiry_date_str, '%d-%m-%Y').date()
                except:
                    try:
                        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    except:
                        expiry_date = None

            days_left_text = ''
            if expiry_date:
                delta = (expiry_date - now).days
                if delta >= 0:
                    days_left_text = str(delta)
                    if delta <= 7:
                        expiry_alerts.append({
                            'product_id': row['product_id'],
                            'product_name': row['product_name'],
                            'current_stock': int(current),
                            'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                            'days_left': days_left_text
                        })
                else:
                    days_left_text = "Expired"

            if ratio < 0.4:
                status = "critical_understock"
                priority = "CRITICAL"
                action = f"URGENT: Order {int(ideal - current)} units now"
            elif ratio < 0.7:
                status = "understock"
                priority = "HIGH"
                action = f"Reorder {int(ideal - current)} units soon"
            elif ratio > 2.0:
                status = "critical_overstock"
                priority = "CRITICAL"
                action = f"Reduce {int(current - ideal)} units"
            elif ratio > 1.3:
                status = "overstock"
                priority = "MEDIUM"
                action = f"Consider reducing {int(current - ideal)} units"
            else:
                status = "optimal"
                priority = "LOW"
                action = "Stock level is good"

            results.append({
                'product_id': str(row['product_id']),
                'product_name': str(row['product_name']),
                'current_stock': int(current),
                'ideal_stock_level': int(ideal),
                'status': status,
                'priority': priority,
                'action': action,
                'expiry_date': expiry_date.strftime('%Y-%m-%d') if expiry_date else '',
                'days_left': days_left_text
            })
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
    return results, expiry_alerts

def save_results(results):
    timestamp = str(int(time.time()))
    filepath = os.path.join(app.config['RESULTS_FOLDER'], f'analysis_{timestamp}.json')
    with open(filepath, 'w') as f:
        json.dump(results, f)
    with open('latest_results.txt', 'w') as f:
        f.write(timestamp)
    return timestamp

def load_results():
    try:
        with open('latest_results.txt', 'r') as f:
            timestamp = f.read().strip()
        filepath = os.path.join(app.config['RESULTS_FOLDER'], f'analysis_{timestamp}.json')
        with open(filepath, 'r') as f:
            return json.load(f)
    except:
        return None

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

            df = pd.read_csv(filepath)
            recommendations, expiry_alerts = analyze_data(df)
            chart = create_chart(recommendations)
            
            # Add to upload history
            add_upload_history(filename, len(recommendations), time.strftime('%Y-%m-%d %H:%M:%S'))
            
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

            save_results(results)
            receiver_email = get_receiver_email()
            if receiver_email:
                send_email_async(send_inventory_alert, recommendations, receiver_email)
                if expiry_alerts:
                    send_email_async(send_expiry_alert, expiry_alerts, receiver_email)
                flash('Analysis complete! Email alert sent.', 'success')
            else:
                flash('Analysis complete! Configure email to receive alerts.', 'info')
            os.remove(filepath)
            return redirect(url_for('results'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
    return render_template('upload.html', form=form)
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
