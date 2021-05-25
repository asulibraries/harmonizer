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
from auth_search import grab_lc
import urllib.parse


with open("auth.json", "r") as j:
    auth = json.load(j)

# flask initalization
application = Flask(__name__)
application.config["DEBUG"] = auth["debug"]
application.config["SECRET_KEY"] = auth["SECRET_KEY"]
cors = CORS(application, resources={r"/subspace/*": {"origins": "*"}})


@application.route("/", methods=["GET"])
def dashboard():
    resp = make_response(render_template("home.html", title="Home | Harmonizer"))
    existing_cookie = request.cookies.get("cromulent")
    if not existing_cookie:
        rando = f"macclure-{random.randint(1,1000)}"
        print(rando)
        resp.set_cookie("cromulent", rando, max_age=300, samesite="None", secure=True)
    return resp


@application.route("/keep-single", methods=["GET"])
def keep_single():
    resp = make_response(
        render_template(
            "keep-single.html", title="Edit a Single KEEP Term | Harmonizer"
        )
    )
    existing_cookie = request.cookies.get("cromulent")
    if not existing_cookie:
        rando = f"macclure-{random.randint(1,1000)}"
        print(rando)
        resp.set_cookie(
            "cromulent", rando, max_age=300, samesite="None", secure=True,
        )
    return resp


@application.route("/prism-single", methods=["GET"])
def prism_single():
    resp = make_response(
        render_template(
            "prism-single.html", title="Edit a Single PRISM Term | Harmonizer"
        )
    )
    existing_cookie = request.cookies.get("cromulent")
    if not existing_cookie:
        rando = f"macclure-{random.randint(1,1000)}"
        print(rando)
        resp.set_cookie(
            "cromulent", rando, max_age=300, samesite="None", secure=True,
        )
    return resp


@application.route("/subspace/lc/<search>", methods=["GET"])
def exl_item(search):
    results = grab_lc(urllib.parse.unquote(search))
    if results is not None:
        return jsonify({"status": "success", "results": results}), 200
    else:
        return jsonify({"status": "No results"}), 200


if __name__ == "__main__":
    application.run()
