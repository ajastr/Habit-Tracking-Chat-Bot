import urllib.request, urllib.parse, urllib.error
import ssl
import re

def joke():
    url = 'http://api.icndb.com/jokes/random'

 # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


    print('Retrieving', url)
    uh = urllib.request.urlopen(url, context=ctx)

    data = uh.read()
    print('Retrieved', len(data), 'characters')
    random = data.decode()
    joke = re.findall("joke\S\S.\S(.+[.])",random)
    print(joke)
    return(joke)
