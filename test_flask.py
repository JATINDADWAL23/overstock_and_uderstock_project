from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>🎉 Flask is Working!</h1>
        <p>If you see this, Flask is running correctly.</p>
        <hr>
        <p>Current time: <script>document.write(new Date());</script></p>
    </body>
    </html>
    """

@app.route('/test')
def test():
    return {"status": "OK", "message": "Flask server is running"}

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Starting Flask Server...")
    print("📍 Open your browser and go to:")
    print("   http://127.0.0.1:5000")
    print("   http://localhost:5000")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        print(f"❌ Error starting Flask: {e}")
        input("Press Enter to exit...")
