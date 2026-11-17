import io
import os
import tempfile
import time
import unittest

from document_app import create_app


class DocumentAppTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE_PATH": os.path.join(self.temp_dir.name, "jobs.sqlite"),
                "UPLOAD_FOLDER": os.path.join(self.temp_dir.name, "uploads"),
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _wait_for_status(self, job_id, expected):
        for _ in range(100):
            response = self.client.get(f"/api/jobs/{job_id}")
            payload = response.get_json()
            if payload["status"] == expected:
                return payload
            time.sleep(0.02)
        self.fail(f"Job {job_id} did not reach status {expected}")

    def test_home_page_and_health_endpoint(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})

    def test_valid_pdf_upload_is_processed_and_downloadable(self):
        response = self.client.post(
            "/upload",
            data={"document": (io.BytesIO(b"%PDF-1.4\n%EOF"), "sample.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        job_id = response.location.rsplit("/", 1)[-1]
        payload = self._wait_for_status(job_id, "Complete")
        self.assertEqual(payload["result"]["file_type"], "PDF")
        download_response = self.client.get(f"/jobs/{job_id}/download")
        self.assertEqual(download_response.status_code, 200)
        download_response.close()

    def test_wrong_file_signature_is_marked_failed(self):
        response = self.client.post(
            "/upload",
            data={"document": (io.BytesIO(b"not a pdf"), "fake.pdf")},
            content_type="multipart/form-data",
        )
        job_id = response.location.rsplit("/", 1)[-1]
        payload = self._wait_for_status(job_id, "Failed")
        self.assertIn("do not match", payload["error"])

    def test_unsupported_extension_is_rejected(self):
        response = self.client.post(
            "/upload",
            data={"document": (io.BytesIO(b"text"), "notes.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
