\
import os
from flask import Blueprint, send_file, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from .models import db

bp = Blueprint("backup", __name__, url_prefix="/backup")

@bp.get("/")
def index():
    return """
    <div style='font-family: system-ui, sans-serif; padding:20px'>
      <h2>Backup & Restore</h2>
      <p><a href='/backup/download' class='btn btn-primary'>Baixar backup (DB)</a></p>
      <form method='post' action='/backup/restore' enctype='multipart/form-data'>
        <label>Restaurar banco (.db/.sqlite):</label><br>
        <input type='file' name='dbfile' accept='.db,.sqlite' required>
        <button style='margin-left:10px'>Restaurar</button>
      </form>
      <p style='margin-top:10px; color:#555'>Ao restaurar, as informações do arquivo enviado passam a valer imediatamente.</p>
    </div>
    """

@bp.get("/download")
def download():
    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    assert db_uri.startswith("sqlite:///"), "Somente SQLite é suportado para backup."
    db_path = db_uri.replace("sqlite:///","")
    filename = os.path.basename(db_path)
    return send_file(db_path, as_attachment=True, download_name=filename)

@bp.post("/restore")
def restore():
    file = request.files.get("dbfile")
    if not file:
        flash("Nenhum arquivo enviado.", "warning")
        return redirect(url_for("backup.index"))
    filename = secure_filename(file.filename)
    if not filename.lower().endswith((".db",".sqlite")):
        flash("Envie um arquivo .db ou .sqlite.", "warning")
        return redirect(url_for("backup.index"))

    db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    assert db_uri.startswith("sqlite:///"), "Somente SQLite é suportado para restore."
    db_path = db_uri.replace("sqlite:///","")

    # Salva em temporário e troca
    tmp_path = db_path + ".uploading"
    file.save(tmp_path)

    # Fecha conexões pendentes
    db.session.close()
    db.engine.dispose()

    # Troca o arquivo
    os.replace(tmp_path, db_path)

    # Opcional: revalidar schema (caso a estrutura esteja atrás/à frente)
    try:
        from .models import ensure_schema
        ensure_schema()
    except Exception:
        pass

    flash("Backup restaurado com sucesso! Os dados já estão ativos.", "success")
    return redirect(url_for("backup.index"))
