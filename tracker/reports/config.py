import os


class Constants:
    RELEASE_TAG_PREFIX = "release-"
    DEV_TAG_PREFIX = "dev-"
    LOG_FORMAT = "%(asctime)s %(levelname)-8s [%(funcName)15s()] %(message)s"
    ATLASSIAN_ORG_NAME = 'mysuperorg'
    CACHED_VERSIONS_REPORT = "http://localhost:9000/cached_versions_report"
    BITBUCKET_API_URL = "https://api.bitbucket.org/2.0"
    BITBUCKET_USER = os.environ['BITBUCKET_USER']
    BITBUCKET_API_KEY = os.environ['BITBUCKET_API_KEY']
    JIRA_URL = "https://{}.atlassian.net/browse"
    BUILD_SYSTEM_URL = 'http://localhost:9001/builds/'

    @classmethod
    def build_system_url(cls, url):
        return cls.BUILD_SYSTEM_URL + url


class EnvConfig:
    def __init__(self, env: str, version_url: str, build_system_url: str = ''):
        self.env = env
        self.version_url = version_url
        self.build_system_url = build_system_url


class GeneralConfig:
    def __init__(self, repo_name: str, has_db: bool = False, changelog_file: str = None):
        self.repo_name = repo_name
        self.has_db = has_db
        self.changelog_file = changelog_file


class ServiceConfig:
    def __init__(self, name: str, general_config: GeneralConfig):
        self.name = name
        self.general_config = general_config
        self.env_configs = {}
        self.order = 0

    def add_env(self, env_config: EnvConfig):
        self.env_configs[env_config.env] = env_config

    def get_version_url(self, env: str):
        return self.env_configs[env].version_url


class ServicesData:

    def __init__(self):
        self.services = {}
        self.__num__ = 0
        self.envs = ['dev', 'prod']
        self.dev_envs = ['dev']
        self.release_envs = set(self.envs) - set(self.dev_envs)
        self.env_tag_prefix = {
            'dev': Constants.DEV_TAG_PREFIX,
            'prod': Constants.RELEASE_TAG_PREFIX
        }

        self.base_versions_urls = {
            'prod': 'http://localhost:8081/prod/dog-ui/initial-dev-versions.json'
        }

        service = ServiceConfig('cat', GeneralConfig('cat-repo', True, 'cat/db/changelog.xml'))
        bs_url = Constants.build_system_url('/job/cat/{}/')
        service.add_env(EnvConfig(env='dev', version_url='http://localhost:8081/dev/cat/status', build_system_url=bs_url))
        service.add_env(EnvConfig(env='prod', version_url='http://localhost:8081/prod/cat/status'))
        self.add_to_services(service)

        service = ServiceConfig('dog', GeneralConfig('dog-repo', True, 'dog/db/changelog.xml'))
        bs_url = Constants.build_system_url('/job/dog/{}')
        service.add_env(EnvConfig(env='dev', version_url='http://localhost:8081/dev/dog/status', build_system_url=bs_url))
        service.add_env(EnvConfig(env='prod', version_url='http://localhost:8081/prod/dog/status'))
        self.add_to_services(service)

        service = ServiceConfig('dog-ui', GeneralConfig('dog-ui-repo'))
        bs_url = Constants.build_system_url('/job/dog-ui/{}/')
        service.add_env(EnvConfig(env='dev', version_url='http://localhost:8081/dev/dog-ui/version.json', build_system_url=bs_url))
        service.add_env(EnvConfig(env='prod', version_url='http://localhost:8081/prod/dog-ui/version.json'))
        self.add_to_services(service)

    def get_app_names(self):
        return [service.name for service in sorted(self.services.values(), key=lambda x: x.order)]

    def get_app_names_with_db(self):
        return [service.name for service in sorted(self.services.values(), key=lambda x: x.order) if service.general_config.has_db]

    def add_to_services(self, service: ServiceConfig):
        self.services[service.name] = service
        self.__num__ += 1
        service.order = self.__num__

    def get_base_branch(self, env: str, version: str = None):
        if env in self.dev_envs:
            return 'devel'
        branch = version.replace('.t', '')
        return '{}.0'.format(branch[:branch.rfind('.')])

