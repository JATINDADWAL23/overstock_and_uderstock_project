from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, IntegerField, TextAreaField, PasswordField
from wtforms.validators import DataRequired, Email
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, io, uuid, base64, time
from werkzeug.utils import secure_filename
from threading import Thread
from inventory_system import InventoryManagementSystem, EmailNotificationSystem
from email_validator import validate_email, EmailNotValidError


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['TESTING'] = False
app.config['MAIL_SUPPRESS_SEND'] = False


# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)


# Global variables
analysis_results = {}


email_config = {}


# Helper functions for receiver email
def set_receiver(address):
    global email_config
    email_config['recipient_emails'] = address
    email_config['configured'] = True


def get_receiver():
    return email_config.get('recipient_emails', '')


# Forms
class EmailConfigForm(FlaskForm):
    smtp_server = StringField('SMTP Server', validators=[DataRequired()], default='smtp.gmail.com')
    smtp_port = IntegerField('SMTP Port', validators=[DataRequired()], default=587)
    sender_email = StringField('Sender Email', validators=[DataRequired(), Email()])
    sender_password = PasswordField('Sender Password', validators=[DataRequired()])
    recipient_emails = TextAreaField('Recipient Emails', validators=[DataRequired()])


class FileUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[FileRequired(), FileAllowed(['csv'])])


def create_simple_chart(data):
    try:
        plt.figure(figsize=(10, 6))
        products = [x['product_name'][:15] for x in data]
        current = [x['current_stock'] for x in data]
        ideal = [x['ideal_stock_level'] for x in data]
        
        x = range(len(products))
        plt.bar([i-0.2 for i in x], current, 0.4, label='Current', color='#3b82f6', alpha=0.8)
        plt.bar([i+0.2 for i in x], ideal, 0.4, label='Ideal', color='#10b981', alpha=0.8)
        
        plt.xlabel('Products')
        plt.ylabel('Stock Quantity')
        plt.title('Current vs Ideal Stock Levels')
        plt.xticks(x, products, rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
        img_buffer.seek(0)
        img_data = base64.b64encode(img_buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{img_data}"
    except Exception as e:
        plt.close()
        return None


def process_analysis_async(data, session_id):
    try:
        print(f"🔄 Starting analysis for session {session_id}")
        ims = InventoryManagementSystem()
        
        # Run analysis
        forecasts, recommendations, alerts = ims.run_analysis(data)
        
        # Convert to list for templates
        recs_list = [recommendations[k] for k in recommendations]
        
        # Create simple chart
        chart = create_simple_chart(recs_list) if recs_list else None
        
        analysis_results[session_id] = {
            'status': 'completed',
            'recommendations_list': recs_list,
            'alerts': alerts,
            'charts': {'stock_comparison': chart} if chart else {}
        }
        
        print(f"✅ Analysis completed for session {session_id}")
        
        # Send email alerts if configured
        if email_config.get('configured', False) and recommendations:
            try:
                print("📧 Email is configured - attempting to send alerts...")
                email_system = EmailNotificationSystem()
                recipients = [x.strip() for x in email_config['recipient_emails'].split(',') if x.strip()]
                
                print(f"📧 Email config: {email_config['smtp_server']}:{email_config['smtp_port']}")
                print(f"📧 From: {email_config['sender_email']}")
                print(f"📧 To: {recipients}")
                
                email_system.configure_email(
                    email_config['smtp_server'], 
                    email_config['smtp_port'],
                    email_config['sender_email'], 
                    email_config['sender_password'], 
                    recipients
                )
                
                ims.alert_system.enable_email_notifications(email_system)
                ims.alert_system.send_bulk_alerts(recommendations)
                print("📧 Email alerts processing completed")
                
            except Exception as e:
                print(f"❌ Email sending failed: {e}")
        else:
            print("⚠️ Email not configured - skipping email alerts")
                
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        analysis_results[session_id] = {
            'status': 'error',
            'error': str(e)
        }


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route("/set-email", methods=["GET", "POST"])
def set_email():
    if request.method == "POST":
        raw = request.form.get("email", "").strip()
        try:
            address = validate_email(raw, check_deliverability=True).email
        except EmailNotValidError as err:
            flash(f"Invalid address – {err}", "danger")
            # Render template directly so error shows immediately (not after redirect)
            return render_template("set_email.html", receiver=raw)
        set_receiver(address)
        flash(f"Receiver e-mail “{address}” saved!", "success")
        return redirect(url_for("index"))
    return render_template("set_email.html", receiver=get_receiver())



@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form = FileUploadForm()
    if form.validate_on_submit():
        try:
            filename = secure_filename(form.file.data.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{int(time.time())}_{filename}")
            form.file.data.save(filepath)
            
            data = pd.read_csv(filepath)
            required_cols = ['product_id', 'product_name', 'current_stock', 'ideal_stock_level', 'status']
            
            for col in required_cols:
                if col not in data.columns:
                    flash(f'Missing required column: {col}', 'error')
                    return render_template('upload.html', form=form)
            
            session['uploaded_file'] = filepath
            session['data_preview'] = data.head().to_html(classes='table table-striped table-sm')
            flash(f'Successfully loaded {len(data)} products!', 'success')
            return redirect(url_for('analyze'))
        except Exception as e:
            flash(f'Error loading file: {str(e)}', 'error')
    
    return render_template('upload.html', form=form)


@app.route('/sample-data')
def use_sample_data():
    try:
        ims = InventoryManagementSystem()
        data = ims.create_sample_data()
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f'sample_{int(time.time())}.csv')
        data.to_csv(filepath, index=False)
        session['uploaded_file'] = filepath
        session['data_preview'] = data.to_html(classes='table table-striped table-sm')
        flash('Sample data loaded successfully!', 'success')
        return redirect(url_for('analyze'))
    except Exception as e:
        flash(f'Error loading sample data: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/analyze')
def analyze():
    if 'uploaded_file' not in session:
        flash('Please upload data first', 'warning')
        return redirect(url_for('upload_file'))
    
    try:
        data = pd.read_csv(session['uploaded_file'])
        session_id = str(uuid.uuid4())
        session['analysis_id'] = session_id
        
        analysis_results[session_id] = {'status': 'processing'}
        thread = Thread(target=process_analysis_async, args=(data, session_id))
        thread.daemon = True
        thread.start()
        
        return render_template('analysis.html', 
                              data_preview=session.get('data_preview', ''),
                              session_id=session_id)
    except Exception as e:
        flash(f'Analysis error: {str(e)}', 'error')
        return redirect(url_for('upload_file'))


@app.route('/analysis-status/<session_id>')
def analysis_status(session_id):
    result = analysis_results.get(session_id, {'status': 'not_found'})
    return jsonify(result)


@app.route('/results')
def results():
    session_id = session.get('analysis_id')
    if not session_id or session_id not in analysis_results:
        flash('No analysis results found', 'warning')
        return redirect(url_for('index'))
    
    result = analysis_results[session_id]
    if result['status'] != 'completed':
        flash('Analysis not completed yet', 'info')
        return redirect(url_for('analyze'))
    
    return render_template('results.html', result=result)


@app.route('/email-config', methods=['GET', 'POST'])
def email_config_page():
    form = EmailConfigForm()
    if form.validate_on_submit():
        global email_config
        email_config = {
            'smtp_server': form.smtp_server.data,
            'smtp_port': form.smtp_port.data,
            'sender_email': form.sender_email.data,
            'sender_password': form.sender_password.data,
            'recipient_emails': form.recipient_emails.data,
            'configured': True
        }
        flash('Email configuration saved successfully!', 'success')
        return redirect(url_for('email_config_page'))
    
    # Pre-populate form
    if email_config.get('configured', False):
        form.smtp_server.data = email_config['smtp_server']
        form.smtp_port.data = email_config['smtp_port'] 
        form.sender_email.data = email_config['sender_email']
        form.recipient_emails.data = email_config['recipient_emails']
    
    return render_template('email_config.html', form=form, configured=email_config.get('configured', False))


@app.route('/test-email')
def test_email():
    if not email_config.get('configured', False):
        return jsonify({'success': False, 'message': 'Email not configured. Please configure email settings first.'})
    
    try:
        print("🧪 Testing email configuration...")
        email_system = EmailNotificationSystem()
        recipients = [x.strip() for x in email_config['recipient_emails'].split(',') if x.strip()]
        
        print(f"📧 Test email config:")
        print(f"   Server: {email_config['smtp_server']}:{email_config['smtp_port']}")
        print(f"   From: {email_config['sender_email']}")
        print(f"   To: {recipients}")
        
        email_system.configure_email(
            email_config['smtp_server'], 
            email_config['smtp_port'],
            email_config['sender_email'], 
            email_config['sender_password'], 
            recipients
        )
        
        test_data = [{
            'product_id': 'TEST001',
            'product_name': 'Test Product for Email Verification',
            'current_stock': 10,
            'ideal_stock_level': 50,
            'stock_ratio': 0.2,
            'action': 'This is a test email from your Flask Inventory Management System',
            'order_quantity': 40
        }]
        
        success, message = email_system.send_stock_alert('critical', test_data)
        
        if success:
            print("✅ Test email sent successfully!")
        else:
            print(f"❌ Test email failed: {message}")
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        error_msg = f"Test email failed: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({'success': False, 'message': error_msg})


@app.route('/export-results/<session_id>')
def export_results(session_id):
    if session_id not in analysis_results:
        flash('No results to export', 'error')
        return redirect(url_for('index'))
    
    result = analysis_results[session_id]
    if result['status'] != 'completed':
        flash('Analysis not completed', 'error') 
        return redirect(url_for('index'))
    
    try:
        df = pd.DataFrame(result['recommendations_list'])
        filename = f'inventory_analysis_{int(time.time())}.csv'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_csv(filepath, index=False)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f'Export error: {str(e)}', 'error')
        return redirect(url_for('results'))


# Debug route for email testing
@app.route('/debug-email')
def debug_email():
    if not email_config.get('configured', False):
        return """
        <h2>❌ Email Not Configured</h2>
        <p>Please configure your email settings first:</p>
        <a href="/email-config">Configure Email Settings</a>
        """
    
    try:
        print("🔧 EMAIL DEBUG MODE")
        print("=" * 50)
        
        email_system = EmailNotificationSystem()
        recipients = [x.strip() for x in email_config['recipient_emails'].split(',') if x.strip()]
        
        print(f"📧 SMTP Server: {email_config['smtp_server']}")
        print(f"📧 SMTP Port: {email_config['smtp_port']}")
        print(f"📧 Sender Email: {email_config['sender_email']}")
        print(f"📧 Recipients: {recipients}")
        print(f"📧 Password Length: {len(email_config['sender_password'])} characters")
        
        email_system.configure_email(
            email_config['smtp_server'], 
            email_config['smtp_port'],
            email_config['sender_email'], 
            email_config['sender_password'], 
            recipients
        )
        
        test_data = [{
            'product_id': 'DEBUG001',
            'product_name': 'Debug Test Product',
            'current_stock': 5,
            'ideal_stock_level': 100,
            'stock_ratio': 0.05,
            'action': 'DEBUG: This is a test email with detailed logging',
            'order_quantity': 95
        }]
        
        print("\n🚀 Attempting to send test email...")
        success, message = email_system.send_stock_alert('critical', test_data)
        
        result_html = f"""
        <html>
        <head><title>Email Debug Results</title></head>
        <body style="font-family: Arial; padding: 20px;">
            <h2>📧 Email Debug Results</h2>
            <div style="background: {'#d4edda' if success else '#f8d7da'}; padding: 15px; border-radius: 5px; margin: 10px 0;">
                <h3>{'✅ SUCCESS' if success else '❌ FAILED'}</h3>
                <p><strong>Message:</strong> {message}</p>
            </div>
            
            <h3>Configuration Details:</h3>
            <ul>
                <li><strong>SMTP Server:</strong> {email_config['smtp_server']}</li>
                <li><strong>SMTP Port:</strong> {email_config['smtp_port']}</li>
                <li><strong>Sender Email:</strong> {email_config['sender_email']}</li>
                <li><strong>Recipients:</strong> {', '.join(recipients)}</li>
                <li><strong>Password Length:</strong> {len(email_config['sender_password'])} characters</li>
            </ul>
            
            <h3>Troubleshooting Tips:</h3>
            <ul>
                <li>For Gmail: Use App Password (not regular password)</li>
                <li>Enable 2-Factor Authentication on Gmail</li>
                <li>Check that recipient emails are valid</li>
                <li>Verify network/firewall settings</li>
            </ul>
            
            <p><a href="/email-config">← Back to Email Configuration</a></p>
        </body>
        </html>
        """
        
        return result_html
        
    except Exception as e:
        error_html = f"""
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h2>❌ Email Debug Error</h2>
            <div style="background: #f8d7da; padding: 15px; border-radius: 5px;">
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
            <p><a href="/email-config">← Back to Email Configuration</a></p>
        </body>
        </html>
        """
        return error_html


if __name__ == '__main__':
    print("🚀 Starting Inventory Management System...")
    print("📍 Main Dashboard: http://127.0.0.1:5000")
    print("📍 Email Debug: http://127.0.0.1:5000/debug-email")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
