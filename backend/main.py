from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import sys
import json
from urllib import parse

from graph import Graph, print_path

log_format = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='my_happy.log', format=log_format, level=logging.DEBUG)


class MyBaseHTTPHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        logging.info('GET Request')
        self._set_headers()

        parsed_path = dict(parse.parse_qsl(parse.urlsplit(self.path).query))

        giv_start = (float(parsed_path['startLat']), float(parsed_path['startLon']))
        giv_end = (float(parsed_path['endLat']), float(parsed_path['endLon']))

        graph = Graph("../backend/map2.osm")
        data = graph.search_path(giv_start, giv_end)

        logging.info(data)

        # data = {
        #     'foo': 'bar'
        # }
        self.wfile.write(bytes(json.dumps(data), 'UTF-8'))


server_address = ('', 9123)

try:
    httpd = HTTPServer(server_address, MyBaseHTTPHandler)
    logging.info('Starting server on {address}:{port}'.format(
        address=httpd.server_address[0], port=httpd.server_address[1])
    )
    httpd.serve_forever()
except OSError as e:
    logging.error(e.strerror)
except:
    e = sys.exc_info()[0]
    logging.error(e)