#!/usr/env python3

import logging
import sys
import requests
from datetime import datetime
from cachetools import cached, TTLCache

from .tools import sort_versions
from .jira_helper import create_jira_link
from .config import Constants

logger = logging.getLogger(__name__)
logging.basicConfig(format=Constants.LOG_FORMAT)
logger.setLevel(logging.DEBUG)


def __get_base_versions_for_releases(services_data):
    response = {}
    for env, url in services_data.base_versions_urls.items():
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            response[env] = r.json()

        except requests.exceptions.RequestException as err:
            logger.exception(f"ENV: {env}")
            logger.exception(f"err {err}")

            response[env] = {app: 'unknown' for app in services_data.services.keys()}

    return response


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def __get_prs(url):
    logger.info("Getting prs for: {}".format(url))
    r = requests.get(url, auth=(Constants.BITBUCKET_USER, Constants.BITBUCKET_API_KEY))
    return r.json()


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def __get_tags(url):
    logger.info("Getting tags for: {}".format(url))
    r = requests.get(url, auth=(Constants.BITBUCKET_USER, Constants.BITBUCKET_API_KEY))
    return r.json()


def create_td_content(pr_data, env, service):
    def build_for_tag(tag):
        return tag[len(Constants.DEV_TAG_PREFIX):]

    jenkins_url = service.env_configs[env].build_system_url

    tags = pr_data['version'].split(',')
    tags_build_urls = {tag: jenkins_url.format(build_for_tag(tag)) for tag in tags}

    builds = ''
    for tag, jenkins_url in tags_build_urls.items():
        builds += ' <a href="{}">{}</a>'.format(jenkins_url, tag)

    content = '{} +   <a href="{}"> {} </a> ({}) [{}]'.format(
        create_jira_link(Constants.ATLASSIAN_ORG_NAME, pr_data['title']),
        pr_data['pr_link'],
        pr_data['hash'],
        pr_data['author'],
        builds,
        pr_data['version']
    )
    return content


def create_td_content_release(pr_data):
    versions = pr_data['version']
    if pr_data['version'] != '':
        versions = sort_versions(versions.split(','))

    content = '{} +   <a href="{}"> {} </a> ({}) {}'.format(
        create_jira_link(Constants.ATLASSIAN_ORG_NAME, pr_data['title']),
        pr_data['pr_link'],
        pr_data['hash'],
        pr_data['author'],
        versions
    )
    return content


def create_report(file, services_data):
    env_app_data = {}
    env_versions_deployed = {env: [] for env in services_data.envs}
    app_names = services_data.get_app_names()
    app_data = services_data.services

    for env in services_data.envs:
        logger.info('===================ENV=' + env + '========================')
        env_app_data[env] = {}
        for app_name in app_names:

            final_address = app_data[app_name].get_version_url(env)

            prs = {
                'appBuild': 'unknown',
                'gitCommitId': 'unknownunknownunknown',
                'gitCommitTime': 'unknown'
            }

            try:
                r = requests.get(final_address, timeout=5)
                r.raise_for_status()
                prs = r.json()
            except requests.exceptions.RequestException as err:
                logger.exception(f"ENV: {env} APP: {app_name}")
                logger.exception(f"err {err}")
                continue

            logger.debug("PRS: {}".format(prs))

            # assign default
            env_app_data[env][app_name] = {
                "build": "unknown",
                "commitId": "unknown",
                "found": False,
                "commitTime": "unknown"
            }

            try:
                build = prs['appBuild']
                env_versions_deployed[env].append(build)

                commit_id = prs['gitCommitId'][:12]
                commit_time = prs['gitCommitTime']

                env_app_data[env][app_name] = {
                    'build': build,
                    'commitId': commit_id,
                    'found': False,
                    'commitTime': commit_time
                }

                logger.info(f"{final_address}: build={build}, commit={commit_id}")

            except KeyError as err:
                logger.exception(f"ENV: {env}, APP: {app_name}")
                logger.exception(f"err {err}")

            logging.debug(env_app_data[env][app_name])

    prs_data = {}
    tags_for_commits = {}
    for app_name in app_names:
        env_prs = {}
        prs_data[app_name] = {}

        repo_app_name = app_data[app_name].general_config.repo_name
        for env in services_data.envs:
            prs_data[app_name][env] = []

            try:
                branch = services_data.get_base_branch(env, env_app_data[env][app_name]['build'])
                prs_query = 'state="MERGED" AND destination.branch.name="{}"'.format(branch)
                prs = __get_prs('{}/repositories/{}/{}/pullrequests?q={}'.format(Constants.BITBUCKET_API_URL,
                                                                                 Constants.ATLASSIAN_ORG_NAME,
                                                                                 repo_app_name, prs_query))
                env_prs[env] = prs

                tag_prefix = services_data.env_tag_prefix[env]
                tags_query = 'name~"{}"&sort=-target.date'.format(tag_prefix)
                tags = __get_tags('{}/repositories/{}/{}/refs/tags?q={}'.format(Constants.BITBUCKET_API_URL,
                                                                                Constants.ATLASSIAN_ORG_NAME,
                                                                                repo_app_name, tags_query))

                tags_for_commits[app_name] = {}
                for tag in tags['values']:
                    commit_id = tag['target']['hash'][:12]
                    if commit_id not in tags_for_commits[app_name]:
                        tags_for_commits[app_name][commit_id] = tag['name']
                    else:
                        tags_for_commits[app_name][commit_id] += ',{}'.format(tag['name'])

                pull_requests = env_prs[env]

                elements_number = min(pull_requests['pagelen'], pull_requests['size'])

                for v in pull_requests['values'][:elements_number]:
                    hash = v['merge_commit']['hash']
                    title = v['title']
                    author = v['author']['display_name']
                    version = ''
                    pr_link = v['links']['html']['href']

                    if hash in tags_for_commits[app_name]:
                        version = tags_for_commits[app_name][hash]

                    logger.info(f"""ENV: {env}, APP: {app_name}
                        HASH:      {hash}
                        COMMIT_ID: {env_app_data[env][app_name]['commitId']}
                        FOUND: {env_app_data[env][app_name]['found']}
                    """)
                    colour = 'lightgray'

                    if env_app_data[env][app_name] and hash == env_app_data[env][app_name]['commitId']:
                        env_app_data[env][app_name]['found'] = True
                    if env_app_data[env][app_name]['found']:
                        colour = 'green'

                    prs_data[app_name][env].append({'title': title, 'hash': hash, 'colour': colour, 'author': author,
                                                    'version': version, 'pr_link': pr_link})

            except Exception as err:
                logger.exception("Unexpected error:", sys.exc_info())
                prs_data[app_name][env].append({'title': 'unknown', 'hash': 'unknown', 'colour': 'red', 'author': 'unknown',
                                                'version': '', 'pr_link': 'unknown'})

    base_versions_for_envs = __get_base_versions_for_releases(services_data)

    with open(file, 'w+') as out:
        out.write('<html><body>')
        out.write('Generated at: {} (UTC)'.format(datetime.utcnow().isoformat()))
        for env in services_data.envs:
            apps_number = len(app_names)
            if env in services_data.release_envs:
                highest_version = sort_versions(env_versions_deployed[env])[0]
                out.write('<h3>{} latest global version:[{}]</h3>'.format(env, highest_version))
                out.write('<table>')
                out.write(('<tr>' + ('<th>{}</th>' * apps_number) + '</tr>').format(*app_names))

                first_row_values = []
                for app_name in app_names:
                    if app_name in env_app_data[env]:
                        first_row_values.append(env_app_data[env][app_name]['build'])
                        first_row_values.append(env_app_data[env][app_name]['commitTime'])
                        first_row_values.append(base_versions_for_envs[env][app_name])
                    else:
                        first_row_values.append('not available')
                        first_row_values.append('?')
                        first_row_values.append('?')

                row = ('<tr>'+('<td>Current version:{}, created:{}, base: {}</td>' * apps_number) + '</tr>').format(*first_row_values)
                out.write(row)
            else:
                out.write('<h3>{}</h3>'.format(env))
                out.write('<table>')
                out.write(('<tr>' + ('<th>{}</th>' * apps_number) + '</tr>').format(*app_names))

                first_row_values = []
                for app_name in app_names:
                    first_row_values.append(env_app_data[env][app_name]['build'])
                    first_row_values.append(env_app_data[env][app_name]['commitTime'])

                row = ('<tr>'+('<td>Current version:{}, created:{}</td>' * apps_number) + '</tr>').format(*first_row_values)
                out.write(row)

            for i in range(10):
                row_values = []
                for app_name in app_names:
                    if env in prs_data[app_name] and i < len(prs_data[app_name][env]):
                        pr_data = prs_data[app_name][env][i]

                        row_values.append(pr_data['colour'])
                        if env in services_data.release_envs:
                            td_content = create_td_content_release(pr_data)
                        else:
                            td_content = create_td_content(pr_data, env, services_data.services[app_name])
                        row_values.append(td_content)

                    else:
                        row_values.append('white')
                        row_values.append('')

                row = ('<tr>' + ('<td bgcolor="{}">{}</td>' * apps_number) + '</tr>').format(*row_values)

                out.write(row)
            out.write('</table>')
        out.write('</body></html>')
