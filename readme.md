# LKServer

**Expose your local Python servers to the internet instantly**

LKServer is a simple yet powerful Python framework that allows you to expose local HTTP servers to the internet through WebSocket tunnels. Perfect for testing webhooks, sharing demos, or accessing local services remotely.

## ✨ Features

- 🌐 **Instant Public URLs** - Get a public URL for your local server in seconds
- 🔒 **Optional Token System** - Free tier (5h) or token-based (48h) with multiple servers
- 📁 **Static Files** - Serve static files effortlessly
- 📝 **Template Engine** - Built-in Jinja2-style templating
- 🔄 **Redirects** - Easy URL redirection management
- 🛡️ **IP Blocking** - Built-in IP blocking capabilities
- 🎯 **Route Decorators** - Flask-style routing with `@app.route()`
- 📤 **File Uploads** - Handle multipart/form-data easily
- 🔍 **Request Parsing** - Automatic parsing of JSON, forms, and query parameters

## 📦 Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/Linkmail16/lkserver.git
```

Or install from source:

```bash
git clone https://github.com/Linkmail16/lkserver.git
cd lkserver
pip install -e .
```

## 🚀 Quick Start

### Basic Hello World

```python
from lkserver import LKServer

app = LKServer(debug=True)

@app.route('/')
def home(request):
    return '<h1>Hello World!</h1>'

app.run()
```

### With Custom Name

```python
app = LKServer(name="myapp", debug=True)

@app.route('/')
def home(request):
    return '<h1>My Custom App</h1>'

app.run()
```

### With Token (48 hours + 3 servers)

```python
app = LKServer(token="your-token-here", debug=True)

@app.route('/')
def home(request):
    return '<h1>Premium Server!</h1>'

app.run()
```

## 📚 Examples

### Handling Different HTTP Methods

```python
from lkserver import LKServer

app = LKServer()

@app.get('/')
def home(request):
    return '<h1>GET Request</h1>'

@app.post('/submit')
def submit(request):
    data = request.get_json()
    return {'status': 'success', 'data': data}

@app.route('/api', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api(request):
    return f'<h1>Method: {request.method}</h1>'

app.run()
```

### Working with Forms and JSON

```python
@app.post('/form')
def handle_form(request):
    # Form data
    username = request.form.get('username')
    password = request.form.get('password')
    
    return f'<h1>Welcome {username}!</h1>'

@app.post('/json')
def handle_json(request):
    # JSON data
    data = request.get_json()
    name = data.get('name')
    
    return {'message': f'Hello {name}!'}

@app.get('/search')
def search(request):
    # Query parameters
    query = request.args.get('q', 'default')
    return f'<h1>Searching for: {query}</h1>'
```

### File Uploads

```python
@app.post('/upload')
def upload(request):
    if 'file' in request.files:
        file_data = request.files['file']
        filename = file_data['filename']
        content = file_data['content']
        
        # Save the file
        with open(f'uploads/{filename}', 'wb') as f:
            f.write(content)
        
        return {'status': 'success', 'filename': filename}
    
    return {'status': 'error', 'message': 'No file uploaded'}
```

### Serving Static Files

```python
from lkserver import LKServer, send_file

app = LKServer()

@app.get('/download')
def download(request):
    return send_file('myfile.pdf', as_attachment=True)

@app.get('/image')
def image(request):
    return send_file('photo.jpg', mimetype='image/jpeg')

# Serve entire static folder
app.static('/static')

app.run()
```

### Using Templates

```python
from lkserver import LKServer, render_template

app = LKServer()

@app.get('/profile')
def profile(request):
    return render_template('profile.html', 
                         name='John Doe',
                         age=30,
                         skills=['Python', 'JavaScript', 'Docker'])

app.run()
```

**templates/profile.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Profile</title>
</head>
<body>
    <h1>{{ name }}</h1>
    <p>Age: {{ age }}</p>
    <h2>Skills:</h2>
    <ul>
    {% for skill in skills %}
        <li>{{ skill }}</li>
    {% endfor %}
    </ul>
</body>
</html>
```

### Redirects

```python
from lkserver import LKServer, redirect

app = LKServer()

@app.get('/old-page')
def old_page(request):
    return redirect('/new-page', code=301)

# Or add redirect rules
app.add_redirect('/old-url', '/new-url', code=302)
app.remove_redirect('/old-url')

app.run()
```

### IP Blocking

```python
app = LKServer()

# Block an IP
app.block_ip('192.168.1.100')

# Unblock an IP
app.unblock_ip('192.168.1.100')

@app.route('/')
def home(request):
    # Blocked IPs will get 403 Forbidden automatically
    return '<h1>Welcome!</h1>'

app.run()
```

### Security Configuration

LKServer includes advanced security features that can be configured at startup:

```python
# Basic security configuration
security_config = {
    'whitelist': ['192.168.1.100', '10.0.0.5'],  # Only these IPs can access
    'blacklist': ['203.0.113.0', '198.51.100.0'], # These IPs are blocked
    'rate_limit': 100,  # Max requests per minute per IP
    'require_auth': True,  # Require authentication
    'auth_token': 'your-secret-token'  # Token for authentication
}

app = LKServer(security=security_config)

@app.route('/')
def home(request):
    return '<h1>Protected Server</h1>'

app.run()
```

**Security Options:**

| Option | Type | Description |
|--------|------|-------------|
| `whitelist` | list | List of IP addresses allowed to access the server. If set, only these IPs can connect |
| `blacklist` | list | List of IP addresses blocked from accessing the server |
| `rate_limit` | int | Maximum number of requests per minute per IP address |
| `require_auth` | bool | If True, requires authentication header for all requests |
| `auth_token` | str | Token required in `Authorization: Bearer <token>` header when `require_auth=True` |

**Example: Whitelist Only**
```python
# Only allow specific IPs
app = LKServer(security={
    'whitelist': ['192.168.1.100', '192.168.1.101']
})
```

**Example: Rate Limiting**
```python
# Limit to 50 requests per minute per IP
app = LKServer(security={
    'rate_limit': 50
})
```

**Example: Token Authentication**
```python
# Require Bearer token authentication
app = LKServer(security={
    'require_auth': True,
    'auth_token': 'my-secret-token-123'
})

# Clients must send:
# Authorization: Bearer my-secret-token-123
```

**Example: Combined Security**
```python
# Multiple security layers
app = LKServer(security={
    'blacklist': ['203.0.113.0'],  # Block known bad actors
    'rate_limit': 100,              # Prevent abuse
    'require_auth': True,           # Require authentication
    'auth_token': 'secure-token'    # Secret token
})
```

**Dynamic IP Blocking:**
```python
app = LKServer()

@app.route('/admin/block')
def block_user(request):
    ip_to_block = request.args.get('ip')
    app.block_ip(ip_to_block)
    return f'<h1>Blocked {ip_to_block}</h1>'

@app.route('/admin/unblock')
def unblock_user(request):
    ip_to_unblock = request.args.get('ip')
    app.unblock_ip(ip_to_unblock)
    return f'<h1>Unblocked {ip_to_unblock}</h1>'

app.run()
```

### Async Handlers

```python
import asyncio
from lkserver import LKServer

app = LKServer()

@app.get('/async')
async def async_handler(request):
    await asyncio.sleep(1)
    return '<h1>Async Response!</h1>'

app.run()
```

### Running in Jupyter/Colab

```python
from lkserver import LKServer

app = LKServer()

@app.route('/')
def home(request):
    return '<h1>Running in Jupyter!</h1>'

# Run in background
task = app.run_background()
```

## 🔧 API Reference

### LKServer

```python
app = LKServer(
    ,           # Port number
    debug=False,         # Enable debug mode
    name=None,           # Custom server name
    token=None,          # Optional token for extended time
    security=None        # Security configuration (dict)
)
```

### Request Object

```python
request.method        # HTTP method (GET, POST, etc.)
request.path          # Request path
request.headers       # Headers dictionary
request.args          # Query parameters dictionary
request.form          # Form data dictionary
request.files         # Uploaded files dictionary
request.json_data     # Parsed JSON data
request.body          # Raw body string
request.remote_addr   # Client IP address
request.get_json()    # Get JSON data
```

### Helper Functions

```python
send_file(filepath, mimetype=None, as_attachment=False, attachment_filename=None)
redirect(location, code=302)
render_template(template_path, **context)
```

## 🎯 Token System

### Free Tier (No Token)
- ⏱️ 5 hours of total usage
- 🖥️ 1 server at a time
- 🔄 Resets every 12 hours

### With Token
- ⏱️ 48 hours of total usage
- 🖥️ Up to 3 simultaneous servers
- 🔄 Resets every 1 hour

Get your token from the service provider and use it like this:

```python
app = LKServer(token="your-token-here")
```

## 📁 Project Structure Example

```
your-project/
├── app.py              # Your main application
├── templates/          # HTML templates
│   └── index.html
├── static/            # Static files (CSS, JS, images)
│   ├── style.css
│   └── script.js
└── uploads/           # Uploaded files (create as needed)
```

## 🛠️ Development

Clone the repository and install in development mode:

```bash
git clone https://github.com/Linkmail16/lkserver.git
cd lkserver
pip install -e .
```

## 🐛 Issues

Found a bug? Have a feature request? Please open an issue on [GitHub](https://github.com/Linkmail16/lkserver/issues).


**Made with ❤️ by Linkmail**