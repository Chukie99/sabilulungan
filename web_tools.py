"""Read bounded public HTTPS pages without accessing local network services."""
import http.client
import ipaddress
import socket
import ssl
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'):
            self.hidden += 1
    def handle_endtag(self, tag):
        if tag in ('script','style'):
            self.hidden = max(0,self.hidden-1)
    def handle_data(self, data):
        if not self.hidden and data.strip():
            self.parts.append(data.strip())


def read_url(url, redirects=0):
    if not isinstance(url,str) or len(url)>4000:
        raise ValueError('URL tidak valid.')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError('Hanya URL HTTPS publik port 443 yang diizinkan.')
    addresses = socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Alamat lokal atau jaringan privat tidak diizinkan.')
    # Pin the validated address, while verifying TLS against the original hostname.
    connection = http.client.HTTPSConnection(parsed.hostname,timeout=15)
    raw = socket.create_connection((addresses[0][4][0],443),timeout=15)
    try:
        connection.sock = ssl.create_default_context().wrap_socket(raw,server_hostname=parsed.hostname)
        connection.request('GET',(parsed.path or '/')+('?' + parsed.query if parsed.query else ''),headers={'User-Agent':'Sabilulungan/3.0'})
        response = connection.getresponse()
        if response.status in (301,302,303,307,308):
            if redirects>=3:
                raise ValueError('Terlalu banyak redirect.')
            location=response.getheader('Location')
            if not location:
                raise ValueError('Redirect tanpa tujuan.')
            return read_url(urljoin(url,location),redirects+1)
        if response.status != 200:
            raise ValueError('Website mengembalikan HTTP '+str(response.status))
        kind=response.getheader('Content-Type','').split(';')[0]
        if kind not in ('text/html','text/plain','application/json'):
            raise ValueError('Hanya halaman HTML, teks, atau JSON yang bisa dibaca.')
        content=response.read(200001)
        if len(content)>200000:
            raise ValueError('Halaman terlalu besar (maksimal 200 KB).')
        text=content.decode('utf-8',errors='replace')
        if kind=='text/html':
            parser=TextParser()
            parser.feed(text)
            text='\n'.join(parser.parts)
        return 'Sumber: '+url+'\n'+text[:20000]
    finally:
        connection.close()
        raw.close()
