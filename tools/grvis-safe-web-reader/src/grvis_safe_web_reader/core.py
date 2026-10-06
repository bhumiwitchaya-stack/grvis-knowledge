#!/usr/bin/env python3
"""Public HTML/PDF extraction with checked-IP connections and bounded workers."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import http.client
import importlib.util
import io
import ipaddress
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, quote, urljoin, urlsplit, urlunsplit
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

VERSION = '0.4.0'
class ReaderError(Exception):
    def __init__(self, code, message, status='error'):
        super().__init__(message)
        self.code, self.status = code, status

def hostname(value):
    candidate = value.strip().rstrip('.').lower()
    try: ipaddress.ip_address(candidate)
    except ValueError: pass
    else: raise ReaderError('unsafe_url', 'IP literals are not allowed')
    try: result = candidate.encode('idna').decode('ascii')
    except UnicodeError: raise ReaderError('unsafe_url', 'Invalid hostname')
    if len(result) > 253 or not result or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', label) for label in result.split('.')):
        raise ReaderError('unsafe_url', 'Require exact DNS hostnames')
    return result

def validate_url(url, domains, allow_http=False):
    if len(url) > 8192 or re.search(r'[\x00-\x20\x7f\\]|%(?:00|0a|0d)', url, re.I):
        raise ReaderError('unsafe_url', 'Invalid URL characters or length')
    try:
        p = urlsplit(url); scheme = p.scheme.lower()
        if scheme not in ({'http', 'https'} if allow_http else {'https'}):
            raise ReaderError('unsafe_url', 'HTTPS required unless HTTP explicitly enabled')
        if p.username is not None or p.password is not None or not p.hostname:
            raise ReaderError('unsafe_url', 'Missing host or URL credentials')
        if any(re.fullmatch(r'password|access_token|api_key|apikey|signature|x-amz-signature',key,re.I) for key,_ in parse_qsl(p.query)):
            raise ReaderError('credential_url','Credential-bearing source URLs are not supported','blocked')
        host = hostname(p.hostname)
        if host not in {hostname(d) for d in domains}:
            raise ReaderError('domain_not_allowed', 'Destination not on exact allowlist', 'blocked')
        port = 443 if scheme == 'https' else 80
        if p.port not in (None, port): raise ReaderError('unsafe_url', 'Only default ports allowed')
    except ValueError as exc: raise ReaderError('unsafe_url', 'Malformed URL') from exc
    return urlunsplit((scheme, host, quote(p.path or '/', safe="/%:@!$&'()*+,;=-._~"),
                       quote(p.query, safe="/%?:@!$&'()*+,;=-._~"), '')), host, port

def public_addresses(host, port):
    try: answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc: raise ReaderError('dns_unavailable', 'Public DNS unavailable', 'unavailable') from exc
    if not answers: raise ReaderError('dns_unavailable', 'No DNS answers', 'unavailable')
    result = []
    for family, kind, proto, _, address in answers:
        ip = ipaddress.ip_address(address[0].split('%', 1)[0])
        if (not ip.is_global or ip.is_multicast or ip.is_unspecified or
            (isinstance(ip, ipaddress.IPv6Address) and (ip.sixtofour or ip.teredo))):
            raise ReaderError('non_public_destination', 'DNS contains prohibited address', 'blocked')
        if family not in (socket.AF_INET, socket.AF_INET6):
            raise ReaderError('non_public_destination', 'Unsupported address family', 'blocked')
        entry = (family, kind, proto, address)
        if entry not in result: result.append(entry)
    return result

def connect_pinned(answers, timeout):
    end = time.monotonic() + timeout
    for family, kind, proto, address in answers:
        remaining = end - time.monotonic()
        if remaining <= 0: break
        sock = socket.socket(family, kind, proto)
        try:
            sock.settimeout(remaining)
            sock.connect(address)  # no hostname resolution at connection time
            return sock
        except OSError: sock.close()
    raise ReaderError('connect_failed', 'Checked public destinations unreachable', 'unavailable')

class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, port, answers, timeout):
        super().__init__(host, port, timeout=timeout, context=ssl.create_default_context())
        self.answers = answers
    def connect(self):
        raw = connect_pinned(self.answers, self.timeout)
        try: self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except BaseException:
            raw.close(); raise

class PinnedHTTP(http.client.HTTPConnection):
    def __init__(self, host, port, answers, timeout):
        super().__init__(host, port, timeout=timeout); self.answers = answers
    def connect(self): self.sock = connect_pinned(self.answers, self.timeout)


def managed_proxy_url():
    value=os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if not value: raise ReaderError('proxy_unavailable','Managed HTTPS proxy unavailable','unavailable')
    try:
        p=urlsplit(value)
        if p.scheme!='http' or p.hostname!='127.0.0.1' or not p.port or p.username or p.password or p.path not in ('','/') or p.query or p.fragment:
            raise ValueError('unapproved proxy')
    except ValueError as exc: raise ReaderError('proxy_unavailable','Only the runtime loopback proxy is supported','unavailable') from exc
    return value

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def managed_opener():
    return build_opener(ProxyHandler({'https':managed_proxy_url()}),HTTPSHandler(context=ssl.create_default_context()),NoRedirect())

# This curated registry is a different trust boundary from checked-IP direct mode.
# The caller's per-task allowlist must still approve each hostname.
MANAGED_GATEWAY_HOSTS = frozenset({'example.com','github.com','raw.githubusercontent.com','docs.python.org',
    'modelcontextprotocol.io','developers.google.com','developers.cloudflare.com'})

def managed_destination(host,port):
    managed_proxy_url()
    if port!=443 or host not in MANAGED_GATEWAY_HOSTS:
        raise ReaderError('gateway_domain_not_allowed','Managed gateway supports reviewed public source hosts only','blocked')
    # Runtime DNS is delegated to its trusted gateway; never claim a local IP check.
    return []

class ManagedProxyConnection:
    """Explicit trusted runtime gateway route; DNS delegated, connection IP not pinned."""
    def __init__(self,host,port,answers,timeout):
        self.host,self.timeout,self.response=host,timeout,None
        self.opener=managed_opener()
    def request(self,method,target,headers):
        if method!='GET': raise ReaderError('unsafe_method','GET only','blocked')
        try: self.response=self.opener.open(Request('https://'+self.host+target,headers=headers,method='GET'),timeout=self.timeout)
        except HTTPError as exc: self.response=exc
        except (URLError,TimeoutError,OSError) as exc:
            raise ReaderError('gateway_unavailable','Managed runtime gateway could not reach this public source','unavailable') from exc
    def getresponse(self):
        response=self.response
        class Adapter:
            status=getattr(response,'status',getattr(response,'code',None))
            def getheader(self,key,default=None): return response.headers.get(key,default)
            def read(self,count): return response.read(count)
        return Adapter()
    def close(self):
        if self.response: self.response.close()

class Node:
    def __init__(self, tag, attrs=None):
        self.tag, self.attrs, self.children = tag, {k: v or '' for k,v in (attrs or [])}, []

class Document(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node('root'); self.stack, self.nodes = [self.root], []
        self.feed(html); self.close()
    def handle_starttag(self, tag, attrs):
        if len(self.nodes) >= 50000 or len(self.stack) >= 128:
            raise ReaderError('document_limit', 'HTML node/depth budget exceeded', 'partial')
        if tag in {'p','li','tr','td','th'} and self.stack[-1].tag == tag: self.stack.pop()
        node = Node(tag, attrs); self.stack[-1].children.append(node); self.nodes.append(node)
        if tag not in self.VOID: self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        for index in range(len(self.stack)-1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]; break
    def handle_data(self, data): self.stack[-1].children.append(data)

SKIP = {'script','style','noscript','svg','template'}
def hidden(node):
    return ('hidden' in node.attrs or node.attrs.get('aria-hidden','').lower() == 'true' or
            bool(re.search(r'(?:display\s*:\s*none|visibility\s*:\s*hidden)', node.attrs.get('style',''), re.I)))
def node_text(node, main=False):
    if node.tag in SKIP | {'head'} or hidden(node): return ''
    if main and node.tag in {'nav','footer','aside','form'}: return ''
    return '\n'.join(t for c in node.children if (t := (node_text(c, main) if isinstance(c,Node) else ' '.join(c.split()))))

def extract_html(raw, content_type, source_url):
    match = re.search(r'charset\s*=\s*["\']?([^\s;"\']+)', content_type, re.I)
    encoding = match.group(1) if match else 'utf-8'; warnings = []
    try: decoded = raw.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        decoded = raw.decode('utf-8', errors='replace'); warnings.append('encoding_fallback_utf8')
    doc = Document(decoded); text_all = node_text(doc.root)
    candidates = []
    def semantic(n):
        if hidden(n) or n.tag in SKIP: return
        if n.tag in {'article','main'}: candidates.append(node_text(n,True))
        for child in n.children:
            if isinstance(child,Node): semantic(child)
    semantic(doc.root)
    text = max(candidates, key=len, default='') or node_text(doc.root, True)
    title = ' '.join(' '.join(c for c in n.children if isinstance(c,str)) for n in doc.nodes if n.tag == 'title')
    base = source_url
    for n in doc.nodes:
        if n.tag == 'base' and n.attrs.get('href'):
            candidate = urljoin(source_url,n.attrs['href'])
            if urlsplit(candidate).scheme in {'http','https'}: base = candidate
            break
    def reference(value):
        if not value or re.search(r'[\x00-\x1f\x7f]', value): return None
        try:
            url = urljoin(base,value); p = urlsplit(url)
            return url if p.scheme in {'http','https'} and p.hostname and p.username is None and p.password is None else None
        except ValueError: return None
    links, images, tables = [], [], []
    def walk(node):
        if hidden(node) or node.tag in SKIP: return
        if node.tag == 'a' and (url := reference(node.attrs.get('href'))):
            links.append({'url':url,'text':node_text(node),'approved_for_fetch':False})
        if node.tag == 'img' and (url := reference(node.attrs.get('src'))):
            images.append({'url':url,'alt':node.attrs.get('alt',''),'approved_for_fetch':False})
        if node.tag == 'table':
            rows = []
            def table_rows(n):
                if hidden(n) or n.tag in SKIP or (n is not node and n.tag == 'table'): return
                if n.tag == 'tr':
                    rows.append([{'text':node_text(c),'rowspan':c.attrs.get('rowspan','1'),'colspan':c.attrs.get('colspan','1')}
                                 for c in n.children if isinstance(c,Node) and c.tag in {'td','th'} and not hidden(c)])
                for c in n.children:
                    if isinstance(c,Node): table_rows(c)
            table_rows(node); tables.append(rows)
        for c in node.children:
            if isinstance(c,Node): walk(c)
    walk(doc.root)
    challenge = bool(re.search(r"(?:verify (?:you are|that you(?:'re| are)) human|complete the captcha|checking your browser|just a moment)",title+'\n'+text[:3000],re.I)) and len(text)<6000
    status = 'blocked' if challenge else 'empty' if not text.strip() else 'partial' if warnings else 'ok'
    return {'status':status,'reason':'challenge_suspected' if challenge else 'no_text' if status=='empty' else 'encoding_fallback' if warnings else None,
            'text':text,'text_all':text_all,'title':title,'links':links,'images':images,'tables':tables,'warnings':warnings,
            'extraction_method':'semantic_html' if any(candidates) else 'clean_html_text',
            'coverage':{'javascript_executed':False,'media_downloaded':False,'completeness_verified':False,
                        'visibility_verified':False,'challenge_detection':'heuristic','table_layout_verified':False}}

def extract_pdf(raw, max_pages):
    if not importlib.util.find_spec('pypdf'):
        raise ReaderError('pdf_dependency_missing','Use available PDF tool or separately install reviewed pypdf','unsupported')
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw), strict=False)
    if reader.is_encrypted: raise ReaderError('encrypted_pdf','Encrypted PDF unsupported','unsupported')
    total = len(reader.pages); pages = []; chars = 0; texts = []; empty_pages = []
    for i in range(min(total,max_pages)):
        text = reader.pages[i].extract_text() or ''; chars += len(text)
        if chars>1000000: raise ReaderError('pdf_text_limit','PDF text budget exceeded','partial')
        start = sum(len(t) for t in texts) + len(texts)
        pages.append({'page':i+1,'start_char':start,'end_char':start+len(text)})
        texts.append(text)
        if not text.strip(): empty_pages.append(i+1)
    text = '\n'.join(texts); incomplete = total>len(pages)
    return {'status':'partial' if incomplete else 'empty' if not text.strip() else 'partial' if empty_pages else 'ok',
            'reason':'page_budget' if incomplete else 'ocr_may_be_required' if empty_pages else None,
            'text':text,'pages':pages,'title':str((reader.metadata or {}).get('/Title','')),'extraction_method':'pdf_text',
            'coverage':{'total_pages':total,'pages_extracted':len(pages),'ocr_performed':False,'completeness_verified':False,
                        'table_layout_verified':False,'media_downloaded':False,'pages_without_text':empty_pages},'warnings':[]}

def fetch_worker(job):
    end = time.monotonic()+job['deadline']; current = job['url']; chain = []
    for hop in range(job['redirects']+1):
        current,host,port = validate_url(current,job['domains'],job.get('allow_http',False))
        timeout = min(10,end-time.monotonic())
        route=job.get('network_route','direct')
        if route=='managed-proxy' and not current.startswith('https:'): raise ReaderError('unsafe_url','Managed proxy route requires HTTPS','blocked')
        answers = managed_destination(host,port) if route=='managed-proxy' else public_addresses(host,port)
        timeout = min(10,end-time.monotonic())
        if timeout<=0: raise ReaderError('deadline','Total deadline exceeded','unavailable')
        cls=ManagedProxyConnection if route=='managed-proxy' else PinnedHTTPS if current.startswith('https:') else PinnedHTTP
        conn=cls(host,port,answers,timeout)
        try:
            p=urlsplit(current)
            conn.request('GET',p.path+('?' + p.query if p.query else ''),headers={'User-Agent':'GRVIS-Research/'+VERSION,
                         'Accept':'text/html,application/xhtml+xml,application/pdf','Accept-Encoding':'identity'})
            response=conn.getresponse(); status=response.status
            if status in {301,302,303,307,308}:
                location=response.getheader('Location')
                if not location or hop==job['redirects']: raise ReaderError('redirect_limit','Redirect budget or missing Location','partial')
                target=urljoin(current,location)
                if current.startswith('https:') and urlsplit(target).scheme!='https':
                    raise ReaderError('https_downgrade','HTTPS downgrade blocked','blocked')
                target,_,_=validate_url(target,job['domains'],job.get('allow_http',False))
                chain.append(target); current=target; continue
            if status in {401,403,429}: raise ReaderError('http_'+str(status),'Authentication, access or rate-limit restriction','blocked')
            if not 200<=status<300: raise ReaderError('http_'+str(status),'Upstream HTTP error','unavailable')
            content_type=response.getheader('Content-Type',''); media_type=content_type.split(';',1)[0].strip().lower()
            if media_type not in {'text/html','application/xhtml+xml','application/pdf'}:
                raise ReaderError('unsupported_type','Only HTML and PDF supported','unsupported')
            length=response.getheader('Content-Length','')
            if length.isdigit() and int(length)>job['max_bytes']: raise ReaderError('body_limit','Response exceeds byte budget','partial')
            raw=response.read(job['max_bytes']+1)
            if len(raw)>job['max_bytes']: raise ReaderError('body_limit','Response exceeds byte budget','partial')
            compression=response.getheader('Content-Encoding','identity').lower().strip()
            if compression=='gzip':
                raw=gzip.GzipFile(fileobj=io.BytesIO(raw)).read(job['max_bytes']+1)
                if len(raw)>job['max_bytes']: raise ReaderError('body_limit','Decompressed response exceeds byte budget','partial')
            elif compression not in {'','identity'}: raise ReaderError('unsupported_encoding','Unsupported compression','unsupported')
        finally: conn.close()
        result=extract_pdf(raw,job['pdf_pages']) if media_type=='application/pdf' else extract_html(raw,content_type,current)
        result.update({'schema_version':'1.0','reader_version':VERSION,'requested_url':job['url'],'source_url':current,'redirect_chain':chain,
                       'http_status':status,'content_type':media_type,'response_bytes':len(raw),'retrieved_at':datetime.now(timezone.utc).isoformat(),
                       'content_sha256':hashlib.sha256(raw).hexdigest(),'content_is_untrusted_data':True,'transport_authenticated':current.startswith('https:'),
                       'network':{'route':route,'dns_public_checked':route=='direct','ip_pinning':route=='direct','dns_method':'system' if route=='direct' else 'managed_gateway','gateway_trusted':route=='managed-proxy','destination_policy':'task_and_curated_exact_allowlist' if route=='managed-proxy' else 'task_exact_allowlist_and_public_ip'}})
        return result
    raise ReaderError('redirect_limit','Redirect budget exhausted','partial')

def failure(job,code,message,status='error'):
    return {'schema_version':'1.0','reader_version':VERSION,'status':status,'reason':code,'error':message,
            'requested_url':job.get('url'),'retrieved_at':datetime.now(timezone.utc).isoformat(),
            'content_is_untrusted_data':True,'coverage':{'completeness_verified':False}}

def bounded_output(result):
    """Cap emitted JSON even when structured extraction amplifies a small body."""
    if len(json.dumps(result,ensure_ascii=False).encode('utf-8')) <= 4*1024*1024: return result
    removed = []
    for key in ['text_all','links','images','tables','pages']:
        if key in result:
            result.pop(key); removed.append(key)
    if 'text' in result: result['text'] = result['text'][:250000]
    if 'title' in result: result['title'] = result['title'][:4096]
    result.setdefault('warnings',[]).append('output_budget_exceeded')
    result['coverage']['omitted_fields'] = removed
    result['coverage']['output_truncated'] = True
    if result.get('status') not in {'blocked','empty','error','unsupported','unavailable'}:
        result['status'],result['reason'] = 'partial','output_budget'
    return result

def validate_job(job):
    if job.get('network_route','direct') not in {'direct','managed-proxy'}: raise ReaderError('invalid_route','Unsupported network route')
    for key,(low,high) in {'max_bytes':(1,20*1024*1024),'deadline':(1,60),'redirects':(0,5),'pdf_pages':(1,100)}.items():
        value=job.get(key)
        if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high: raise ReaderError('invalid_budget','Invalid '+key+' budget')
    domains=job.get('domains')
    if not isinstance(domains,list) or not 1<=len(domains)<=50 or not all(isinstance(d,str) for d in domains):
        raise ReaderError('unsafe_url','Require 1–50 exact hostnames')
    if not isinstance(job.get('url'),str) or not isinstance(job.get('allow_http',False),bool): raise ReaderError('unsafe_url','Invalid URL/HTTP flag')
    validate_url(job['url'],domains,job.get('allow_http',False))

def run_job(job):
    try:
        validate_job(job)
        process=subprocess.run([sys.executable,str(Path(__file__).resolve()),'_worker'],input=json.dumps(job),capture_output=True,text=True,timeout=job['deadline'])
        if process.returncode!=0: return failure(job,'worker_failed','Worker exited without valid result')
        result=json.loads(process.stdout)
        if not job.get('include_all_text'): result.pop('text_all',None)
        if job.get('chunks') and 'text' in result:
            value=result.pop('text'); result['text_chunks']=[value[i:i+12000] for i in range(0,len(value),12000)]
        return result
    except subprocess.TimeoutExpired: return failure(job,'deadline','Total job deadline exceeded','unavailable')
    except ReaderError as exc: return failure(job,exc.code,str(exc),exc.status)
    except (ValueError,OSError): return failure(job,'runtime_unavailable','Reader runtime unavailable','unavailable')

def batch_jobs(jobs,total_deadline=120):
    if not 1<=len(jobs)<=12 or not 1<=total_deadline<=300: raise ReaderError('invalid_budget','Batch needs 1–12 URLs; deadline 1–300 seconds')
    started=time.monotonic(); results=[]; seen={}
    for original in jobs:
        job=dict(original); remaining=int(total_deadline-(time.monotonic()-started))
        if remaining<1:
            results.append(failure(job,'batch_deadline','Batch deadline exhausted','unavailable')); continue
        job['deadline']=min(job['deadline'],remaining); result=run_job(job); digest=result.get('content_sha256')
        if digest:
            result['duplicate_of']=seen.get(digest); seen.setdefault(digest,result.get('source_url'))
        results.append(result)
    return {'schema_version':'1.0','sources':results,'counts':{s:sum(r['status']==s for r in results) for s in {r['status'] for r in results}},
            'coverage':{'requested_sources':len(jobs),'results_recorded':len(results),'completeness_verified':False},'elapsed_seconds':round(time.monotonic()-started,3)}

def capabilities():
    try: managed_proxy_url(); proxy=True
    except ReaderError: proxy=False
    return {'reader_version':VERSION,'python':sys.version.split()[0],'html':True,'pdf':bool(importlib.util.find_spec('pypdf')),
            'network_verified':False,'managed_proxy_available':proxy,'managed_proxy_domains':sorted(MANAGED_GATEWAY_HOSTS),'dns_ip_pinning':{'direct':True,'managed-proxy':False},'per_job_process_deadline':True,'javascript':False,'ocr':False,
            'social_api':False,'media':False,'local_stdio_mcp':True,'remote_mcp_deployed':False,'scheduler':False}

def main():
    if len(sys.argv)==2 and sys.argv[1]=='_worker':
        job=json.loads(sys.stdin.read(32768))
        try:
            validate_job(job)
            try:
                import resource
                resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,)*2)
                resource.setrlimit(resource.RLIMIT_CPU,(job['deadline']+1,)*2)
            except (ImportError,ValueError,OSError): pass
            result=fetch_worker(job)
        except ReaderError as exc: result=failure(job,exc.code,str(exc),exc.status)
        except Exception as exc: result=failure(job,'fetch_failed','Fetch/parse failed ('+type(exc).__name__+')')
        print(json.dumps(bounded_output(result),ensure_ascii=False)); return 0
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['fetch','batch','capabilities']); parser.add_argument('url',nargs='?')
    parser.add_argument('--url',action='append',dest='urls',default=[]); parser.add_argument('--allow-domain',action='append',default=[])
    parser.add_argument('--network-route',choices=['direct','managed-proxy'],default='direct')
    parser.add_argument('--allow-http',action='store_true'); parser.add_argument('--deadline',type=int,default=20)
    parser.add_argument('--batch-deadline',type=int,default=120); parser.add_argument('--max-response-mib',type=int,default=2)
    parser.add_argument('--max-redirects',type=int,default=3); parser.add_argument('--pdf-pages',type=int,default=30)
    parser.add_argument('--chunks',action='store_true'); parser.add_argument('--include-all-text',action='store_true')
    args=parser.parse_args()
    if args.mode=='capabilities': print(json.dumps(capabilities())); return 0
    urls=([args.url] if args.url else [])+args.urls
    if not urls or (args.mode=='fetch' and len(urls)!=1): parser.error('fetch needs one URL; batch needs 1–12')
    jobs=[{'url':url,'domains':args.allow_domain,'network_route':args.network_route,'allow_http':args.allow_http,'deadline':args.deadline,'max_bytes':args.max_response_mib*1024*1024,
           'redirects':args.max_redirects,'pdf_pages':args.pdf_pages,'chunks':args.chunks,'include_all_text':args.include_all_text} for url in urls]
    try: result=run_job(jobs[0]) if args.mode=='fetch' else batch_jobs(jobs,args.batch_deadline)
    except ReaderError as exc: result=failure({},exc.code,str(exc),exc.status)
    print(json.dumps(result,ensure_ascii=False))
    if args.mode=='batch' and 'sources' in result: return 0 if all(r['status']=='ok' for r in result['sources']) else 1
    return 0 if result.get('status')=='ok' else 1

if __name__=='__main__': raise SystemExit(main())
