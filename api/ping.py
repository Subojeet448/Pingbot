from http.server import BaseHTTPRequestHandler
import urllib.request
import urllib.error
import json
import time
import ssl

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # Parse URL from query string
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        target_url = params.get('url', [None])[0]

        if not target_url:
            self.wfile.write(json.dumps({'error': 'No URL provided'}).encode())
            return

        # Add https:// if missing
        if not target_url.startswith(('http://', 'https://')):
            target_url = 'https://' + target_url

        result = self._ping(target_url)
        self.wfile.write(json.dumps(result).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def _ping(self, url):
        start = time.time()
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'PingBot/1.0 (Uptime Monitor)',
                    'Accept': '*/*'
                }
            )
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                ms = round((time.time() - start) * 1000)
                status_code = resp.getcode()
                return {
                    'url': url,
                    'status': 'up',
                    'status_code': status_code,
                    'ms': ms,
                    'ok': True
                }
        except urllib.error.HTTPError as e:
            ms = round((time.time() - start) * 1000)
            # 4xx/5xx — site is reachable but returning error
            ok = e.code < 500
            return {
                'url': url,
                'status': 'up' if ok else 'down',
                'status_code': e.code,
                'ms': ms,
                'ok': ok
            }
        except urllib.error.URLError as e:
            ms = round((time.time() - start) * 1000)
            return {
                'url': url,
                'status': 'down',
                'status_code': 0,
                'ms': ms,
                'ok': False,
                'error': str(e.reason)
            }
        except Exception as e:
            ms = round((time.time() - start) * 1000)
            return {
                'url': url,
                'status': 'down',
                'status_code': 0,
                'ms': ms,
                'ok': False,
                'error': str(e)
            }

    def log_message(self, format, *args):
        pass  # Suppress default logging
