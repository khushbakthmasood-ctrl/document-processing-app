# Document Processing and Status Tracking App

A small three-layer demo app for the DevOps assignment. A user uploads a PDF, PNG, or JPEG. The app checks that the file extension matches its file signature, records its status, and shows basic file details.

## The three layers

1. **Presentation layer:** Flask HTML pages in `document_app/templates` and CSS in `document_app/static`.
2. **Management layer:** `document_app/routes.py` handles web/API requests; `document_app/services/document_manager.py` applies the upload and processing rules.
3. **Data layer:** `document_app/data/job_repository.py` stores job records in SQLite; `document_app/data/file_storage.py` stores uploaded files on disk.

This local demo uses a background worker thread to process jobs. In a cloud version, the background queue could be replaced with Amazon SQS and the worker with AWS Lambda; S3 could replace local file storage, and DynamoDB could replace SQLite.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `python -m venv .venv`.
4. Activate the environment:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`
5. Run `pip install -r requirements.txt`.
6. Run `python run.py`.
7. Open `http://127.0.0.1:5000`.

To run the checks, use `python -m unittest discover -s tests`.

## Run with Docker

If Docker is installed, run `docker compose up --build` from this folder, then open `http://127.0.0.1:5000`. App data is kept in the local `data` folder.

## CI/CD assignment demo on AWS

This project is prepared for a simple GitHub-to-AWS deployment pipeline:

1. **GitHub** stores the application source code.
2. **AWS CodePipeline** starts when a new commit is pushed to the `main` branch.
3. **AWS CodeBuild** installs the requirements and runs the unit tests in `buildspec.yml`.
4. **AWS Elastic Beanstalk** runs the Flask app using the WSGI entry point in `application.py` and the start command in `Procfile`.

The home page includes a `CI/CD DEMO · VERSION 1` badge. After the first deployment, edit this text in `document_app/templates/index.html` in GitHub and change it to `CI/CD DEMO · VERSION 2`. Commit the change to `main`. When the pipeline succeeds, refresh the Elastic Beanstalk URL and show that the page displays Version 2.

The AWS environment uses an EC2 instance and can incur charges. Choose a single-instance environment, check the current AWS Free Tier/credits for your account and region, and delete the Elastic Beanstalk environment and pipeline after the demo if you no longer need them. Set a strong `SECRET_KEY` as an Elastic Beanstalk environment variable before making the app public.

## Demo scope

- Accepts PDF, PNG, and JPEG files up to 10 MB.
- Shows a job ID and status: Queued, Processing, Complete, or Failed.
- Checks basic file signatures and records file size and SHA-256 checksum.
- Lets the user download the uploaded file after processing.
- Does not include user accounts, OCR, or AI analysis yet; these are suitable extensions for the next assignment.
