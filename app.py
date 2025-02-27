# app.py
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import threading
import queue
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///emails.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Email queue for background processing
email_queue = queue.Queue()


# Database Models
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="DRAFT")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    emails = db.relationship("Email", backref="campaign", lazy=True)


class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False)
    recipient = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default="PENDING")
    meta_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)


def generate_email_content(prompt, meta_data):
    """Generate email content using Groq API"""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Replace placeholders in prompt with meta_data values
    for key, value in meta_data.items():
        prompt = prompt.replace(f"{{{key}}}", str(value))

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Generate a professional email with the following context: {prompt}",
            }
        ],
        model="mixtral-8x7b-32768",
        temperature=0.7,
        max_tokens=500,
    )

    return response.choices[0].message.content


def send_email(recipient, content):
    """Send email using SMTP"""
    sender_email = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient
    msg["Subject"] = "Your Subject"
    msg.attach(MIMEText(content, "plain"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)


def email_worker():
    """Background worker to process emails"""
    with app.app_context():
        while True:
            try:
                email_id = email_queue.get()
                if email_id is None:
                    break

                email = Email.query.get(email_id)
                campaign = Campaign.query.get(email.campaign_id)

                try:
                    # Generate content
                    content = generate_email_content(campaign.prompt, email.meta_data)

                    # Send email
                    send_email(email.recipient, content)

                    # Update status
                    email.status = "SENT"
                    email.sent_at = datetime.utcnow()
                    db.session.commit()

                except Exception as e:
                    print(f"Error sending email {email_id}: {str(e)}")
                    email.status = "FAILED"
                    db.session.commit()

            except Exception as e:
                print(f"Worker error: {str(e)}")
            finally:
                email_queue.task_done()


# Start email processing thread
email_thread = threading.Thread(target=email_worker, daemon=True)
email_thread.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/campaign", methods=["POST"])
def create_campaign():
    data = request.json
    campaign = Campaign(name=data["name"], prompt=data["prompt"])
    db.session.add(campaign)
    db.session.commit()
    return jsonify({"id": campaign.id}), 201


@app.route("/api/upload/<int:campaign_id>", methods=["POST"])
def upload_data(campaign_id):
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    try:
        df = pd.read_csv(file)
        records = df.to_dict("records")

        # Create email records
        for record in records:
            email = Email(
                campaign_id=campaign_id, recipient=record["email"], meta_data=record
            )
            db.session.add(email)
        db.session.commit()

        # Queue emails for processing
        emails = Email.query.filter_by(campaign_id=campaign_id).all()
        for email in emails:
            email_queue.put(email.id)

        return jsonify({"message": "Processing started"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/campaign/<int:campaign_id>/status")
def campaign_status(campaign_id):
    emails = Email.query.filter_by(campaign_id=campaign_id)

    stats = {
        "total": emails.count(),
        "sent": emails.filter_by(status="SENT").count(),
        "pending": emails.filter_by(status="PENDING").count(),
        "failed": emails.filter_by(status="FAILED").count(),
    }

    return jsonify(stats)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
