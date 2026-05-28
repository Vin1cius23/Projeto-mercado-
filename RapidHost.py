import os
from flask import Flask, render_template

_ip = "0.0.0.0"
_port = 5000
_static_path = ""
_template_path = ""

def hostIP(ip):
    global _ip
    _ip = ip

def hostPort(port):
    global _port
    _port = int(port)

def setStaticPath(path):
    global _static_path
    _static_path = path

def setTemplatePath(path):
    global _template_path
    _template_path = path

def hostSite(filename, information=""):
    """
    Hosts the site using standard Flask under the hood, importing the unified 
    app if available, or setting up a fallback server.
    """
    global _ip, _port, _static_path, _template_path
    
    # Try to import our unified Flask app and run it
    try:
        from app import app as unified_app
        print(f"[RapidHost] Running unified application on http://{_ip}:{_port}")
        unified_app.run(debug=True, host=_ip, port=_port, use_reloader=False)
    except Exception as e:
        print(f"[RapidHost] Fallback to simple server due to: {e}")
        # Fallback simple Flask app
        app = Flask(
            __name__,
            static_folder=_static_path if _static_path else "Static",
            template_folder=_template_path if _template_path else "Template"
        )
        
        @app.route("/")
        def index():
            return render_template(filename)
            
        app.run(debug=True, host=_ip, port=_port, use_reloader=False)
