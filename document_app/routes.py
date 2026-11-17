from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.exceptions import RequestEntityTooLarge


def create_blueprint(manager, repository, storage):
    routes = Blueprint("main", __name__)

    @routes.get("/")
    def index():
        return render_template("index.html", jobs=repository.list_recent())

    @routes.post("/upload")
    def upload():
        uploaded_file = request.files.get("document")
        try:
            job_id = manager.submit_upload(uploaded_file)
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("main.index"))
        return redirect(url_for("main.job_detail", job_id=job_id))

    @routes.get("/jobs/<job_id>")
    def job_detail(job_id):
        job = repository.get(job_id)
        if not job:
            return render_template("not_found.html"), 404
        return render_template("job.html", job=job)

    @routes.get("/api/jobs/<job_id>")
    def job_status(job_id):
        job = repository.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(
            {
                "job_id": job["job_id"],
                "status": job["status"],
                "updated_at": job["updated_at"],
                "result": job["result"],
                "error": job["error_message"],
            }
        )

    @routes.get("/jobs/<job_id>/download")
    def download(job_id):
        job = repository.get(job_id)
        if not job:
            return render_template("not_found.html"), 404
        path = storage.get_path(job["stored_name"])
        return _send_file(path, job["original_name"])

    @routes.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @routes.app_errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        flash("The file is larger than the 10 MB limit.", "error")
        return redirect(url_for("main.index"))

    return routes


def _send_file(path, download_name):
    from flask import send_file

    try:
        return send_file(path, as_attachment=True, download_name=download_name)
    except FileNotFoundError:
        return render_template("not_found.html"), 404
