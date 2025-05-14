
import urllib.parse

def generate_mailto(region_email: str, subject: str, body: str) -> str:
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)
    return f"mailto:{region_email}?subject={encoded_subject}&body={encoded_body}"
