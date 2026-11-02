from pathlib import Path

from app.core.config import settings
from app.utils.file_upload import sanitize_display_name

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def _upload(client, headers, proposal_id, name, content, mime):
    return client.post(
        f"/api/v1/proposals/{proposal_id}/documents",
        files={"file": (name, content, mime)},
        headers=headers,
    )


def test_upload_lista_download_e_exclusao(client, auth_headers, make_proposal):
    p = make_proposal()
    res = _upload(client, auth_headers, p["id"], "matricula.pdf", PDF_BYTES, "application/pdf")
    assert res.status_code == 201, res.text
    doc = res.json()
    assert doc["display_name"] == "matricula.pdf"
    assert doc["size_bytes"] == len(PDF_BYTES)

    docs = client.get(f"/api/v1/proposals/{p['id']}/documents", headers=auth_headers).json()
    assert [d["id"] for d in docs] == [doc["id"]]

    dl = client.get(f"/api/v1/documents/{doc['id']}/download", headers=auth_headers)
    assert dl.status_code == 200
    assert dl.content == PDF_BYTES
    assert dl.headers["content-type"] == "application/pdf"

    # download exige autenticação
    assert client.get(f"/api/v1/documents/{doc['id']}/download").status_code in (401, 403)

    stored = list(Path(settings.UPLOAD_DIR).iterdir())
    assert len(stored) == 1

    assert client.delete(f"/api/v1/documents/{doc['id']}", headers=auth_headers).status_code == 204
    assert not stored[0].exists()

    actions = [h["action"] for h in client.get(f"/api/v1/proposals/{p['id']}/history", headers=auth_headers).json()]
    assert actions[:2] == ["DOCUMENT_REMOVED", "DOCUMENT_ADDED"]


def test_rejeita_tipo_nao_permitido(client, auth_headers, make_proposal):
    p = make_proposal()
    res = _upload(client, auth_headers, p["id"], "script.sh", b"#!/bin/sh", "text/x-sh")
    assert res.status_code == 415


def test_rejeita_conteudo_que_nao_bate_com_mime(client, auth_headers, make_proposal):
    p = make_proposal()
    res = _upload(client, auth_headers, p["id"], "falso.pdf", PNG_BYTES, "application/pdf")
    assert res.status_code == 400


def test_rejeita_arquivo_vazio(client, auth_headers, make_proposal):
    p = make_proposal()
    res = _upload(client, auth_headers, p["id"], "vazio.pdf", b"", "application/pdf")
    assert res.status_code == 400


def test_rejeita_arquivo_acima_do_limite(client, auth_headers, make_proposal):
    p = make_proposal()
    big = PDF_BYTES + b"0" * (settings.MAX_UPLOAD_BYTES + 1)
    res = _upload(client, auth_headers, p["id"], "grande.pdf", big, "application/pdf")
    assert res.status_code == 413


def test_sanitize_display_name_remove_caminho():
    assert sanitize_display_name("../../etc/passwd") == "passwd"
    assert sanitize_display_name("C:\\temp\\<x>.pdf").endswith("_x_.pdf")
    assert sanitize_display_name("") == "document"
