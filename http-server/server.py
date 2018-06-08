import json
import logging
import os
import re
import semver
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from cachetools import TTLCache
from logentries import LogentriesHandler


class Datadog:
    import socket
    from datadog import api
    from datadog import ThreadStats
    stats = ThreadStats()

    ACTUAL_HOST_NAME = socket.gethostname()
    METRIC_NAME_TEMPLATE = 'otm_spec_server.{}'
    REQUESTS_METRIC = METRIC_NAME_TEMPLATE.format('http.requests')
    GITHUB_RESOURCE_METRIC = METRIC_NAME_TEMPLATE.format('github_resource')
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'unknown')

    def __init__(self):
        from datadog import initialize
        initialize()
        self.stats.start()

        params = {
            'description': 'HTTP requests',
            'short_name': 'requests',
            'type': 'count',
            'unit': 'request',
            'per_unit': None
        }

        self.api.Metadata.update(metric_name=self.REQUESTS_METRIC, **params)

    def request(self, verb, request_type, version):
        tags = [
            'verb:{}'.format(verb),
            'environment:{}'.format(self.ENVIRONMENT)
        ]
        if request_type:
            tags.append('type:{}'.format(request_type)),
        if version:
            tags.append('version:{}'.format(version)),

        self.stats.increment(metric_name=self.REQUESTS_METRIC, tags=tags, value=1, sample_rate=1)

    def github_resource(self, file, version, from_cache, status_code=None):
        tags = [
            'file:{}'.format(file),
            'version:{}'.format(version),
            'from_cache:{}'.format(from_cache),
            'environment:{}'.format(self.ENVIRONMENT)
        ]
        if status_code:
            tags.append('status_code:{}'.format(status_code))
        if version and version != 'images':
            tags.append('version:{}'.format(version)),
        self.stats.increment(metric_name=self.GITHUB_RESOURCE_METRIC, tags=tags, value=1, sample_rate=1)

    def event(self, title, text):
        self.stats.event(
            title=title,
            text=text,
            tags=['environment:{}'.format(self.ENVIRONMENT), 'otm_spec_server'],
            hostname=self.ACTUAL_HOST_NAME,
            aggregation_key='otm_spec_server')
        self.stats.flush()


HOST_NAME = '0.0.0.0'
PORT_NUMBER = 9000

versions_cache = TTLCache(maxsize=100, ttl=500)  # 5 minutes
files_cache = TTLCache(maxsize=1000, ttl=86400)  # 24 hours

log = logging.getLogger('otm-spec-server')

local_html_file_string = os.environ.get("LOCAL_HTML_FILE", "False")
local_swagger_file_string = os.environ.get("LOCAL_SWAGGER_FILE", "False")
local_html_file = local_html_file_string.upper() == "TRUE"
local_swagger_file = local_swagger_file_string.upper() == "TRUE"

datadog = Datadog()


class MyHandler(BaseHTTPRequestHandler):
    CONTENT_TYPES = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "svg": "image/svg+xml",
        "html": "text/html; charset=utf-8",
        "htm": "text/html; charset=utf-8",
        "yaml": "text/x-yaml; charset=utf-8",
        "yml": "text/x-yaml; charset=utf-8",
    }

    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    if not GITHUB_TOKEN:
        log.error("No GITHUB_TOKEN found in environment. Unable to serve files from Github.")

    GITHUB_TOKEN_STRING = 'token {}'.format(GITHUB_TOKEN)

    def do_HEAD(self):
        datadog.request('HEAD', None, None)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        log.info("GET {}".format(self.path))
        log.debug("GET {}".format(self.path))
        pat = re.compile(r'/([0-9a-zA-Z\-.]+)/*(.*)')
        matched = pat.match(self.path)
        if matched:
            (version, file) = matched.groups()
            file_extension = file.rsplit('.')[-1]
        else:
            (version, file, file_extension) = ('', '', '')

        # Handle this first, since browsers tend to request a favicon for every request they do.
        if version == 'favicon.ico':
            self.send_response(404)
            self.end_headers()
            return

        req = self.get_versions_from_github()
        if req.status_code in (200, 201):
            tags_list = req.json()
            tags = dict((t.get('name').rsplit('/')[-1], t) for t in tags_list)

            if version == 'health':
                health = {
                    'name': 'otm-spec-server',
                    'version': tags_list[0]['name'].rsplit('/')[-1],
                    'health': 'RUNNING'
                }
                self.handle_response(200, {}, bytes(json.dumps(health, indent=2), "utf-8"))
                return
            if not version:
                latest_stable = next(v for v in sorted(tags, reverse=True) if not semver.parse(v)['prerelease'])
                self.handle_redirect(latest_stable)
                return
            if not file:
                self.handle_redirect("/{}/index.html".format(version))
                return

            # noinspection PyBroadException
            try:
                tag = tags.get(version)
                if tag:
                    sha = tag['commit']['sha']

                    if file == 'index.html' or file == '':
                        datadog.request('GET', "index.html", version)
                        self.handle_index_html(sha, tags, version, local_html_file)
                    elif file == 'swagger.yaml':
                        datadog.request('GET', "swagger.yaml", version)
                        self.handle_swagger_yaml(sha, version, local_swagger_file)
                    else:
                        datadog.request('GET', file_extension, version)
                        self.handle_github_file(file, file_extension, sha, version)
                else:
                    self.handle_github_file("{}/{}".format(version, file), file_extension, "master", version)
            except FileNotFoundError:
                self.handle_error(404, "File not found: '{}'".format(file))
            except Exception:
                self.handle_error(500, "Unkown error")
        else:
            self.handle_error(req.status_code, req.content)

    def handle_github_file(self, file, file_extension, sha, version):
        req = self.get_file_from_github(sha, file, version)
        if req.status_code in (200, 201):
            content_type = self.CONTENT_TYPES.get(file_extension) if file_extension else req.headers[
                'Content-type']
            self.handle_response(200, {'Content-type': content_type}, req.content)
        else:
            if req.status_code == 404:
                self.handle_error(req.status_code, '{}: {}'.format(self.possible_bytes_to_utf8(req.content), file))
            else:
                self.handle_error(req.status_code, req.content)

    def handle_file_request(self, sha, file_name, version, local_file=False):
        contents = None
        if local_file:
            log.info("Serving local file: %s", file_name)
            with open('../{}'.format(file_name), 'rb') as file:
                contents = file.read()
        else:
            req = self.get_file_from_github(sha, file_name, version)
            if req.status_code in (200, 201):
                contents = req.content
        return contents

    def handle_swagger_yaml(self, sha, version, local_file=False):
        contents = self.handle_file_request(sha, 'api/swagger.yaml', version, local_file)
        processed = contents.replace(b"{{VERSION}}", bytes(version, "utf-8"))
        self.handle_response(
            200,
            {'Content-type': self.CONTENT_TYPES['yaml']},
            processed
        )

    def handle_index_html(self, sha, tags, version, local_file=False):
        version_select = ['<option value="{0}" {1}>{0}</option>'.format(v, 'selected' if v == version else '') for v
                          in list(tags)]

        # Compatibility with older versions, where index.html did not contain a placeholder for version selection.
        if version in ['4.0.0-b1', '4.0.0', '4.0.1', '4.1.0', '4.1.1', '4.1.2']:
            tag = tags.get('4.2.0-a1')
            sha = tag['commit']['sha']

        contents_bytes = self.handle_file_request(sha, 'redoc/index.html', local_file)
        contents = contents_bytes.decode("utf-8")
        processed = contents \
            .replace("spec-url='/api-docs'", "spec-url='swagger.yaml'") \
            .replace("{{VERSION_SELECT}}", "\n".join(version_select))
        self.handle_response(
            200,
            {'Content-type': self.CONTENT_TYPES['html']},
            bytes(processed, "utf-8")
        )

    def get_versions_from_github(self):
        result = versions_cache.get("versions")
        if not result:
            log.debug("Getting versions from Github")
            result = requests.get("https://api.github.com/repos/opentripmodel/opentripmodel/tags",
                                  headers={'Authorization': self.GITHUB_TOKEN_STRING})
            versions_cache.setdefault("versions", result)
        return result

    @staticmethod
    def get_file_from_github(sha, file, version):
        cachekey = "{}{}".format(sha, file)
        result = files_cache.get(cachekey)
        if not result:
            log.debug("Getting file from github: {}/{}".format(sha, file))
            result = requests.get(
                "https://raw.githubusercontent.com/opentripmodel/opentripmodel/{}/{}".format(sha, file))
            if result.status_code in (200, 201):
                files_cache.setdefault(cachekey, result)
            datadog.github_resource(file=file, version=version, from_cache=True, status_code=result.status_code)
        else:
            datadog.github_resource(file=file, version=version, from_cache=True)
        return result

    def handle_redirect(self, url):
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()

    def handle_response(self, status_code, headers, body):
        self.send_response(status_code)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def possible_bytes_to_utf8(message):
        try:
            message = message.decode("utf-8")
        except AttributeError:
            pass
        return message

    def handle_error(self, status_code, message):
        message = self.possible_bytes_to_utf8(message).replace("\n", "")

        log.warning("Handling error %d: %s", status_code, message)
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        content = '''
        <html><head><title>Error {0}</title></head>
        <body><h1>Error {0}</h1>
        <p>{1}</p>
        </body></html>
        '''.format(status_code, message)
        self.wfile.write(bytes(content, 'UTF-8'))


def initialize_logging():
    logentries_token = os.environ.get('LOGENTRIES_TOKEN')
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=log_level)
    if logentries_token:
        log.addHandler(LogentriesHandler(logentries_token))
    else:
        log.warning("No LOGENTRIES_TOKEN found in environment. Only logging to local console.")
    log.info("Logging initialized, level=%s", log_level)


if __name__ == '__main__':
    initialize_logging()

    log.debug("LOCAL_HTML_FILE=%s", local_html_file)
    log.debug("LOCAL_SWAGGER_FILE=%s", local_swagger_file)

    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    log.info('Server Starts - %s:%s', HOST_NAME, PORT_NUMBER)
    datadog.event('OTM Spec Server Starts', 'HTTP server starts listening on {}:{}'.format(HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    log.info('Server Stops - %s:%s', HOST_NAME, PORT_NUMBER)
    datadog.event('OTM Spec Server Stops', 'HTTP server stopped listening on {}:{}'.format(HOST_NAME, PORT_NUMBER))
