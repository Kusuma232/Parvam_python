import re


text = "My email is test@example.com and my phone number is 9876543210."

emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
phone_numbers = re.findall(r"\b\d{10}\b", text)

print("Emails:", emails)
print("Phone Numbers:", phone_numbers)
