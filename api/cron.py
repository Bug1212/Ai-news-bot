"""
Vercel serverless function — called by the cron job every 6 hours.
GET /api/cron  → runs the bot and returns a status JSON.
"""
from http.server import BaseHTTPRequestHandler
import asyncio
import json
import sys
import os

# Make sure the parent directory is on the path so we can import bot.py
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bot import send_ai_news   # reuse all the logic from bot.py


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            asyncio.run(send_ai_news())
            body = json.dumps({"status": "ok", "message": "News sent successfully!"})
            status = 200
        except Exception as e:
            body = json.dumps({"status": "error", "message": str(e)})
            status = 500

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode())
