from flask import Flask
from .routes import main # Lưu ý dấu chấm để import từ cùng thư mục

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # Đăng ký các Blueprint
    app.register_blueprint(main)

    return app