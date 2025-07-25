
import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv

from langchain_core.pydantic_v1 import BaseModel as LangChainBaseModel, Field


load_dotenv()

# --- Configuration ---
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

class EmailContent(LangChainBaseModel):
    """Represents the content of a single fetched email."""
    sender: str = Field(description="The sender of the email.")
    subject: str = Field(description="The subject line of the email.")
    body: str = Field(description="The plain text body of the email.")

# --- Core Email Fetching Logic ---
def fetch_recent_emails(limit: int = 5) -> list[EmailContent]:
    """
    Connects to the IMAP email server and fetches the most recent emails.
    """
    if not EMAIL or not PASSWORD:
        print("ERROR: Email credentials not found in .env file.")
        return [EmailContent(sender="Configuration Error", subject="Missing Credentials", body="Please set EMAIL and EMAIL_PASSWORD in your .env file.")]

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, 'ALL')
        if status != "OK":
            return [EmailContent(sender="IMAP Error", subject="Could not search inbox.", body="")]

        email_ids = messages[0].split()
        if not email_ids:
            return [EmailContent(sender="Info", subject="No emails found", body="Your inbox is empty.")]
            
        recent_email_ids = email_ids[-limit:]

        emails = []
        for eid in reversed(recent_email_ids):
            _, data = mail.fetch(eid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            subject, encoding = decode_header(msg.get("Subject", "(No Subject)"))[0]
            if isinstance(subject, bytes): subject = subject.decode(encoding or "utf-8", errors="ignore")

            from_, encoding = decode_header(msg.get("From", "(No Sender)"))[0]
            if isinstance(from_, bytes): from_ = from_.decode(encoding or "utf-8", errors="ignore")

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition")):
                        payload = part.get_payload(decode=True)
                        if payload: body = payload.decode(errors="ignore")
                        break
            else:
                payload = msg.get_payload(decode=True)
                if payload: body = payload.decode(errors="ignore")

            emails.append(EmailContent(sender=from_, subject=subject, body=body.strip()))

        mail.logout()
        return emails

    except Exception as e:
        print(f"Error fetching emails: {e}")
        error_body = "Could not connect to the email server. Please check the credentials in the .env file and ensure IMAP access is enabled for the account."
        # This provides a much more helpful error directly to the user
        if "AUTHENTICATIONFAILED" in str(e):
            error_body = "Email login failed. For Gmail, you MUST use a special 16-digit 'App Password', not your regular password. Please check your .env file."
        return [EmailContent(sender="Fatal Error", subject="Failed to Connect", body=error_body)]