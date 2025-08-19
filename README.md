# InventoryPro - AI Inventory Management System

A smart Flask-based inventory management system that analyzes stock levels, predicts optimal inventory, and sends email alerts.

![Dashboard Preview](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey)

## Features

- **AI Stock Analysis** - Automatically calculates ideal stock levels
- **Visual Dashboard** - Interactive charts and summary cards
- **Email Alerts** - Beautiful HTML email notifications
- **Historical Data** - Track inventory trends over time
- **Mobile Responsive** - Works on all devices

## Quick Start

### 1. Install Requirements

### 2. Configure Email (Optional)
In `app.py`, update these settings:
SENDER_EMAIL = "your-email@gmail.com"
SENDER_PASSWORD = "your-gmail-app-password"

### 3. Run Application
python app.py

### 4. Open Browser
Go to `http://localhost:5000`

## How to Use

### Step 1: Prepare CSV File
Create a CSV file with these columns:
product_id,product_name,current_stock,expiry_date
P001,Organic Rice 5kg,120,2025-08-20
P002,Olive Oil 1L,30,2025-08-18
P003,Cheese 200g,15,2025-08-21

### Step 2: Upload and Analyze
1. Click **"Upload Data"**
2. Select your CSV file
3. Click **"Upload and Analyze"**
4. View AI analysis results

### Step 3: Configure Email Alerts
1. Click **"Email Settings"**
2. Enter your email address
3. Save configuration
4. Receive automatic alerts for critical items

## Understanding Results

### Dashboard Cards
- **Blue Card** - Total items analyzed
- **Red Card** - Critical items needing immediate attention
- **Yellow Card** - Items that need restocking
- **Cyan Card** - Overstocked items

### Chart
- **Red Bars** - Current stock levels
- **Teal Bars** - AI-recommended ideal stock levels

### Table Columns
- **Status** - Critical Understock, Understock, Optimal, Overstock
- **Priority** - CRITICAL, HIGH, MEDIUM, LOW
- **Action** - AI recommendations for each product
- **Expiry** - Days until expiration

### Status Meanings
- 🔴 **Critical Understock** - Order immediately
- 🟡 **Understock** - Reorder soon
- 🟢 **Optimal** - Stock level is good
- 🔵 **Overstock** - Consider reducing

## Features Explained

### AI Analysis
The system automatically:
- Calculates ideal stock levels based on product type
- Considers historical trends
- Provides specific recommendations
- Tracks inventory patterns over time

### Email System
- Sends beautiful HTML email alerts
- Two types: Inventory alerts and Expiry alerts
- Automatic alerts when uploading new data
- Manual alerts from "Previous Predictions" page

### Navigation Menu
- **Dashboard** - Main overview page
- **Upload Data** - Upload CSV files for analysis
- **Sample Data** - Try with sample data
- **Email Settings** - Configure alert recipients
- **Analysis** - View latest analysis results
- **Previous Predictions** - Browse historical data

## Gmail Email Setup

### Get Gmail App Password
1. Enable 2-factor authentication on your Gmail account
2. Go to Google Account Settings → Security
3. Under "2-Step Verification", click "App passwords"
4. Select "Mail" and generate a new password
5. Use this password in your configuration (not your regular Gmail password)

### Update Configuration
SENDER_EMAIL = "youremail@gmail.com"
SENDER_PASSWORD = "your-16-digit-app-password"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


## File Structure
InventoryPro/

│

├── 📄 app.py Main Flask application

│

├── 📁 templates/ HTML template files

│ ├── 🏠 index.html Dashboard homepage

│ ├── 📤 upload.html File upload page

│ ├── 📊 results.html Analysis results

│ ├── 📚 previous_analyses.html Historical data

│ └── ⚙️ set_email.html Email settings

│

├── 📁 static/ Static files

│ ├── 📂 uploads/ Temporary storage

│ └── 📂 results/ Analysis data

│

├── 📝 README.md Documentation

├── 📋 requirements.txt Dependencies

└── ⚙️ .env Configuration


## Advanced Features

### Previous Predictions
- Browse all historical analyses
- Compare trends over time
- Manual alert triggers
- Delete old analyses

### Sample Data
- Test the system with sample data
- No file upload required
- Instant analysis results

### Data Validation
- Automatic CSV format checking
- Duplicate file detection
- Error handling and user feedback

## Troubleshooting

### Common Issues

**Email not sending:**
- Verify Gmail App Password is correct
- Check 2-factor authentication is enabled
- Ensure SMTP settings are accurate

**CSV upload fails:**
- Check file format matches required columns
- Verify date format is DD-MM-YYYY or YYYY-MM-DD
- Ensure file is not corrupted

**Charts not displaying:**
- Clear browser cache
- Check matplotlib installation
- Verify file permissions

### Error Messages
- **"No results found"** - Upload a CSV file first
- **"Email not configured"** - Set up email in Email Settings
- **"Invalid CSV format"** - Check your CSV file structure

## System Requirements
- Python 3.7 or higher
- 512MB RAM minimum
- 100MB disk space
- Internet connection (for email alerts)
- Modern web browser

## CSV File Requirements

### Required Columns
- `product_id` - Unique identifier (e.g., P001, P002)
- `product_name` - Product name (e.g., "Organic Rice 5kg")
- `current_stock` - Current quantity (numeric)
- `expiry_date` - Expiration date (DD-MM-YYYY or YYYY-MM-DD)

### Optional Enhancements
You can add more columns, but these four are required for basic functionality.

## AI Logic Explanation

The AI calculates ideal stock levels using these multipliers:
- **Fast-moving items** (milk, bread, eggs): 2.0x current stock
- **Staple items** (rice, oil, flour): 1.8x current stock
- **Perishables** (fruits, vegetables, cheese): 1.3x current stock
- **Default items**: 1.5x current stock

## License
This project is open source and available under the MIT License.

## Support
For questions or issues, please check the troubleshooting section above or create an issue in the project repository.

---

**Made with ❤️ for better inventory management**

*Star this project if you find it helpful!*


