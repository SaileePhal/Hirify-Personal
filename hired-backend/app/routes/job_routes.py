from flask import Blueprint, jsonify, request
from app.utils.supabase import supabase
from app.middlewares.auth_middleware import token_required

job_bp = Blueprint("job_bp", __name__)

# ---------------------------------------------
# Pagination Helper
# ---------------------------------------------
def _get_pagination_params():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
    except:
        page, page_size = 1, 10

    page = max(page, 1)
    page_size = max(page_size, 1)

    return page, page_size


# ---------------------------------------------
# Health Check
# ---------------------------------------------
@job_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Jobs routes working ✅"}), 200


# ---------------------------------------------
# 1. CREATE JOB (Recruiter only)
# ---------------------------------------------
@job_bp.route("/create", methods=["POST"])
@token_required
def create_job(user):
    if user.get("role") != "recruiter":
        return jsonify({"error": "Only recruiters can post jobs"}), 403

    try:
        data = request.get_json() or {}

        required_fields = [
            "title", "company_name", "location", "job_type",
            "salary_range", "experience_level", "skills_required"
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"{field} is required"}), 400

        job_data = {
            "recruiter_id": user["auth_uid"],
            "title": data["title"],
            "company_name": data["company_name"],
            "location": data["location"],
            "job_type": data["job_type"],
            "salary_range": data["salary_range"],
            "experience_level": data["experience_level"],
            "description": data.get("description"),
            "skills_required": data["skills_required"],
            "application_deadline": data.get("application_deadline")
        }

        response = supabase.table("jobs").insert(job_data).execute()

        if response.data:
            return jsonify({"message": "Job posted successfully", "job": response.data[0]}), 201

        return jsonify({"error": response.error or "Failed to create job"}), 500

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# # ---------------------------------------------
# # 2. GET ALL JOBS (Paginated)
# # ---------------------------------------------
# @job_bp.route("/", methods=["GET"])
# def get_all_jobs():
#     try:
#         page, page_size = _get_pagination_params()
#         offset = (page - 1) * page_size
#         to_index = offset + page_size - 1

#         jobs_resp = supabase.table("jobs").select("*").order("created_at", desc=True).range(offset, to_index).execute()

#         total_resp = supabase.table("jobs").select("id", count="exact").execute()
#         total = total_resp.count or 0

#         return jsonify({
#             "page": page,
#             "page_size": page_size,
#             "total": total,
#             "jobs": jobs_resp.data or []
#         }), 200

#     except Exception as e:
#         return jsonify({"error": f"Failed to fetch jobs: {str(e)}"}), 500





# ---------------------------------------------
# 2. GET ALL JOBS (Alternative 1: Single-Field Search)
# ---------------------------------------------
@job_bp.route("/", methods=["GET"])
def get_all_jobs():
    try:
        page, page_size = _get_pagination_params()
        offset = (page - 1) * page_size
        to_index = offset + page_size - 1

        search_query = request.args.get('q')
        
        # 1. Start with the base query
        query = supabase.table("jobs").select("*", count="exact")

        # 2. Apply search filter only to the 'title' field
        if search_query:
            search_pattern = f"%{search_query}%"
            
            # Use the simple .ilike() for one column.
            # This is less likely to break than .raw_filter() or .or_().
            query = query.ilike("title", search_pattern)
            
            # NOTE: If ilike is not available, try eq():
            # query = query.eq("title.ilike", search_pattern)

        # 3. Execute the combined query (Data + Count)
        response = (
            query
            .order("created_at", desc=True)
            .range(offset, to_index)
            .execute()
        )
        
        total = response.count or 0
        jobs_data = response.data or []
        
        return jsonify({
            "page": page,
            "page_size": page_size,
            "total": total,
            "jobs": jobs_data
        }), 200

    except Exception as e:
        print(f"Server Error during get_all_jobs: {e}") 
        return jsonify({"error": f"Failed to fetch jobs due to a server error: {str(e)}"}), 500


# ---------------------------------------------
# 3. GET A SINGLE JOB
# ---------------------------------------------
@job_bp.route("/<job_id>", methods=["GET"])
def get_job_by_id(job_id):
    try:
        response = supabase.table("jobs").select("*").eq("id", job_id).single().execute()
        if not response.data:
            return jsonify({"error": "Job not found"}), 404

        return jsonify({"job": response.data}), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch job: {str(e)}"}), 500


# ---------------------------------------------
# 4. GET JOBS POSTED BY RECRUITER (Paginated)
# ---------------------------------------------
@job_bp.route("/my-jobs", methods=["GET"])
@token_required
def get_my_jobs(user):
    if user.get("role") != "recruiter":
        return jsonify({"error": "Only recruiters can view this"}), 403

    try:
        page, page_size = _get_pagination_params()
        offset = (page - 1) * page_size
        to_index = offset + page_size - 1

        jobs_resp = (
            supabase.table("jobs")
            .select("*")
            .eq("recruiter_id", user["auth_uid"])
            .order("created_at", desc=True)
            .range(offset, to_index)
            .execute()
        )

        total_resp = (
            supabase.table("jobs")
            .select("id", count="exact")
            .eq("recruiter_id", user["auth_uid"])
            .execute()
        )

        total = total_resp.count or 0

        return jsonify({
            "page": page,
            "page_size": page_size,
            "total": total,
            "jobs": jobs_resp.data or []
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to fetch recruiter jobs: {str(e)}"}), 500


# ---------------------------------------------
# 5. UPDATE JOB
# ---------------------------------------------
@job_bp.route("/<job_id>", methods=["PUT"])
@token_required
def update_job(user, job_id):
    if user.get("role") != "recruiter":
        return jsonify({"error": "Only recruiters can update jobs"}), 403

    try:
        job_check = supabase.table("jobs").select("recruiter_id").eq("id", job_id).single().execute()

        if not job_check.data:
            return jsonify({"error": "Job not found"}), 404

        if job_check.data["recruiter_id"] != user["auth_uid"]:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json() or {}
        update_data = {k: v for k, v in data.items() if v is not None}

        response = supabase.table("jobs").update(update_data).eq("id", job_id).execute()

        if response.data:
            return jsonify({"message": "Job updated successfully", "job": response.data[0]}), 200

        return jsonify({"error": "Failed to update job"}), 500

    except Exception as e:
        return jsonify({"error": f"Update failed: {str(e)}"}), 500


# ---------------------------------------------
# 6. DELETE JOB
# ---------------------------------------------
@job_bp.route("/<job_id>", methods=["DELETE"])
@token_required
def delete_job(user, job_id):
    if user.get("role") != "recruiter":
        return jsonify({"error": "Only recruiters can delete jobs"}), 403

    job_check = supabase.table("jobs").select("recruiter_id").eq("id", job_id).single().execute()

    if not job_check.data:
        return jsonify({"error": "Job not found"}), 404

    if job_check.data["recruiter_id"] != user["auth_uid"]:
        return jsonify({"error": "Unauthorized"}), 403

    supabase.table("jobs").delete().eq("id", job_id).execute()

    return jsonify({"message": "Job deleted successfully"}), 200

