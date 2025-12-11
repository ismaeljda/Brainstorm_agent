from http.server import SimpleHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
import os

# Load .env for frontend access
load_dotenv()

class MyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == '__main__':
    print(f"🌐 Frontend server starting on http://localhost:8000")
    print(f"🔑 ANAM API Key: {os.getenv('ANAM_API_KEY')[:20]}...")
    server = HTTPServer(('localhost', 8000), MyHandler)
    server.serve_forever()
