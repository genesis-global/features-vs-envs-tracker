#!/usr/env python3

import requests
import xml.etree.ElementTree as ET
import itertools
import logging

from .config import Constants

logger = logging.getLogger(__name__)
logging.basicConfig(format=Constants.LOG_FORMAT)
logger.setLevel(logging.DEBUG)


def __load_db_changelog(project, branch, changelog_file):

    url = 'https://api.bitbucket.org/2.0/repositories/{}/{}/src/{}/{}'.format(
        Constants.ATLASSIAN_ORG_NAME, project, branch, changelog_file)
    logger.debug('URL to query:' + url)
    resp = requests.get(url, auth=(Constants.BITBUCKET_USER, Constants.BITBUCKET_API_KEY))

    return resp.text


def __get_migrations(changelog):

    root = ET.fromstring(changelog)
    migrations = []

    for item in root:
        migrations.append(item.attrib['file'])

    return migrations


def __compare_migrations(project, release_branch, changelog_file):
    devel_migrations = __get_migrations(__load_db_changelog(project, 'devel', changelog_file))
    release_migrations = __get_migrations(__load_db_changelog(project, release_branch, changelog_file))

    now_different = False
    to_remove = set()
    result = []
    for devel, release in itertools.zip_longest(devel_migrations, release_migrations, fillvalue=''):
        if devel != release or now_different:
            now_different = True
            result.append({'devel': devel, 'release': release, 'remove': devel in to_remove})

            if release != '':
                logger.debug("{} <====== {} [{}]".format(devel, release, devel in to_remove))
                to_remove.add(release)
            else:
                logger.debug("{} [{}]".format(devel, devel in to_remove))

    return result


def create_report(file, release_branch, services_data):
    app_data = services_data.services
    app_names = services_data.get_app_names_with_db()
    app_results = {}

    for app in app_names:
        changelog_file = services_data.services[app].general_config.changelog_file
        result = __compare_migrations(app_data[app].general_config.repo_name, release_branch, changelog_file)
        app_results[app] = result

    with open(file, 'w+') as out:
        out.write('<html><body>')
        for app in app_names:
            out.write('<h3>{}</h3>'.format(app))
            out.write('<table width="100%">')
            for result in app_results[app]:
                l_color = 'white'
                r_color = 'green'
                if result['remove']:
                    l_color = 'red'
                if result['release'] == '':
                    r_color = 'white'

                out.write('<tr><td bgcolor="{}" width="50%">{}</td><td bgcolor="{}" width="50%">{}</td></tr>'
                          .format(l_color, result['devel'], r_color, result['release']))
            out.write('</table>')
            out.write('<hr>')
        out.write('</body></html>')
