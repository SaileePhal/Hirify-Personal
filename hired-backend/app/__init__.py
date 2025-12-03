from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from app.routes.auth_routes import auth_bp
    from app.routes.job_routes import job_bp
    from app.routes.user_jobs_routes import user_jobs_bp


    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(job_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(user_jobs_bp, url_prefix="/api/v1/user-jobs")

    return app
