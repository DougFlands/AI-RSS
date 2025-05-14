from src.core.utils.config import get_env_variable
from src.core.models.email import send_email
from flask import Blueprint,  jsonify,  request
from flask_mail import  Message

email_bp = Blueprint("email", __name__, url_prefix="/mail")

@email_bp.route('/send', methods=['POST'])
def post_send_email():
    recipients = request.json.get("recipients")  # 收件人列表
    subject = request.json.get("subject")        # 邮件主题
    body = request.json.get("body")              # 邮件内容

    if not recipients or not subject or not body:
        return jsonify({"error": "Missing recipients, subject, or body"}), 400

    try:
        send_email(subject, recipients, body)
        return jsonify({"status": "success", "message": "Email sent successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500
    
