import asyncio
import json
import uuid
import websockets
from typing import Callable, Dict, Any, Optional
import inspect
import mimetypes
import os
from urllib.parse import parse_qs, unquote
import base64
import hashlib
import urllib.request
import sys

class UpdateChecker:
    
    
    UPDATE_URL = "https://geometryamerica.xyz/updates/version.txt"
    VERSION_CHECK_TIMEOUT = 5  
    CURRENT_VERSION = "1.0.1"
    
    @staticmethod
    def check_for_updates():
        
        print("Checking for updates...", end=" ", flush=True)
        
        try:
            req = urllib.request.Request(
                UpdateChecker.UPDATE_URL,
                headers={'User-Agent': 'LKServer-UpdateChecker/1.0'}
            )
            with urllib.request.urlopen(req, timeout=UpdateChecker.VERSION_CHECK_TIMEOUT) as response:
                remote_version = response.read().decode('utf-8').strip()
            
            if remote_version == UpdateChecker.CURRENT_VERSION:
                print("Up to date!")
                return
            
            
            print("New version available!")
            print()
            print(f"  Current version: {UpdateChecker.CURRENT_VERSION}")
            print(f"  Latest version:  {remote_version}")
            print()
            print("  To update, run:")
            print()
            print("      pip install --upgrade --force-reinstall git+https://github.com/Linkmail16/lkserver.git")
            print()
            print("  Or if you installed from source:")
            print()
            print("     cd lkserver")
            print("     git pull")
            print("     pip install -e . --force-reinstall")
            print()

            
        except Exception as e:
            print(f"Failed")

class Request:
    def __init__(self, data: Dict[str, Any]):
        self.method = data['method']
        self.path = data['path']
        self.full_path = data['path']
        self.headers = data.get('headers', {})
        self.remote_addr = data.get('remote_addr', 'unknown')
        self.query_string = ''
        
        
        if '?' in self.path:
            self.path, self.query_string = self.full_path.split('?', 1)
        
        
        self.args = {}
        if self.query_string:
            for param in self.query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    self.args[unquote(key)] = unquote(value)
        
        
        self.form = {}
        self.json_data = None
        self.files = {}
        
        
        if data.get('body_encoding') == 'base64':
            self.raw_body = base64.b64decode(data.get('body', ''))
        else:
            self.raw_body = data.get('body', '').encode('utf-8') if isinstance(data.get('body', ''), str) else data.get('body', b'')
        
        self.body = self.raw_body.decode('utf-8', errors='ignore') if self.raw_body else ''
        
        
        content_type = self.headers.get('content-type', '').lower()
        
        if 'application/json' in content_type and self.body:
            try:
                self.json_data = json.loads(self.body)
            except:
                pass
        
        elif 'application/x-www-form-urlencoded' in content_type and self.body:
            parsed = parse_qs(self.body)
            self.form = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        
        elif 'multipart/form-data' in content_type:
            
            self._parse_multipart()
    
    def _parse_multipart(self):
        
        try:
            content_type = self.headers.get('content-type', '')
            boundary = None
            for part in content_type.split(';'):
                if 'boundary=' in part:
                    boundary = part.split('boundary=')[1].strip()
                    break
            
            if not boundary:
                return
            
            parts = self.raw_body.split(f'--{boundary}'.encode())
            
            for part in parts[1:-1]:  
                if not part.strip():
                    continue
                
                
                try:
                    header_end = part.find(b'\r\n\r\n')
                    if header_end == -1:
                        continue
                    
                    headers = part[:header_end].decode('utf-8', errors='ignore')
                    content = part[header_end+4:].rstrip(b'\r\n')
                    
                    
                    name = None
                    filename = None
                    for line in headers.split('\r\n'):
                        if 'Content-Disposition' in line:
                            if 'name="' in line:
                                name = line.split('name="')[1].split('"')[0]
                            if 'filename="' in line:
                                filename = line.split('filename="')[1].split('"')[0]
                    
                    if name:
                        if filename:
                            self.files[name] = {
                                'filename': filename,
                                'content': content
                            }
                        else:
                            self.form[name] = content.decode('utf-8', errors='ignore')
                except:
                    continue
        except:
            pass
    
    def get_json(self):
        
        return self.json_data

def send_file(filepath: str, mimetype: str = None, as_attachment: bool = False, attachment_filename: str = None):
    
    if not os.path.exists(filepath):
        return ('<h1>404 Not Found</h1><p>File not found</p>', 404, {'Content-Type': 'text/html'})
    
    with open(filepath, 'rb') as f:
        content = f.read()
    
    if mimetype is None:
        mimetype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'
    
    headers = {'Content-Type': mimetype}
    
    if as_attachment:
        filename = attachment_filename or os.path.basename(filepath)
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    
    encoded_content = base64.b64encode(content).decode('utf-8')
    
    return (encoded_content, 200, headers, 'base64')

def redirect(location: str, code: int = 302):
    
    return (
        f'<html><body>Redirecting to <a href="{location}">{location}</a></body></html>',
        code,
        {'Location': location, 'Content-Type': 'text/html'}
    )

def render_template(template_path: str, **context):
    
    if not os.path.exists(template_path):
        return f'<h1>Template Error</h1><p>Template {template_path} not found</p>'
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()
    
    
    for key, value in context.items():
        template = template.replace('{{ ' + key + ' }}', str(value))
        template = template.replace('{{' + key + '}}', str(value))
    
    
    import re
    for_pattern = r'\{% for (\w+) in (\w+) %\}(.*?)\{% endfor %\}'
    
    def replace_loop(match):
        item_name = match.group(1)
        list_name = match.group(2)
        loop_content = match.group(3)
        
        if list_name not in context:
            return ''
        
        result = []
        for item in context[list_name]:
            item_html = loop_content
            if isinstance(item, dict):
                for k, v in item.items():
                    item_html = item_html.replace('{{ ' + item_name + '.' + k + ' }}', str(v))
                    item_html = item_html.replace('{{' + item_name + '.' + k + '}}', str(v))
            else:
                item_html = item_html.replace('{{ ' + item_name + ' }}', str(item))
                item_html = item_html.replace('{{' + item_name + '}}', str(item))
            result.append(item_html)
        
        return ''.join(result)
    
    template = re.sub(for_pattern, replace_loop, template, flags=re.DOTALL)
    
    
    if_pattern = r'\{% if (\w+) %\}(.*?)\{% endif %\}'
    
    def replace_if(match):
        condition = match.group(1)
        content = match.group(2)
        
        if condition in context and context[condition]:
            return content
        return ''
    
    template = re.sub(if_pattern, replace_if, template, flags=re.DOTALL)
    
    return template

class LKServer:
    def __init__(self, port: int = 7000, debug: bool = False, name: str = None, 
                 security: dict = None, token: str = None, check_updates: bool = True,
                 timeout: int = 300):
        self.server_url = f'ws://195.35.9.209:{port}/ws'
        self.client_id = str(uuid.uuid4())
        self.name = name
        self.routes = {}
        self.redirects = {}
        self.ws = None
        self.public_url = None
        self.running = False
        self.debug = debug
        self.blocked_ips = set()
        self.security_config = security or {}
        self.static_folder = 'static'
        self.template_folder = 'templates'
        self.token = token  
        self.check_updates = check_updates
        self.keepalive_task = None
        self.timeout = timeout
        
    def block_ip(self, ip: str):
        self.blocked_ips.add(ip)
        
    def unblock_ip(self, ip: str):
        self.blocked_ips.discard(ip)
    
    def add_redirect(self, from_path: str, to_path: str, code: int = 302):
        
        self.redirects[from_path] = (to_path, code)
        if self.debug:
            print(f"Added redirect: {from_path} -> {to_path} ({code})")
    
    def remove_redirect(self, from_path: str):
        
        if from_path in self.redirects:
            del self.redirects[from_path]
            if self.debug:
                print(f"Removed redirect: {from_path}")
    
    def static(self, path: str):
        
        @self.route(f'{path}/<filename>')
        def serve_static(request):
            filename = request.path.split('/')[-1]
            filepath = os.path.join(self.static_folder, filename)
            return send_file(filepath)
        
        return serve_static
        
    def route(self, path: str, methods: list = None):
        if methods is None:
            methods = ['GET']
        
        def decorator(func: Callable):
            if path not in self.routes:
                self.routes[path] = {}
            
            for method in methods:
                self.routes[path][method.upper()] = func
            
            return func
        
        return decorator
    
    def get(self, path: str):
        return self.route(path, methods=['GET'])
    
    def post(self, path: str):
        return self.route(path, methods=['POST'])
    
    def put(self, path: str):
        return self.route(path, methods=['PUT'])
    
    def delete(self, path: str):
        return self.route(path, methods=['DELETE'])
    
    async def _keepalive_loop(self):
        """Envía pings para mantener la conexión viva"""
        while self.running and self.ws:
            try:
                await asyncio.sleep(self.timeout // 10)
                if self.ws and self.running:
                   
                    await self.ws.ping()
            except Exception:
                
                break
    
    async def _handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        request = Request(request_data)
        
        if request.remote_addr in self.blocked_ips:
            return {
                'status': 403,
                'body': '<h1>403 Forbidden</h1><p>Your IP has been blocked</p>',
                'headers': {'Content-Type': 'text/html'}
            }
        
        
        if request.path in self.redirects:
            target, code = self.redirects[request.path]
            return {
                'status': code,
                'body': f'<html><body>Redirecting to <a href="{target}">{target}</a></body></html>',
                'headers': {'Location': target, 'Content-Type': 'text/html'}
            }
        
        handler = None
        if request.path in self.routes and request.method in self.routes[request.path]:
            handler = self.routes[request.path][request.method]
        
        if not handler:
            return {
                'status': 404,
                'body': f'<h1>404 Not Found</h1><p>Route {request.method} {request.path} not found</p>',
                'headers': {'Content-Type': 'text/html'}
            }
        
        try:
            sig = inspect.signature(handler)
            if len(sig.parameters) > 0:
                if inspect.iscoroutinefunction(handler):
                    result = await handler(request)
                else:
                    result = handler(request)
            else:
                if inspect.iscoroutinefunction(handler):
                    result = await handler()
                else:
                    result = handler()
            
            
            if isinstance(result, dict):
                return {
                    'status': 200,
                    'body': json.dumps(result),
                    'headers': {'Content-Type': 'application/json'}
                }
            elif isinstance(result, tuple):
                body = result[0]
                status = result[1]
                headers = result[2] if len(result) > 2 else {}
                encoding = result[3] if len(result) > 3 else None
                
                response = {
                    'status': status,
                    'headers': headers
                }
                
                if encoding == 'base64':
                    response['body'] = body
                    response['body_encoding'] = 'base64'
                elif isinstance(body, dict):
                    response['body'] = json.dumps(body)
                    headers.setdefault('Content-Type', 'application/json')
                else:
                    response['body'] = str(body)
                    headers.setdefault('Content-Type', 'text/html')
                
                return response
            else:
                return {
                    'status': 200,
                    'body': str(result),
                    'headers': {'Content-Type': 'text/html'}
                }
        
        except Exception as e:
            print(f"Error in handler {request.path}: {e}")
            import traceback
            traceback.print_exc()
            return {
                'status': 500,
                'body': f'<h1>500 Internal Server Error</h1><p>{str(e)}</p>',
                'headers': {'Content-Type': 'text/html'}
            }
    
    async def _listen(self):
        try:
            async for message in self.ws:
                if isinstance(message, bytes):
                    message = message.decode('utf-8')
                
                data = json.loads(message)
                
                if data['type'] == 'registered':
                    self.public_url = data['public_url']
                    http_port = data['http_port']
                    has_token = data.get('has_token', False)
                    time_info = data.get('time_info', {})
                    
                    print(f"\n{'='*60}")
                    print(f"Server exposed successfully")
                    print(f"{'='*60}")
                    print(f"Master URL: {self.public_url}")
                    if self.name:
                        print(f"Mirror URL: http://172.86.90.227:7000/s/{self.name}")
                    
                    if has_token:
                        print(f"\nStatus: WITH TOKEN")
                        print(f"Time remaining: {time_info.get('remaining_formatted', 'N/A')}")
                        print(f"Reset in: {time_info.get('reset_in', 0)} seconds")
                        print(f"Max servers: 3 simultaneous")
                    else:
                        print(f"\nStatus: FREE (No Token)")
                        print(f"Time remaining: {time_info.get('remaining_formatted', 'N/A')}")
                        print(f"Reset in: {time_info.get('reset_in', 0)} seconds (12 hours)")
                        print(f"Max servers: 1 at a time")
                        print(f"\nTip: Get a token for 48 hours and 3 servers!")
                    
                    if time_info.get('active_servers', 0) > 1:
                        print(f"\n⚠️  WARNING: You have {time_info['active_servers']} active servers")
                        print(f"   Time consumption rate: {time_info.get('consumption_rate', 'N/A')}")
                    
                    print(f"Request timeout: {self.timeout} seconds")
                    print(f"{'='*60}\n")
                    
                    
                    if not self.keepalive_task:
                        self.keepalive_task = asyncio.create_task(self._keepalive_loop())
                
                elif data['type'] == 'warning':
                    print(f"\n⚠️  {data['message']}")
                    if 'time_remaining' in data:
                        print(f"   Time left: {data['time_remaining']}s\n")
                
                elif data['type'] == 'disconnecting':
                    print(f"\n{data['message']}")
                    print(f"   {data.get('detail', '')}\n")
                    self.running = False
                
                elif data['type'] == 'error':
                    print(f"ERROR: {data['message']}")
                    if 'name_taken' in data:
                        print(f"El nombre '{self.name}' ya está en uso. Elige otro nombre.")
                
                elif data['type'] == 'http_request':
                    request_id = data['request_id']
                    
                    if self.debug:
                        print(f"{data['method']} {data['path']} - {data.get('remote_addr', 'unknown')}")
                    
                    response = await self._handle_request(data)
                    response['type'] = 'http_response'
                    response['request_id'] = request_id
                    
                    await self.ws.send(json.dumps(response))
        
        except websockets.exceptions.ConnectionClosed:
            print("Connection closed")
            self.running = False
        except Exception as e:
            print(f"Error in listen: {e}")
            import traceback
            traceback.print_exc()
            self.running = False
        finally:
          
            if self.keepalive_task:
                self.keepalive_task.cancel()
                self.keepalive_task = None
    
    async def _connect(self):
        print("Connecting to server...")
        
        try:
            async with websockets.connect(
                self.server_url,
                ping_interval=self.timeout // 10,
                ping_timeout=self.timeout // 15,
                max_size=10 * 1024 * 1024,
                close_timeout=self.timeout
            ) as ws:
                self.ws = ws
                
                await ws.send(json.dumps({
                    'type': 'register',
                    'client_id': self.client_id,
                    'name': self.name,
                    'security': self.security_config,
                    'token': self.token
                }))
                
                self.running = True
                await self._listen()
        
        except Exception as e:
            print(f"Connection error: {e}")
            self.running = False
        finally:
           
            if self.keepalive_task:
                self.keepalive_task.cancel()
                self.keepalive_task = None
    
    def run(self):
        
        if self.check_updates:
            UpdateChecker.check_for_updates()
        
        print("Starting LKServer...")
        print(f"Registered routes: {len(self.routes)}")
        
        for path, methods in self.routes.items():
            for method in methods.keys():
                print(f"  {method} {path}")
        
        if self.redirects:
            print(f"Registered redirects: {len(self.redirects)}")
            for path, (target, code) in self.redirects.items():
                print(f"  {path} -> {target} ({code})")
        
        try:
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._connect())
                print("Server task created. Running in background...")
            except RuntimeError:
                asyncio.run(self._connect())
        except KeyboardInterrupt:
            print("\nStopping server...")
    
    async def run_async(self):
        
        if self.check_updates:
            UpdateChecker.check_for_updates()
        await self._connect()
    
    def run_background(self):
        
        if self.check_updates:
            UpdateChecker.check_for_updates()
        
        print("Starting LKServer in background...")
        print(f"Registered routes: {len(self.routes)}")
        
        for path, methods in self.routes.items():
            for method in methods.keys():
                print(f"  {method} {path}")
        
        if self.redirects:
            print(f"Registered redirects: {len(self.redirects)}")
            for path, (target, code) in self.redirects.items():
                print(f"  {path} -> {target} ({code})")
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        task = asyncio.create_task(self._connect())
        print("Server is running in background...")
        return task
