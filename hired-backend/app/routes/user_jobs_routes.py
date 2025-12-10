from flask import Blueprint, jsonify, request
from app.utils.supabase import supabase
from app.middlewares.auth_middleware import token_required

user_jobs_bp = Blueprint("user_jobs_bp", __name__)

# -------------------------
# Pagination helper
# -------------------------
def _get_pagination_params():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
    except Exception:
        page, page_size = 1, 10
    page = max(1, page)
    page_size = max(1, page_size)
    return page, page_size



# ---------------------------------------------
# Saved_Job Routes
# ---------------------------------------------




# ---------------------------------------------
# 1. SAVE A JOB (Candidate)
# POST /saved-jobs
# ---------------------------------------------
@user_jobs_bp.route("/saved-jobs", methods=["POST"])
@token_required
def save_job(user):
    if user.get("role") != "candidate":
        return jsonify({"error": "Only candidate can save jobs"}), 403

    data = request.get_json() or {}
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400

    try:
        existing = supabase.table("saved_jobs").select("*").eq("job_id", job_id).eq("user_id", user["auth_uid"]).execute()
        if existing.data:
            return jsonify({"message": "Job already saved", "saved_job": existing.data[0]}), 200

        saved_job = {"user_id": user["auth_uid"], "job_id": job_id}
        resp = supabase.table("saved_jobs").insert(saved_job).execute()
        if resp.data:
            return jsonify({"message": "Job saved successfully", "saved_job": resp.data[0]}), 201

        return jsonify({"error": "Failed to save job"}), 500

    except Exception as e:
        return jsonify({"error": f"Failed to save job: {str(e)}"}), 500


# ---------------------------------------------
# 2. GET ALL SAVED JOBS FOR USER (expanded + pagination)
# GET /saved-jobs?page=1&page_size=10
# ---------------------------------------------
@user_jobs_bp.route("/saved-jobs", methods=["GET"])
@token_required
def get_saved_jobs(user):
    if user.get("role") != "candidate":
        return jsonify({"error": "Only candidate can view saved jobs"}), 403

    page, page_size = _get_pagination_params()
    offset = (page - 1) * page_size
    to_index = offset + page_size - 1

    try:
        # select joined job fields (only few fields) to avoid FK issues
        saved_resp = (
            supabase.table("saved_jobs")
            .select("id, job_id, saved_at, jobs(recruiter_id, company_name, title)")
            .eq("user_id", user["auth_uid"])
            .order("saved_at", desc=True)
            .range(offset, to_index)
            .execute()
        )

        total_resp = supabase.table("saved_jobs").select("id", count="exact").eq("user_id", user["auth_uid"]).execute()
        total = getattr(total_resp, "count", None) or 0

        return jsonify({
            "page": page,
            "page_size": page_size,
            "total": total,
            "saved_jobs": saved_resp.data or []
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch saved jobs: {str(e)}"}), 500


# ---------------------------------------------
# 3. REMOVE A SAVED JOB
# DELETE /saved-jobs/<saved_job_id>
# ---------------------------------------------
@user_jobs_bp.route("/saved-jobs/<saved_job_id>", methods=["DELETE"])
@token_required
def remove_saved_job(user, saved_job_id):
    if user.get("role") != "candidate":
        return jsonify({"error": "Only candidate can remove saved jobs"}), 403

    try:
        #saved_job 's id is passed and not job_id
        resp = supabase.table("saved_jobs").delete().eq("id", saved_job_id).eq("user_id", user["auth_uid"]).execute()
        if not resp.data or len(resp.data) == 0:
            return jsonify({"error": "Saved job not found"}), 404

        return jsonify({"message": "Saved job removed"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to remove saved job: {str(e)}"}), 500






# ---------------------------------------------
# Applications Routes
# ---------------------------------------------




# ---------------------------------------------
# 4. APPLY FOR A JOB
# POST /applications
# body: { job_id, resume_url (optional), cover_letter (optional) }
# ---------------------------------------------
@user_jobs_bp.route("/applications", methods=["POST"])
@token_required
def apply_job(user):
    if user.get("role") != "candidate":
        return jsonify({"error": "Only candidate can apply for jobs"}), 403

    data = request.get_json() or {}
    job_id = data.get("job_id")
    if not job_id:
        return jsonify({"error": "job_id is required"}), 400
    resume_url= data.get("resume_url")
    if not resume_url:
        return jsonify({"error": "resume_url is required"}), 400

    try:
        existing = supabase.table("applications").select("*").eq("job_id", job_id).eq("candidate_id", user["auth_uid"]).execute()
        if existing.data:
            return jsonify({"message": "Already applied for this job", "application": existing.data[0]}), 200

        application = {
            "candidate_id": user["auth_uid"],
            "job_id": job_id,
            "resume_url": resume_url,
            "cover_letter": data.get("cover_letter"),
            "status": "applied"
        }

        resp = supabase.table("applications").insert(application).execute()
        if resp.data:
            return jsonify({"message": "Application submitted successfully", "application": resp.data[0]}), 201

        return jsonify({"error": "Failed to submit application"}), 500

    except Exception as e:
        return jsonify({"error": f"Failed to submit application: {str(e)}"}), 500


# ---------------------------------------------
# 5. GET ALL APPLICATIONS OF CANDIDATE (paginated)
# GET /applications?page=1&page_size=10
# ---------------------------------------------
@user_jobs_bp.route("/applications", methods=["GET"])
@token_required
def get_user_applications(user):
    if user.get("role") != "candidate":
        return jsonify({"error": "Only candidate can view their applications"}), 403

    page, page_size = _get_pagination_params()
    offset = (page - 1) * page_size
    to_index = offset + page_size - 1

    try:
        apps_resp = (
            supabase.table("applications")
            .select("id, job_id, resume_url, cover_letter, status, applied_at, jobs(recruiter_id, company_name, title)")
            .eq("candidate_id", user["auth_uid"])
            .order("applied_at", desc=True)
            .range(offset, to_index)
            .execute()
        )
        total_resp = supabase.table("applications").select("id", count="exact").eq("candidate_id", user["auth_uid"]).execute()
        total = getattr(total_resp, "count", None) or 0

        return jsonify({
            "page": page,
            "page_size": page_size,
            "total": total,
            "applications": apps_resp.data or []
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch applications: {str(e)}"}), 500


# ---------------------------------------------
# 6. GET ALL APPLICATIONS FOR RECRUITER (paginated)
# GET /applications/recruiter?page=1&page_size=10
# NOTE: Do NOT rely on PostgREST automatic relationship selection (users(*)). Instead
#       fetch candidate user info in a second call and attach it.
# ---------------------------------------------
# @user_jobs_bp.route("/applications/recruiter", methods=["GET"])
# @token_required
# def get_applications_for_recruiter(user):
#     if user.get("role") != "recruiter":
#         return jsonify({"error": "Only recruiters can view applications"}), 403

#     page, page_size = _get_pagination_params()
#     offset = (page - 1) * page_size
#     to_index = offset + page_size - 1

#     try:
#         # fetch job ids for this recruiter
#         jobs_resp = supabase.table("jobs").select("id").eq("recruiter_id", user["auth_uid"]).execute()
#         job_ids = [j["id"] for j in (jobs_resp.data or [])]

#         if not job_ids:
#             return jsonify({"page": page, "page_size": page_size, "total": 0, "applications": []}), 200

#         apps_resp = (
#             supabase.table("applications")
#             .select("id, job_id, candidate_id, resume_url, cover_letter, status, applied_at, jobs(company_name, title)")
#             .in_("job_id", job_ids)
#             .order("applied_at", desc=True)
#             .range(offset, to_index)
#             .execute()
#         )

#         # get total count for these jobs
#         total_resp = supabase.table("applications").select("id", count="exact").in_("job_id", job_ids).execute()
#         total = getattr(total_resp, "count", None) or 0

#         applications = apps_resp.data or []

#         # collect candidate ids and fetch basic user info in bulk (if users table exists)
#         candidate_ids = list({app["candidate_id"] for app in applications if app.get("candidate_id")})
#         candidates_map = {}
#         if candidate_ids:
#             try:
#                 users_resp = supabase.table("users").select("id, full_name, email").in_("id", candidate_ids).execute()
#                 for u in (users_resp.data or []):
#                     candidates_map[u["id"]] = {"id": u["id"], "full_name": u.get("full_name"), "email": u.get("email")}
#             except Exception:
#                 # If users table / relationship isn't present, skip enriching
#                 candidates_map = {}

#         # attach candidate info
#         for app in applications:
#             cid = app.get("candidate_id")
#             app["candidate"] = candidates_map.get(cid) if cid else None

#         return jsonify({
#             "page": page,
#             "page_size": page_size,
#             "total": total,
#             "applications": applications
#         }), 200

#     except Exception as e:
#         return jsonify({"error": f"Failed to fetch recruiter applications: {str(e)}"}), 500





# ---------------------------------------------
# 6. GET ALL APPLICATIONS FOR RECRUITER (paginated) (NEW FIXED VERSION)
# ---------------------------------------------
@user_jobs_bp.route("/applications/recruiter", methods=["GET"])
@token_required
def get_applications_for_recruiter(user):
    if user.get("role") != "recruiter":
        return jsonify({"error": "Only recruiters can view applications"}), 403

    page, page_size = _get_pagination_params()
    offset = (page - 1) * page_size
    to_index = offset + page_size - 1

    # 🔥 CRITICAL FIX 1: Read the optional job_id query parameter
    filter_job_id = request.args.get("job_id")
    
    try:
        # Determine the list of job IDs to filter by:
        
        # Scenario A: Filtering by a specific job ID passed in the URL
        if filter_job_id:
            # Check if the job actually belongs to the recruiter before proceeding
            job_check = supabase.table("jobs").select("id").eq("id", filter_job_id).eq("recruiter_id", user["auth_uid"]).execute()
            if not job_check.data:
                # If the job doesn't exist or doesn't belong to this recruiter, return empty list
                return jsonify({"page": page, "page_size": page_size, "total": 0, "applications": []}), 200
            
            job_ids = [filter_job_id] # Only filter by the specific ID
        
        # Scenario B: No job_id passed, fetch ALL jobs for this recruiter
        else:
            # fetch job ids for this recruiter
            jobs_resp = supabase.table("jobs").select("id").eq("recruiter_id", user["auth_uid"]).execute()
            job_ids = [j["id"] for j in (jobs_resp.data or [])]

        if not job_ids:
            return jsonify({"page": page, "page_size": page_size, "total": 0, "applications": []}), 200

        # 🔥 CRITICAL FIX 2: Apply the calculated job_ids list (which might contain only one ID)
        apps_query = (
            supabase.table("applications")
            .select("id, job_id, candidate_id, resume_url, cover_letter, status, applied_at, jobs(company_name, title)")
            .in_("job_id", job_ids) # Use the calculated job_ids
        )

        # Execute the paginated response
        apps_resp = (
            apps_query
            .order("applied_at", desc=True)
            .range(offset, to_index)
            .execute()
        )

        # get total count for these jobs (Use the same .in_() filter)
        total_resp = supabase.table("applications").select("id", count="exact").in_("job_id", job_ids).execute()
        total = getattr(total_resp, "count", None) or 0

        applications = apps_resp.data or []

        # ... (rest of the code for fetching candidate info remains the same)

        # collect candidate ids and fetch basic user info in bulk (if users table exists)
        # ... (This section remains unchanged)

        # attach candidate info
        # ... (This section remains unchanged)
        
        return jsonify({
            "page": page,
            "page_size": page_size,
            "total": total,
            "applications": applications
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch recruiter applications: {str(e)}"}), 500







# ---------------------------------------------
# 7. UPDATE APPLICATION (PATCH /applications/<id>)
# - recruiter: update status (selected, rejected, under-review)
# - candidate: update resume_url and/or cover_letter
# ---------------------------------------------
@user_jobs_bp.route("/applications/<application_id>", methods=["PATCH"])
@token_required
def update_application(user, application_id):
    data = request.get_json() or {}

    # --- recruiter updates status ---
    if user.get("role") == "recruiter":
        new_status = data.get("status")
        if not new_status:
            return jsonify({"error": "status is required for recruiter updates"}), 400

        try:
            app_check = supabase.table("applications").select("job_id").eq("id", application_id).single().execute()
            if not app_check.data:
                return jsonify({"error": "Application not found"}), 404

            job_id = app_check.data.get("job_id")
            job_check = supabase.table("jobs").select("recruiter_id").eq("id", job_id).single().execute()
            if not job_check.data or job_check.data.get("recruiter_id") != user["auth_uid"]:
                return jsonify({"error": "Unauthorized"}), 403

            upd_resp = supabase.table("applications").update({"status": new_status}).eq("id", application_id).execute()
            return jsonify({"message": "Application status updated", "application": upd_resp.data[0] if upd_resp.data else {}}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to update status: {str(e)}"}), 500

    # --- candidate updates resume/cover ---
    elif user.get("role") == "candidate":
        resume_url = data.get("resume_url")
        cover_letter = data.get("cover_letter")
        if not resume_url and cover_letter is None:
            return jsonify({"error": "resume_url or cover_letter required"}), 400

        try:
            app_check = supabase.table("applications").select("candidate_id").eq("id", application_id).single().execute()
            if not app_check.data or app_check.data.get("candidate_id") != user["auth_uid"]:
                return jsonify({"error": "Unauthorized"}), 403

            upd = {}
            if resume_url:
                upd["resume_url"] = resume_url
            if cover_letter is not None:
                upd["cover_letter"] = cover_letter

            upd_resp = supabase.table("applications").update(upd).eq("id", application_id).execute()
            return jsonify({"message": "Application updated", "application": upd_resp.data[0] if upd_resp.data else {}}), 200

        except Exception as e:
            return jsonify({"error": f"Failed to update application: {str(e)}"}), 500

    else:
        return jsonify({"error": "Unauthorized role"}), 403


# ---------------------------------------------
# 8. WITHDRAW APPLICATION
# DELETE /applications/<id>  (candidate only)
# ---------------------------------------------
@user_jobs_bp.route("/applications/<application_id>", methods=["DELETE"])
@token_required
def withdraw_application(user, application_id):
    if user.get("role") != "candidate":
        return jsonify({"error": "Only candidate can withdraw applications"}), 403

    try:
        app_check = supabase.table("applications").select("candidate_id").eq("id", application_id).single().execute()
        if not app_check.data or app_check.data.get("candidate_id") != user["auth_uid"]:
            return jsonify({"error": "Application not found or unauthorized"}), 404

        supabase.table("applications").delete().eq("id", application_id).execute()
        return jsonify({"message": "Application withdrawn"}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to withdraw application: {str(e)}"}), 500
