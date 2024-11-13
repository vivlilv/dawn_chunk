import imaplib
import email
from email.header import decode_header
import imaplib
import email
from email.header import decode_header
import re


def decode_if_bytes(value, encoding="utf-8"):
    if isinstance(value, bytes):
        try:
            return value.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback to default encoding if UTF-8 fails
            try:
                return value.decode("latin-1")  # Common fallback encoding
            except:
                return value.decode(errors="ignore")  # Ignore undecodable bytes
    return value


def get_email_body(email_message):
    # Check if the email message is multipart
    if email_message.is_multipart():
        # Iterate through each part of the email
        for part in email_message.walk():
            # If the content type is text/plain or text/html, we extract the body
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            # Check if the part is either text/plain or text/html
            if content_type == "text/plain" or content_type == "text/html":
                try:
                    # Get the email body
                    body = part.get_payload(decode=True)
                    return decode_if_bytes(body)
                except Exception as e:
                    print(f"Failed to decode part: {e}")
                    return None
    else:
        # If it's not multipart, extract the payload (the body)
        try:
            body = email_message.get_payload(decode=True)
            return decode_if_bytes(body)
        except Exception as e:
            print(f"Failed to decode body: {e}")
            return None


def fetch_emails_from_folder(imap, folder, target_sender):
    imap.select(folder)

    print(f"\nSearching for emails from {target_sender} in {folder}...")
    _, all_messages = imap.search(None, "ALL")
    all_messages = all_messages[0].split()

    # Process each email
    for num in all_messages:
        _, msg_data = imap.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                email_body = response_part[1]
                email_message = email.message_from_bytes(email_body)

                # Extract sender
                sender = decode_header(email_message.get("From", ""))[0][0]
                sender = decode_if_bytes(sender)

                # Check if the sender matches the target sender
                if target_sender in sender:
                    # Extract subject
                    subject = decode_header(email_message.get("Subject", ""))[0][0]
                    subject = decode_if_bytes(subject)

                    # Extract date
                    date = email_message.get("Date", "")

                    # Extract the body
                    body = get_email_body(email_message)

                    return body


def get_specific_email_senders(username, password, target_sender):
    # Connect to the IMAP server
    imap_server = "outlook.office365.com"
    imap = imaplib.IMAP4_SSL(imap_server)

    try:
        # Login to the server
        imap.login(username, password)

        body = fetch_emails_from_folder(imap, "Junk", target_sender)
        # if body is None:
        #     # If not found in Junk, try Inbox
        #     body = fetch_emails_from_folder(imap, "INBOX", target_sender)

    except imaplib.IMAP4.error as e:
        print(f"An IMAP error occurred: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        try:
            imap.close()
            imap.logout()
            return body
        except:
            pass


def extract_link_from_body(body):
    pattern = r'class="maillink">(https?://[^\s]+)</a></p>'
    match = re.search(pattern, body)
    if match:
        return match.group(1)
    return None


def get_verification_link(username,password, target_sender="hello@dawninternet.com"):
    body = get_specific_email_senders(username, password, target_sender)
    link = extract_link_from_body(body)
    print(f"Extracted link: {link}")
    return link
