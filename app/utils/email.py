import os
from dotenv import load_dotenv
from fastapi import BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig

load_dotenv()

# SMTP Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("EMAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("EMAIL_APP_PASSWORD"),
    MAIL_FROM=os.getenv("EMAIL_USERNAME"),
    MAIL_SERVER=os.getenv("EMAIL_SERVER"),
    MAIL_PORT=int(os.getenv("EMAIL_PORT", 587)),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

async def send_otp_email(email: str, otp: str, background_tasks: BackgroundTasks):
    """
    Sends OTP to the registered email as a background task.
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
                <h2 style="color: #4A90E2;">Account Verification</h2>
                <p>Use the OTP below to verify your account. It is valid for <strong>5 minutes</strong>.</p>
                <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px;
                            text-align: center; padding: 15px; margin: 20px 0;
                            background: #f4f4f4; border: 1px dashed #4A90E2; border-radius: 5px;">
                    {otp}
                </div>
                <p style="color: #999; font-size: 13px;">If you didn't request this, ignore this email.</p>
            </div>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Your OTP Verification Code",
        recipients=[email],         # registered email goes here
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)  # sends in background