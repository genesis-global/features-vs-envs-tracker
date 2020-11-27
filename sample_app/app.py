#!/usr/env python3

from flask import Flask, jsonify
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s %(levelname)-8s [%(funcName)15s()] %(message)s")
logger.setLevel(logging.DEBUG)

app = Flask(__name__)


@app.route("/prod/dog-ui/initial-dev-versions.json", methods=['GET'])
def initial_dev_versions():
    return jsonify({
        "cat": "dev-0.0.122",
        "dog": "dev-0.0.32",
        "dog-ui": "dev-0.0.13",
    })


@app.route("/dev/cat/status", methods=["GET"])
def get_dev_cat_status():
    return jsonify({
        "appBuild": "dev-0.0.167",
        "gitCommitId": "a7d80b5d5ca0c075aab5289fb622d34339654b63",
        "gitBranch": "origin/devel",
        "gitCommitTime": "2020-11-25T14:04:30+0100"
    })


@app.route("/dev/dog/status", methods=["GET"])
def get_dev_dog_status():
    return jsonify({
        "appBuild": "dev-0.0.36",
        "gitCommitId": "4c004415419ef4c4e0d4bfaf736b89ce5e0e65de",
        "gitBranch": "origin/devel",
        "gitCommitTime": "2020-11-26T14:04:30+0100"
    })


@app.route("/dev/dog-ui/version.json", methods=["GET"])
def get_dev_dog_ui_status():
    return jsonify({
        "appBuild": "dev-0.0.15",
        "gitCommitId": "2517b828224158e208c5bc239674f66978a18290",
        "gitBranch": "origin/devel",
        "gitCommitTime": "2020-11-27T14:04:30+0100"
    })


@app.route("/prod/cat/status", methods=["GET"])
def get_prod_cat_status():
    return jsonify({
        "appBuild": "release-1.0.12",
        "gitCommitId": "1a31edbfff0ce04cf8f5ed24d5af441780a9159b",
        "gitBranch": "origin/release-1.0.0",
        "gitCommitTime": "2020-11-26T14:04:30+0100"
    })


@app.route("/prod/dog/status", methods=["GET"])
def get_prod_dog_status():
    return jsonify({
        "appBuild": "release-1.0.12",
        "gitCommitId": "9b1549d8fc9fa1fdf68430e6bf0db5094151c168",
        "gitBranch": "origin/release-1.0.0",
        "gitCommitTime": "2020-11-25T14:04:30+0100"
    })


@app.route("/prod/dog-ui/version.json", methods=["GET"])
def get_prod_dog_ui_status():
    return jsonify({
        "appBuild": "release-1.0.12",
        "gitCommitId": "90403a9bd51d25f97a09f10d44f02c46e1377f4a",
        "gitBranch": "origin/release-1.0.0",
        "gitCommitTime": "2020-11-27T14:04:30+0100"
    })


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8081)
