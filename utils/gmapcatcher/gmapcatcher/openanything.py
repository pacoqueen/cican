'''OpenAnything: a kind and thoughtful library for HTTP web services

This program is part of 'Dive Into Python', a free Python book for
experienced programmers.  Visit http://diveintopython.org/ for the
latest version.
'''

__author__ = 'Mark Pilgrim (mark@diveintopython.org)'
__version__ = '$Revision: 1.6 $'[11:-2]
__date__ = '$Date: 2004/04/16 21:16:24 $'
__copyright__ = 'Copyright (c) 2004 Mark Pilgrim'
__license__ = 'Python'

import urllib2, urlparse, gzip, httplib, mimetypes
from StringIO import StringIO
from mapConst import *
#from django.template.defaultfilters import urlencode


#USER_AGENT = 'OpenAnything/%s +http://diveintopython.org/http_web_services/' % __version__
USER_AGENT = '%s/%s +%s' % (NAME, VERSION, WEB_ADDRESS)

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code
        return result

class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, headers):
        result = urllib2.HTTPError(
            req.get_full_url(), code, msg, headers, fp)
        result.status = code
        return result

def encode_post_data_dict( post_data ):
    data = []
    for key in post_data.keys():
        data.append( urlencode(key) +'='+ urlencode(post_data[key]) )
    return '&'.join(data)

def encode_post_data( post_data ):
    data = []
    for x in post_data:
        data.append( urlencode(x[0]) +'='+ urlencode(x[1]) )
    return '&'.join(data)

def openAnything( source, etag=None, lastmodified=None, agent=USER_AGENT, post_data=None, files=None ):
    """URL, filename, or string --> stream

    This function lets you define parsers that take any input source
    (URL, pathname to local or network file, or actual data as a string)
    and deal with it in a uniform manner.  Returned object is guaranteed
    to have all the basic stdio read methods (read, readline, readlines).
    Just .close() the object when you're done with it.

    If the etag argument is supplied, it will be used as the value of an
    If-None-Match request header.

    If the lastmodified argument is supplied, it must be a formatted
    date/time string in GMT (as returned in the Last-Modified header of
    a previous request).  The formatted date/time will be used
    as the value of an If-Modified-Since request header.

    If the agent argument is supplied, it will be used as the value of a
    User-Agent request header.
    """

    if hasattr(source, 'read'):
        return source

    if source == '-':
        return sys.stdin

    if isinstance(post_data, dict):
        post_data_dict = post_data
        post_data = []
        for key in post_data_dict.keys():
            post_data.append( (key, post_data_dict[key]) )

    protocol = urlparse.urlparse(source)[0]
    if protocol=='http' or protocol=='https':
        # open URL with urllib2
        request = urllib2.Request(source)
        request.add_header('User-Agent', agent)
        if lastmodified:
            request.add_header('If-Modified-Since', lastmodified)
        if etag:
            request.add_header('If-None-Match', etag)
        if post_data and files:
            content_type, body = encode_multipart_formdata( post_data, files )
            request.add_header('Content-Type', content_type)
            request.add_data(body)
        elif post_data:
            request.add_data( encode_post_data( post_data ) )
        request.add_header('Accept-encoding', 'gzip')
        opener = urllib2.build_opener(SmartRedirectHandler(), DefaultErrorHandler())
        return opener.open(request)

    # try to open with native open function (if source is a filename)
    try:
        return open(source)
    except (IOError, OSError):
        pass

    # treat source as string
    return StringIO(str(source))

def fetch(source, etag=None, lastmodified=None, agent=USER_AGENT, post_data=None, files=None):
    '''Fetch data and metadata from a URL, file, stream, or string'''
    result = {}
    f = openAnything(source, etag, lastmodified, agent, post_data, files)
    result['data'] = f.read()
    if hasattr(f, 'headers'):
        # save ETag, if the server sent one
        result['etag'] = f.headers.get('ETag')
        # save Last-Modified header, if the server sent one
        result['lastmodified'] = f.headers.get('Last-Modified')
        if f.headers.get('content-encoding') == 'gzip':
            # data came back gzip-compressed, decompress it
            result['data'] = gzip.GzipFile(fileobj=StringIO(result['data'])).read()
    if hasattr(f, 'url'):
        result['url'] = f.url
        result['status'] = 200
    if hasattr(f, 'status'):
        result['status'] = f.status
    f.close()
    return result

def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(open(filename,'rb').read())
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    #print '--== encode_multipart_formdata:body ==--'
    return content_type, body

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
