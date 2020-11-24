#!/usr/env python3

from flask import Flask, redirect
import logging

from reports import dbchangelog as dbchangelogreport
from reports import pullrequests as prsreport
from reports.config import ServicesData, Constants

logger = logging.getLogger(__name__)
logging.basicConfig(format=Constants.LOG_FORMAT)
logger.setLevel(logging.DEBUG)

services_data = ServicesData()

app = Flask(__name__)


@app.route("/", methods=["GET"])
def main():
    return redirect(Constants.CACHED_VERSIONS_REPORT)


@app.route("/service-versions", methods=['GET'])
def refresh():
    file = "/tmp/environments-report.html"
    prsreport.create_report(file, services_data)
    with open(file, 'r') as file:
        return file.read()


@app.route("/dbchangelogs/diff/<version>", methods=["GET"])
def get_dbchangelogs_diff(version):

    file = "/tmp/migrations-report.html"
    dbchangelogreport.create_report(file, version, services_data)
    with open(file, "r") as file:
        return file.read()


if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
