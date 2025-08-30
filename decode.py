import itsdangerous
import sys

def decode_flask_cookie(secret_key, cookie_str):
    """Decode a Flask session cookie"""
    serializer = itsdangerous.URLSafeTimedSerializer(
        secret_key,
        salt="cookie-session",
        serializer=itsdangerous.serializer.JSONSerializer(),
        signer=itsdangerous.signer.HMACAlgorithm(itdangerous.signer.SHA1)
    )
    
    try:
        data = serializer.loads(cookie_str)
        return data
    except Exception as e:
        print(f"Failed to decode: {e}")
        return None

if __name__ == "__main__":

    session_data = decode_flask_cookie("FLASK_SECRET_KEY", "eyJpc19hZG1pbiI6dHJ1ZX0.aLLyoQ.9mrUSGjYHqiLCnRXWxQ-UAc15H4")
    print("Decoded session:", session_data)
