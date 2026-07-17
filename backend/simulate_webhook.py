import hashlib
import hmac
import json

import httpx

# Paste your real Paystack test secret key here (same one as in backend/.env).
# Do NOT commit this file or share it anywhere with the key filled in.
SECRET_KEY = "sk_test_PASTE_YOUR_KEY_HERE"

# Paste the reference you got back from /payments/initialize.
REFERENCE = "nmcn_b0fd22d0534c4fe392de26e87c2ea1b4"

payload = {"event": "charge.success", "data": {"reference": REFERENCE}}
body = json.dumps(payload).encode()
signature = hmac.new(SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()

response = httpx.post(
    "http://localhost:8000/payments/webhook",
    content=body,
    headers={"x-paystack-signature": signature, "Content-Type": "application/json"},
)
print(response.status_code, response.text)
