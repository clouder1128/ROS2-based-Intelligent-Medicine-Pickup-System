"""测试文件上传、下载、删除生命周期以及扩展名和异常校验。"""

import io

from flask import Flask

from api import upload_controller


def make_client(tmp_path, monkeypatch):
    monkeypatch.setattr(upload_controller, "_UPLOAD_DIR", tmp_path)
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(upload_controller.upload_bp)
    return app.test_client()


def test_upload_download_delete_lifecycle(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"name,value\nA,1\n"), "data.CSV")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["file_name"] == "data.CSV"
    assert data["content_type"] == "text/csv"
    assert data["file_size"] > 0

    file_id = data["file_id"]
    downloaded = client.get(f"/api/upload/{file_id}")
    assert downloaded.status_code == 200
    assert downloaded.data == b"name,value\nA,1\n"
    assert downloaded.mimetype == "text/csv"
    downloaded.close()

    deleted = client.delete(f"/api/upload/{file_id}")
    assert deleted.status_code == 200
    assert deleted.get_json()["data"]["deleted"] is True
    assert client.get(f"/api/upload/{file_id}").status_code == 404


def test_upload_validation_errors(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)

    assert client.post("/api/upload").status_code == 400
    assert client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"x"), "")},
        content_type="multipart/form-data",
    ).status_code == 400
    assert client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"x"), "payload.exe")},
        content_type="multipart/form-data",
    ).status_code == 400

    monkeypatch.setattr(upload_controller, "_MAX_SIZE_BYTES", 1)
    assert client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"xx"), "large.png")},
        content_type="multipart/form-data",
    ).status_code == 400

    assert client.get("/api/upload/..bad.png").status_code == 400
    assert client.delete("/api/upload/..bad.png").status_code == 400
    assert client.delete("/api/upload/missing.png").status_code == 404


def test_delete_reports_filesystem_error(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch)
    target = tmp_path / "file.png"
    target.write_bytes(b"x")

    original_unlink = upload_controller.Path.unlink

    def fail_unlink(path, *args, **kwargs):
        if path == target:
            raise OSError("locked")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(upload_controller.Path, "unlink", fail_unlink)
    response = client.delete("/api/upload/file.png")
    assert response.status_code == 500
    assert response.get_json()["error"]["code"] == "FILE_DELETE_ERROR"


def test_allowed_extension_helper():
    assert upload_controller._allowed_ext("image.PNG") == (True, "png")
    assert upload_controller._allowed_ext("no-extension") == (False, None)
