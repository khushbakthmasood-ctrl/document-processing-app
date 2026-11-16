"""WSGI entry point used by AWS Elastic Beanstalk."""

from document_app import create_app

application = create_app()
