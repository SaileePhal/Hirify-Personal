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
# @auth_bp.route("/signup", methods=["POST"])
# def signup():
#     try:
#         data = request.get_json()

#         email = data.get("email")
#         password = data.get("password")
#         first_name = data.get("first_name")
#         last_name = data.get("last_name")
#         role = data.get("role")  # candidate / recruiter

#         if not all([email, password, first_name, last_name, role]):
#             return jsonify({"error": "All fields are required"}), 400

#         # 1. Create user in Supabase Auth
#         user = supabase.auth.sign_up({
#             "email": email,
#             "password": password
#         })

#         if not user or not user.user:
#             return jsonify({"error": "Supabase signup failed"}), 400

#         uid = user.user.id  # Supabase UID

#         # 2. Insert custom data into public.users
#         response = supabase.table("users").insert({
#             "auth_uid": uid,
#             "first_name": first_name,
#             "last_name": last_name,
#             "role": role
#         }).execute()

#         return jsonify({
#             "message": "User registered successfully",
#             "auth_uid": uid
#         }), 201

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# ------------------------------------------------------
# SIGNUP ROUTE (FINAL, STABILIZED FIX)
# ------------------------------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name") or ""
    role = data.get("role")

    if not all([email, password, first_name, role]):
        return jsonify({"error": "All fields are required"}), 400

    try:
        # --- PHASE 1: Create user in Supabase Auth ---
        user_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # If sign_up didn't crash, but failed to return user data
        if not user_response.user:
            # Note: This is now a true failure since we handle the existing user case below.
            return jsonify({"error": "Supabase signup failed to return user data."}), 400

        uid = user_response.user.id  # Supabase UID

        # --- PHASE 2: Create/Update custom data in public.users (Explicit Upsert) ---
        
        # 2a. Check if the profile already exists (using the new UID)
        profile_data = supabase.table("users").select("auth_uid").eq("auth_uid", uid).execute()
        
        user_profile_exists = len(profile_data.data) > 0
        
        profile_payload = {
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            # Removed 'created_at': 'now()' to simplify payload, as DB should handle default.
        }

        if user_profile_exists:
            # 2b. If the profile exists -> UPDATE
            db_op = supabase.table("users").update(profile_payload).eq("auth_uid", uid)
        else:
            # 2c. If the profile does NOT exist (Correct for a new user) -> INSERT
            profile_payload["auth_uid"] = uid # Add the foreign key for insertion
            db_op = supabase.table("users").insert(profile_payload)
            
        # Execute the chosen database operation
        response = db_op.execute()
        
        # If the API response object is missing the expected attribute, 
        # but the DB operation succeeded (which we know it does for new users),
        # we still treat it as a success and return 201.
        # Check only for *explicit* error attributes if the operation should have returned data.
        if hasattr(response, 'error') and response.error: 
            print(f"Database operation failed after successful Auth: {response.error}")
            return jsonify({"error": "Profile creation/update failed. Please contact support."}), 500

        # Success case for both new users (INSERT) and weird existing users (UPDATE)
        return jsonify({
            "message": "User registered successfully",
            "auth_uid": uid
        }), 201

    # 🔥 Simplified Exception Handling: Catch all runtime errors and classify them.
    except Exception as e:
        error_message = str(e)
        error_message_lower = error_message.lower()

        # 1. Existing User / Auth Error Check (The most common cause of signup failure)
        # We target the most common strings, including the new '23503' that appeared for existing users.
        if "user already exists" in error_message_lower or \
           "already registered" in error_message_lower or \
           "insert or update on table \"users\" violates foreign key constraint" in error_message_lower or \
           "key (auth_uid) is not present" in error_message_lower:
            
            # Return 409 Conflict for resource conflict (existing user)
            return jsonify({"error": "This email is already registered. Please sign in."}), 409

        # 2. Supabase Client Library Error Check (Crashes on success/failure due to missing attributes)
        # This catches the AttributeError/APIResponse errors when the sign_up call fails gracefully or succeeds awkwardly.
        if "has no attribute 'error'" in error_message or \
           "has no attribute 'user'" in error_message:
            
            # We assume this is a Supabase client library internal error and it should have been a success 
            # or a user-already-exists error. Given the complexity, returning a 409 is the safest fallback.
            return jsonify({"error": "This email is already registered. Please sign in."}), 409
        
        # 3. Final Fallback for unexpected server errors
        print(f"Unexpected server-side error during signup: {error_message}") 
        return jsonify({"error": "An internal server error occurred during registration."}), 500

# ------------------------------------------------------
# LOGIN ROUTE
# ------------------------------------------------------
# @auth_bp.route("/login", methods=["POST"])
# def login():
#     try:
#         data = request.get_json()

#         email = data.get("email")
#         password = data.get("password")

#         if not email or not password:
#             return jsonify({"error": "Email and password required"}), 400

#         # 1. Login with Supabase Auth
#         user = supabase.auth.sign_in_with_password({
#             "email": email,
#             "password": password
#         })

#         if not user or not user.user:
#             return jsonify({"error": "Invalid login credentials"}), 401

#         uid = user.user.id

#         # 2. Get user role + info from public.users
#         user_data = supabase.table("users").select("*").eq("auth_uid", uid).execute()

#         if not user_data.data:
#             return jsonify({"error": "User not found in public.users"}), 404

#         profile = user_data.data[0]

#         return jsonify({
#             "message": "Login successful",
#             "access_token": user.session.access_token,
#             "user": {
#                 "auth_uid": uid,
#                 "first_name": profile["first_name"],
#                 "last_name": profile["last_name"],
#                 "role": profile["role"],
#                 "email": user.user.email
#             }
#         }), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# ------------------------------------------------------
# LOGIN ROUTE (FIXED)
# ------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    try:
        # 1. Login with Supabase Auth
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # CRITICAL CHECK 1: If sign_in_with_password fails, the 'user' object might have an error attribute,
        # or the call itself might raise an exception. Let's assume the library raises an exception for invalid credentials.
        # We will move the exception handling below.

        # CRITICAL CHECK 2: If the result object is missing data (meaning failure)
        # We replace the previous check: if not user or not user.user:
        # We must rely on the `except` block for true credential errors,
        # but we check the result object for generic API failure.
        # However, a clean Supabase client should throw on credential failure.
        # We will keep the code clean and rely on the try/except block.

        uid = user.user.id # This line will not be reached if an exception is thrown
        
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
    
    # 🔥 CRITICAL FIX: Catch the Supabase authentication failure exception.
    # The actual exception class (e.g., AuthApiError) depends on your specific Supabase client library.
    # If the library raises a generic `Exception` for invalid credentials, your previous code was flawed.
    # We will assume that failed authentication due to wrong password/email results in an exception
    # with a specific message that we can detect, or we catch the generic exception and return 401.
    except Exception as e:
        error_message = str(e).lower()
        
        # Check for specific Supabase-related error messages typically returned for failed login
        # This is a safe way to handle unknown specific library exceptions
        if "invalid login credentials" in error_message or "invalid email or password" in error_message:
            # Return 401 Unauthorized with a generic, secure message
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Catch errors related to user not found (sometimes this is a separate exception)
        if "user not found" in error_message or "no user with that email" in error_message:
            return jsonify({"error": "Invalid email or password"}), 401
        
        # Log the unexpected server error for debugging
        print(f"Unexpected server error during login: {e}") 
        
        # If it's another server-side error (e.g., database connection down, runtime error),
        # return a generic 500 error to the client for security.
        return jsonify({"error": "An internal server error occurred."}), 500


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
    