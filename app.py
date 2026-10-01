import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import boto3
import pymysql

app = Flask(__name__)

S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
DB_HOST = os.environ.get("DB_HOST")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME", "studentdb")

def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    course = request.form.get('course')
    photo = request.files.get('photo')

    if not photo or photo.filename == '':
        return "No photo uploaded", 400

    filename = secure_filename(photo.filename)

    s3 = boto3.client('s3')
    s3.upload_fileobj(
        photo,
        S3_BUCKET_NAME,
        filename,
        ExtraArgs={"ContentType": photo.content_type}
    )

    photo_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{filename}"

    conn = get_db()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO students (name, email, course, photo_url) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, email, course, photo_url))
        conn.commit()
    finally:
        conn.close()

    return f"<h2>Registration Successful!</h2><p>Student {name} registered.</p><p><img src='{photo_url}' width='200'/></p><a href='/'>Register Another</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
