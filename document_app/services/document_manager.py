import hashlib
import os
import uuid


ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
MAX_FILE_BYTES = 10 * 1024 * 1024


class DocumentManager:
    """Applies upload rules and coordinates background document checks."""

    def __init__(self, repository, storage, executor):
        self.repository = repository
        self.storage = storage
        self.executor = executor

    def submit_upload(self, uploaded_file):
        original_name = (getattr(uploaded_file, "filename", "") or "").strip()
        if not original_name:
            raise ValueError("Choose a file first.")

        extension = os.path.splitext(original_name)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("Please upload a PDF, PNG, or JPEG file.")

        job_id = uuid.uuid4().hex[:12].upper()
        stored_name, path = self.storage.save(uploaded_file, job_id)
        size_bytes = os.path.getsize(path)
        if size_bytes == 0:
            os.remove(path)
            raise ValueError("The selected file is empty.")
        if size_bytes > MAX_FILE_BYTES:
            os.remove(path)
            raise ValueError("The file is larger than the 10 MB limit.")

        self.repository.create(job_id, original_name, stored_name)
        self.executor.submit(self.process_job, job_id, path, extension)
        return job_id

    def process_job(self, job_id, path, extension):
        self.repository.set_status(job_id, "Processing")
        try:
            with open(path, "rb") as source:
                sample = source.read(16)
                source.seek(0)
                digest = hashlib.sha256(source.read()).hexdigest()

            self._check_signature(sample, extension)
            result = {
                "file_size_bytes": os.path.getsize(path),
                "file_type": extension[1:].upper(),
                "sha256": digest,
                "message": "File passed the basic format check.",
            }
            self.repository.complete(job_id, result)
        except ValueError as error:
            self.repository.fail(job_id, str(error))
        except OSError:
            self.repository.fail(job_id, "The file could not be read.")
        except Exception:
            self.repository.fail(job_id, "An unexpected processing error occurred.")

    @staticmethod
    def _check_signature(sample, extension):
        valid = {
            ".pdf": sample.startswith(b"%PDF-"),
            ".png": sample.startswith(b"\x89PNG\r\n\x1a\n"),
            ".jpg": sample.startswith(b"\xff\xd8\xff"),
            ".jpeg": sample.startswith(b"\xff\xd8\xff"),
        }
        if not valid[extension]:
            raise ValueError("The file contents do not match the selected file type.")
