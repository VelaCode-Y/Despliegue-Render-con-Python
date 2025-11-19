from flask import Flask, render_template, request, redirect, url_for, flash
import os

# --- Detección de motor de BD ---
DB_URL = os.environ.get("DATABASE_URL")  # Render: postgres://...
USE_SQLITE = not bool(DB_URL)            # Si no hay DATABASE_URL → usamos SQLite local

# Imports según el motor
if USE_SQLITE:
    import sqlite3
else:
    import psycopg2

app = Flask(__name__, template_folder='views')
app.secret_key = os.environ.get("SECRET_KEY", "dev")


# ---------- Conexión ----------
def get_conn():
    """Devuelve una conexión según el motor disponible."""
    if USE_SQLITE:
        return sqlite3.connect("usuarios_local.db")
    else:
        return psycopg2.connect(DB_URL, sslmode="require")


# ---------- Inicialización de BD ----------
def init_db():
    """Crea la tabla si no existe, con SQL según el motor."""
    if USE_SQLITE:
        sql = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            fecha_nacimiento TEXT NOT NULL,
            sexo TEXT NOT NULL,
            pais TEXT NOT NULL,
            tipo_documento TEXT NOT NULL,
            numero_documento TEXT NOT NULL,
            correo TEXT NOT NULL,
            departamento TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """
    else:
        sql = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombres VARCHAR(100) NOT NULL,
            apellidos VARCHAR(100) NOT NULL,
            fecha_nacimiento DATE NOT NULL,
            sexo VARCHAR(10) NOT NULL,
            pais VARCHAR(100) NOT NULL,
            tipo_documento VARCHAR(50) NOT NULL,
            numero_documento VARCHAR(50) NOT NULL,
            correo VARCHAR(120) NOT NULL,
            departamento VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        cur.close()


@app.after_request
def force_utf8(response):
    """Garantiza UTF-8 en todas las respuestas HTML."""
    ct = response.headers.get("Content-Type", "")
    if ct.startswith("text/html") and "charset" not in ct.lower():
        response.headers["Content-Type"] = ct + "; charset=utf-8"
    return response


# ---------- Rutas ----------
@app.route("/", methods=["GET"])
def root_redirect():
    return redirect(url_for("registro"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    """Formulario principal."""
    if request.method == "POST":
        datos = {
            "nombres": (request.form.get("nombres") or "").strip(),
            "apellidos": (request.form.get("apellidos") or "").strip(),
            "fecha_nacimiento": (request.form.get("fecha_nacimiento") or "").strip(),
            "sexo": (request.form.get("sexo") or "").strip(),
            "pais": (request.form.get("pais") or "").strip(),
            "tipo_documento": (request.form.get("tipo_documento") or "").strip(),
            "numero_documento": (request.form.get("numero_documento") or "").strip(),
            "correo": (request.form.get("correo") or "").strip(),
            "departamento": (request.form.get("departamento") or "").strip(),
        }

        if not all(datos.values()):
            flash("Todos los campos son obligatorios.", "error")
            return render_template("registro.html", datos=datos)

        if USE_SQLITE:
            insert_sql = """
                INSERT INTO usuarios
                (nombres, apellidos, fecha_nacimiento, sexo, pais, tipo_documento,
                 numero_documento, correo, departamento)
                VALUES (:nombres, :apellidos, :fecha_nacimiento, :sexo, :pais,
                        :tipo_documento, :numero_documento, :correo, :departamento)
            """
        else:
            insert_sql = """
                INSERT INTO usuarios
                (nombres, apellidos, fecha_nacimiento, sexo, pais, tipo_documento,
                 numero_documento, correo, departamento)
                VALUES (%(nombres)s, %(apellidos)s, %(fecha_nacimiento)s, %(sexo)s,
                        %(pais)s, %(tipo_documento)s, %(numero_documento)s,
                        %(correo)s, %(departamento)s)
            """

        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(insert_sql, datos)
            conn.commit()
            cur.close()

        flash("Registro guardado correctamente ✅", "ok")
        return redirect(url_for("registro"))

    return render_template("registro.html")


@app.route("/usu_registrados", methods=["GET"])
def usu_registrados():
    sql = """
        SELECT id, nombres, apellidos, fecha_nacimiento, sexo, pais,
               tipo_documento, numero_documento, correo, departamento, created_at
        FROM usuarios
        ORDER BY created_at DESC
    """

    with get_conn() as conn:
        if USE_SQLITE:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql)
            filas = cur.fetchall()
            datos = [dict(row) for row in filas]
            cur.close()
        else:
            cur = conn.cursor()
            cur.execute(sql)
            filas = cur.fetchall()
            cols = [desc[0] for desc in cur.description]
            datos = [dict(zip(cols, f)) for f in filas]
            cur.close()

    return render_template("usu_registrados.html", datos=datos)


# ---------- Arranque ----------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080)
