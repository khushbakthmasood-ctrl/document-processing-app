import os
from concurrent.futures import ThreadPoolExecutor

from flask import Flask

from document_app.data.file_storage import LocalFileStorage
from document_app.data.job_repository import JobRepository
from document_app.routes import create_blueprint
from document_app.services.document_manager import DocumentManager


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-before-deployment"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH", os.path.join(app.instance_path, "jobs.sqlite")
        ),
        UPLOAD_FOLDER=os.environ.get(
            "UPLOAD_FOLDER", os.path.join(app.instance_path, "uploads")
        ),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    repository = JobRepository(app.config["DATABASE_PATH"])
    repository.initialize()
    storage = LocalFileStorage(app.config["UPLOAD_FOLDER"])
    executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="document-worker")
    manager = DocumentManager(repository, storage, executor)

    app.extensions["job_repository"] = repository
    app.extensions["document_manager"] = manager
    app.register_blueprint(create_blueprint(manager, repository, storage))
    return app
