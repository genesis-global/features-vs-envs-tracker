#!/usr/env python3

import re
from .config import Constants

__jira_regex = re.compile('[A-Za-z]{2,}-\d+')


def create_jira_link(org_name, description):
    jiras = __jira_regex.findall(description)
    result = description
    for jira in jiras:
        result = result.replace(jira, '<a href="{}/{}">{}</a>'.format(Constants.JIRA_URL, org_name, jira, jira))
    return result


def get_jira_item_regex():
    return  __jira_regex
