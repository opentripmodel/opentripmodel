import logging
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from cachetools import TTLCache
from logentries import LogentriesHandler

HOST_NAME = 'localhost'
PORT_NUMBER = 9000

versions_cache = TTLCache(maxsize=100, ttl=500)  # 5 minutes
files_cache = TTLCache(maxsize=1000, ttl=86400)  # 24 hours

log = logging.getLogger('otm-spec-server')

local_html_file = os.environ.get("LOCAL_HTML_FILE", False)
local_swagger_file = os.environ.get("LOCAL_SWAGGER_FILE", False)

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
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
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

            if not version:
                self.handle_redirect(list(tags)[0])
                return
            if not file:
                self.handle_redirect("/{}/index.html".format(version))
                return

            try:
                tag = tags.get(version)
                if tag:
                    sha = tag['commit']['sha']

                    if file == 'index.html' or file == '':
                        self.handle_index_html(sha, tags, version, local_html_file)
                    elif file == 'swagger.yaml':
                        self.handle_swagger_yaml(sha, version, local_swagger_file)
                    else:
                        self.handle_github_file(file, file_extension, sha)
                else:
                    self.handle_github_file("{}/{}".format(version, file), file_extension, "master")
            except FileNotFoundError:
                self.handle_error(404, "File not found: '{}'".format(file))
            except Exception:
                self.handle_error(500, "Unkown error")
        else:
            self.handle_error(req.status_code, req.content)

    def handle_github_file(self, file, file_extension, sha):
        req = self.get_file_from_github(sha, file)
        if req.status_code in (200, 201):
            content_type = self.CONTENT_TYPES.get(file_extension) if file_extension else req.headers[
                'Content-type']
            self.handle_response(200, {'Content-type': content_type}, req.content)
        else:
            if req.status_code == 404:
                self.handle_error(req.status_code, '{}: {}'.format(self.possible_bytes_to_utf8(req.content), file))
            else:
                self.handle_error(req.status_code, req.content)

    def handle_file_request(self, sha, file_name, local_file=False):
        contents = None
        if local_file:
            with open('../{}'.format(file_name), 'r') as file:
                contents = file.read()
        else:
            req = self.get_file_from_github(sha, file_name)
            if req.status_code in (200, 201):
                contents = req.content
        return contents

    def handle_swagger_yaml(self, sha, version, local_file=False):
        contents = self.handle_file_request(sha, 'api/swagger.yaml', local_file)
        processed = contents.replace(b"{{VERSION}}", bytes(version, "utf-8"))
        self.handle_response(
            200,
            {'Content-type': self.CONTENT_TYPES['yaml']},
            processed
        )

    def handle_index_html(self, sha, tags, version, local_file=False):
        version_select = ['<option value="{0}" {1}>{0}</option>'.format(v, 'selected' if v == version else '') for v
                          in list(tags)]

        contents = self.handle_file_request(sha, 'redoc/index.html', local_file)
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

    def get_file_from_github(self, sha, file):
        cachekey = "{}{}".format(sha, file)
        result = files_cache.get(cachekey)
        if not result:
            log.debug("Getting file from github: {}/{}".format(sha, file))
            result = requests.get(
                "https://raw.githubusercontent.com/opentripmodel/opentripmodel/{}/{}".format(sha, file),
                headers={'Authorization': self.GITHUB_TOKEN_STRING})
            files_cache.setdefault(cachekey, result)
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


if __name__ == '__main__':
    initialize_logging()

    httpd = HTTPServer((HOST_NAME, PORT_NUMBER), MyHandler)
    log.info('Server Starts - %s:%s', HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    log.info('Server Stops - %s:%s', HOST_NAME, PORT_NUMBER)