from flask import Blueprint, request, jsonify
from app.supabase_client import supabase
from app.utils.supabase import get_supabase_client


auth_bp = Blueprint('auth', __name__)

supabase = get_supabase_client()

@auth_bp.route("/health", methods=["GET"])
def auth_health():
    return jsonify({"status": "Auth routes are working ✅"})

# ------------------------------------------------------
# SIGNUP ROUTE
# ------------------------------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        role = data.get("role")  # candidate / recruiter

        if not all([email, password, first_name, last_name, role]):
            return jsonify({"error": "All fields are required"}), 400

        # 1. Create user in Supabase Auth
        user = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if not user or not user.user:
            return jsonify({"error": "Supabase signup failed"}), 400

        uid = user.user.id  # Supabase UID

        # 2. Insert custom data into public.users
        response = supabase.table("users").insert({
            "auth_uid": uid,
            "first_name": first_name,
            "last_name": last_name,
            "role": role
        }).execute()

        return jsonify({
            "message": "User registered successfully",
            "auth_uid": uid
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------
# LOGIN ROUTE
# ------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        # 1. Login with Supabase Auth
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not user or not user.user:
            return jsonify({"error": "Invalid login credentials"}), 401

        uid = user.user.id

        # 2. Get user role + info from public.users
        user_data = supabase.table("users").select("*").eq("auth_uid", uid).execute()

        if not user_data.data:
            return jsonify({"error": "User not found in public.users"}), 404

        profile = user_data.data[0]

        return jsonify({
            "message": "Login successful",
            "access_token": user.session.access_token,
            "user": {
                "auth_uid": uid,
                "first_name": profile["first_name"],
                "last_name": profile["last_name"],
                "role": profile["role"],
                "email": user.user.email
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------
# TEST PROTECTED ROUTE
# ------------------------------------------------------
@auth_bp.route("/protected", methods=["GET"])
def protected_test():
    try:
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing token"}), 401

        token = auth_header.split(" ")[1]

        # Verify token with Supabase
        user = supabase.auth.get_user(token)

        if not user:
            return jsonify({"error": "Invalid token"}), 403

        return jsonify({
            "message": "Token is valid",
            "user_id": user.user.id,
            "email": user.user.email
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Get Profile
# @auth_bp.route('/profile/<user_id>', methods=['GET'])
# def profile(user_id):
#     try:
#         response = supabase.table('users').select('*').eq('id', user_id).single().execute()
#         if response.data is None:
#             return jsonify({"error": "User not found"}), 404
#         return jsonify(response.data), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

@auth_bp.route('/profile/<auth_uid>', methods=['GET'])
def profile(auth_uid):
    try:
        response = supabase.table('users').select('*').eq('auth_uid', auth_uid).single().execute()
        if response.data is None:
            return jsonify({"error": "User not found"}), 404
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    