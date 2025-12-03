from functools import wraps
from flask import request, jsonify
from app.utils.supabase import supabase  # Assuming you already have a Supabase client setup

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token is missing"}), 401

        try:
            # Extract token: "Bearer <token>"
            token = auth_header.split(" ")[1]

            # Validate token with Supabase Auth
            auth_resp = supabase.auth.get_user(token)

            if not auth_resp or not auth_resp.user:
                return jsonify({"error": "Invalid or expired token"}), 403

            auth_uid = auth_resp.user.id  # UID from Supabase Auth

            # Fetch user from custom users table by auth_uid
            user_resp = (
                supabase
                .table("users")
                .select("*")
                .eq("auth_uid", auth_uid)
                .single()
                .execute()
            )

            if not user_resp.data:
                return jsonify({"error": "User not found in users table"}), 404

            user = user_resp.data
            user["email"] = auth_resp.user.email
            user["auth_uid"] = auth_uid

        except Exception as e:
            return jsonify({"error": f"Auth failed: {str(e)}"}), 403

        return f(user, *args, **kwargs)

    return decorated
