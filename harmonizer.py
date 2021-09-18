from flask import (
    Flask,
    render_template,
    request,
    flash,
    abort,
    session,
    redirect,
    url_for,
    make_response,
    jsonify,
)
from flask_cors import CORS
import json
import requests
import random
import urllib.parse
from cas import CASClient
import sys
from auth_search import grab_lc, manual_grab_lc
from mongodb import (
    user_lookup,
    jobs_lookup,
    insert_coll_job,
    insert_item_job,
    single_job_lookup,
    kill_job,
    kill_rec_from_job,
    get_tokens,
)
from api_helpers import (
    get_colls,
    retrieve_coll_meta,
    retrieve_item_meta,
    retrieve_term_meta,
    cookie_monster,
    send_term_updates,
)

cd = sys.path[0]
with open(f"{cd}/auth.json", "r") as j:
    auth = json.load(j)

# flask initalization
appy = Flask(__name__)
appy.config["DEBUG"] = auth["debug"]
appy.config["SECRET_KEY"] = auth["SECRET_KEY"]
base_url = auth["base_url"]

# CAS setup
cas_service_url = base_url + auth["cas_service_url"]
cas_client = CASClient(
    version=2, service_url=cas_service_url, server_url="https://weblogin.asu.edu/cas/"
)

# limit CORS requests to APIs created in this flask instance
cors = CORS(appy, resources={r"/subspace/*": {"origins": base_url}})

logo_list = [
    "logo-1.png",
    "logo-2.png",
    "logo-3.png",
    "logo-4.png",
    "logo-5.png",
    "logo-6.png",
    "logo-7.png",
    "logo-8.png",
]

## ERROR HANDLING
# generic you're-not-allowed-to-access-that:
@appy.errorhandler(403)
def forbidden(e):
    return render_template("forbidden.html"), 403


## CAS AUTHENTICATION
@appy.route("/login")
def login():
    # Already logged in
    if "username" in session:
        return redirect(url_for("dashboard"))

    next = request.args.get("next")
    ticket = request.args.get("ticket")

    # No ticket, the request came from end user, send to CAS login:
    if not ticket:
        cas_login_url = cas_client.get_login_url()
        return redirect(cas_login_url)

    # There IS a ticket, the request come from CAS as callback.
    # need call `verify_ticket()` to validate ticket and get user profile.
    user, attributes, pgtiou = cas_client.verify_ticket(ticket)

    if not user:
        return 'Failed to verify ticket. <a href="/login">Login</a>'
    else:
        # Login successful, redirect according to `next` query parameter.
        session["username"] = user
        return redirect(next)


@appy.route("/")
def index():
    return redirect(url_for("login"))


@appy.route("/logout")
def logout():
    redirect_url = url_for("logout_callback", _external=True)
    cas_logout_url = cas_client.get_logout_url(redirect_url)
    session.clear()
    return redirect(cas_logout_url)


@appy.route("/logout_callback")
def logout_callback():
    # redirect from CAS logout request after CAS logout successfully
    session.pop("username", None)
    return 'Logged out from CAS. <a href="/login">Login</a>'


## MAIN PAGES
@appy.route("/dashboard", methods=["GET"])
def dashboard():
    if "username" in session:
        resp = make_response(
            render_template(
                "home.html",
                title="Home | Harmonizer",
                loggedin=True,
                user=session["username"],
                logo=(random.choice(logo_list)),
            )
        )
        resp = cookie_monster(request, resp)
        return resp
    else:
        return redirect(url_for("login"))


@appy.route("/keep-single", methods=["GET"])
def keep_single():
    if "username" in session:
        resp = make_response(
            render_template(
                "single.html",
                title="Edit a Single KEEP Term | Harmonizer",
                kind="keep",
                loggedin=True,
                user=session["username"],
                logo=(random.choice(logo_list)),
            )
        )
        resp = cookie_monster(request, resp)
        return resp
    else:
        return redirect(url_for("login"))


@appy.route("/prism-single", methods=["GET"])
def prism_single():
    if "username" in session:
        resp = make_response(
            render_template(
                "single.html",
                title="Edit a Single PRISM Term | Harmonizer",
                kind="prism",
                loggedin=True,
                user=session["username"],
                logo=(random.choice(logo_list)),
            )
        )
        resp = cookie_monster(request, resp)
        return resp
    else:
        return redirect(url_for("login"))


@appy.route("/my-jobs", methods=["GET"])
def my_jobs():
    if "username" in session:
        user_data = user_lookup(session["username"])
        job_recs = jobs_lookup(user_data)
        resp = make_response(
            render_template(
                "user-jobs.html",
                title="My Jobs | Harmonizer",
                loggedin=True,
                user=session["username"],
                logo=(random.choice(logo_list)),
                jobs=job_recs,
            )
        )
        resp = cookie_monster(request, resp)
        return resp
    else:
        return redirect(url_for("login"))


@appy.route("/run-jobs", methods=["GET"])
def run_jobs():
    if "username" in session:
        resp = make_response(
            render_template(
                "run-jobs.html",
                title="Run a Job | Harmonizer",
                loggedin=True,
                user=session["username"],
                colls=(get_colls()),
                logo=(random.choice(logo_list)),
            )
        )
        resp = cookie_monster(request, resp)
        return resp
    else:
        return redirect(url_for("login"))


@appy.route("/single-job/<input_user>/<job_id>/<rec>", methods=["GET"])
def view_job_record(input_user, job_id, rec):
    if "username" in session:
        session_username = session["username"]
        if input_user == session_username:
            user_data = user_lookup(session_username)
            job = single_job_lookup(user_data, job_id)
            if job is not None:
                index_number = int(rec) - 1
                try:
                    chosen_record = job["docs"][index_number]
                except:
                    redirect_rec_index = len(job["docs"])
                    if redirect_rec_index > 0:
                        return redirect(
                            f"/single-job/{input_user}/{job_id}/{redirect_rec_index}"
                        )
                    else:
                        flash(f"Sorry, no more records to left in job #{job_id}.")
                        return redirect(url_for("my_jobs"))
                else:
                    if len(job["docs"]) == int(rec):
                        last = True
                    else:
                        last = False

                    if index_number == 0:
                        first = True
                    else:
                        first = False

                    next = int(rec) + 1
                    prev = int(rec) - 1

                    resp = make_response(
                        render_template(
                            "single-job.html",
                            title=f"Job {job_id}, Term ID# {chosen_record} | Harmonizer",
                            loggedin=True,
                            user=session["username"],
                            logo=(random.choice(logo_list)),
                            rec=chosen_record,
                            kind=job["repo"],
                            job_id=job_id,
                            last=last,
                            first=first,
                            next=next,
                            prev=prev,
                        )
                    )
                    resp = cookie_monster(request, resp)
                    return resp
            else:
                flash(f"Sorry, I couldn't find job #{job_id}.")
                return redirect(url_for("dashboard"))
        else:
            return render_template("forbidden-job.html")
    else:
        return redirect(url_for("login"))


## SUBSPACE
# specific API endpoints supporting the above main pages
@appy.route("/subspace/lc/<search>", methods=["GET"])
def exl_item(search):
    results = grab_lc(urllib.parse.unquote(search))
    if results is not None:
        return jsonify({"status": "success", "results": results}), 200
    else:
        return jsonify({"status": "No results"}), 200


@appy.route("/subspace/colls", methods=["GET"])
def colls():
    results = get_colls()
    return jsonify(results), 200


@appy.route("/subspace/coll-metadata", methods=["POST"])
def coll_metadata():
    data = request.get_json()
    meta = retrieve_coll_meta(data["repo_name"], data["col_id"])
    if meta is not None:
        user_rec = user_lookup(data["username"])
        new_job = insert_coll_job(user_rec, meta, data)
        if new_job is not None:
            return jsonify(new_job), 200
        else:
            return jsonify("Error creating new job"), 500
    else:
        return jsonify({"status": "empty"}), 200


@appy.route("/subspace/item-metadata", methods=["POST"])
def item_metadata():
    data = request.get_json()
    meta_data, meta_status = retrieve_item_meta(data["repo_name"], data["item_id"])
    if meta_data is not None:
        user_rec = user_lookup(data["username"])
        new_job = insert_item_job(user_rec, meta_data, data)
        if new_job is not None:
            return jsonify(new_job), 200
        else:
            return jsonify("Error creating new job"), 500
    else:
        return jsonify({"status": f"Solr search for item returned {meta_status}."}), 200


@appy.route("/subspace/delete_job", methods=["POST"])
def delete_job():
    data_package = request.get_json()
    user_data = user_lookup(data_package["user"])
    result = kill_job(user_data, data_package)
    if result:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "fail"}), 500


@appy.route("/subspace/delete_rec_from_job", methods=["POST"])
def delete_rec_from_job():
    data_package = request.get_json()
    user_data = user_lookup(data_package["user"])
    result = kill_rec_from_job(
        user_data, data_package["job_id"], data_package["rec_id"]
    )
    if result:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "fail"}), 500


@appy.route("/subspace/update_repo_term", methods=["POST"])
def update_repo_term():
    data_package = request.get_json()
    result, term_data = retrieve_term_meta(
        data_package["repo_name"], data_package["term_id"]
    )
    if result:
        next_result, status_code = send_term_updates(term_data, data_package)
        if next_result:
            return jsonify({"status": "success"}), 200
        else:
            return (
                jsonify(
                    {"status": "fail", "response": f"Failed with code {status_code}"}
                ),
                500,
            )
    else:
        return jsonify({"status": "fail", "response": term_data}), 500


@appy.route("/subspace/lc-manual-search", methods=["POST"])
def lc_manual_search():
    data_package = request.get_json()
    result, resp = manual_grab_lc(data_package["uri"])
    if result:
        return jsonify({"status": "success", "response": resp}), 200
    else:
        return (
            jsonify({"status": "fail", "response": f"Failed with code {resp}"}),
            500,
        )


if __name__ == "__main__":
    appy.run()
