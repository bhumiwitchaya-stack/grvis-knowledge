"""Offline regression tests; fixtures do not certify live network access."""
import gzip
import io
import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from grvis_safe_web_reader import core as r
from grvis_safe_web_reader import mcp as m

BASE={'url':'https://example.com/','domains':['example.com'],'deadline':2,'max_bytes':2097152,'redirects':3,'pdf_pages':30}
def dns(host,port,**kw): return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',port))]
class Response:
 def __init__(self,body=b'<main>Article</main>',status=200,headers=None):
  self.status=status; self.body=body; self.headers={'Content-Type':'text/html; charset=utf-8',**(headers or {})}
 def getheader(self,key,default=None): return self.headers.get(key,default)
 def read(self,count): return self.body[:count]
class Tests(unittest.TestCase):
 def extract(self,html,ctype='text/html; charset=utf-8'): return r.extract_html(html.encode(),ctype,BASE['url'])
 def transport(self,responses,job=None):
  connections=[]
  for resp in responses:
   conn=Mock(); conn.getresponse.return_value=resp; connections.append(conn)
  with patch.object(r,'public_addresses',return_value=dns('',443)),patch.object(r,'PinnedHTTPS',side_effect=connections):
   return r.fetch_worker(job or dict(BASE)),connections
 def test_managed_proxy_requires_loopback_without_credentials(self):
  import os
  for value in ['http://remote.example:1234','http://u:p@127.0.0.1:1234','https://127.0.0.1:1234','http://127.0.0.1:1234/path']:
   with patch.dict(os.environ,{'HTTPS_PROXY':value}),self.assertRaises(r.ReaderError): r.managed_proxy_url()
  with patch.dict(os.environ,{'HTTPS_PROXY':'http://127.0.0.1:1234'}): self.assertEqual(r.managed_proxy_url(),'http://127.0.0.1:1234')
 def test_gateway_transport_failure_is_explicit_unavailable(self):
  opener=Mock();opener.open.side_effect=r.URLError('transport failed')
  with patch.object(r,'managed_opener',return_value=opener),self.assertRaises(r.ReaderError) as ctx:
   conn=r.ManagedProxyConnection('example.com',443,[],2);conn.request('GET','/',{})
  self.assertEqual(ctx.exception.code,'gateway_unavailable');self.assertEqual(ctx.exception.status,'unavailable')
 def test_managed_route_requires_curated_and_task_host(self):
  job={**BASE,'url':'https://custom.example/','domains':['custom.example'],'network_route':'managed-proxy'}
  with patch.object(r,'managed_proxy_url',return_value='http://127.0.0.1:1234'),self.assertRaises(r.ReaderError) as ctx: r.fetch_worker(job)
  self.assertEqual(ctx.exception.code,'gateway_domain_not_allowed')
  with self.assertRaises(r.ReaderError): r.fetch_worker({**BASE,'network_route':'managed-proxy','domains':['github.com']})
 def test_managed_route_delegates_dns_and_reports_trust_boundary(self):
  conn=Mock();conn.getresponse.return_value=Response()
  with patch.object(r,'managed_proxy_url',return_value='http://127.0.0.1:1234'),patch.object(r,'ManagedProxyConnection',return_value=conn),patch.object(socket,'getaddrinfo',side_effect=AssertionError('Local DNS is unavailable')):
   result=r.fetch_worker({**BASE,'network_route':'managed-proxy'})
  self.assertEqual(result['network']['dns_method'],'managed_gateway');self.assertFalse(result['network']['dns_public_checked']);self.assertFalse(result['network']['ip_pinning'])
 def test_managed_route_redirect_does_not_widen_registry(self):
  conn=Mock();conn.getresponse.return_value=Response(status=302,headers={'Location':'https://custom.example/'})
  job={**BASE,'network_route':'managed-proxy','domains':['example.com','custom.example']}
  with patch.object(r,'managed_proxy_url',return_value='http://127.0.0.1:1234'),patch.object(r,'ManagedProxyConnection',return_value=conn) as connections,self.assertRaises(r.ReaderError) as ctx: r.fetch_worker(job)
  self.assertEqual(ctx.exception.code,'gateway_domain_not_allowed');self.assertEqual(connections.call_count,1)
 def test_managed_route_http_rejected(self):
  with self.assertRaises(r.ReaderError): r.fetch_worker({**BASE,'url':'http://example.com/','allow_http':True,'network_route':'managed-proxy'})
 def test_mcp_route_set_by_server_not_tool_argument(self):
  server=m.Server(['example.com'],'managed-proxy')
  with self.assertRaises(m.ProtocolError): server.tool('grvis_fetch',{'url':BASE['url'],'network_route':'direct'})
  with patch.object(m,'run_job',return_value={'status':'ok'}) as run:
   server.tool('grvis_fetch',{'url':BASE['url']})
  self.assertEqual(run.call_args.args[0]['network_route'],'managed-proxy')
 def test_idna_and_unicode_path(self):
  url,host,_=r.validate_url('HTTPS://BÜCHER.example./ไทย#fragment',['xn--bcher-kva.example'])
  self.assertEqual(host,'xn--bcher-kva.example'); self.assertIn('%E0',url); self.assertNotIn('#',url)
 def test_reject_unsafe_url(self):
  urls=['file:///etc/passwd','http://example.com/','https://u:p@example.com/','https://127.0.0.1/',
        'https://example.com.attacker.test/','https://example.com:8443/','https://example.com/a\nb','https://example.com/%0d%0aX',
        'https://example.com/\\x','https://[::1]/','https://example.com/?access_token=secret']
  for url in urls:
   with self.subTest(url=url),self.assertRaises(r.ReaderError): r.validate_url(url,['example.com'])
 def test_private_and_mixed_dns(self):
  for address in ['127.0.0.1','10.0.0.1','169.254.169.254','224.0.0.1','::1','2002:0a00:0001::1']:
   answers=dns('',443)+[(socket.AF_INET,socket.SOCK_STREAM,6,'',(address,443))]
   with self.subTest(address=address),patch.object(socket,'getaddrinfo',return_value=answers),self.assertRaises(r.ReaderError):
    r.public_addresses('example.com',443)
 def test_checked_ip_connection_does_not_resolve_again(self):
  sock=Mock()
  with patch.object(socket,'socket',return_value=sock),patch.object(socket,'getaddrinfo',side_effect=AssertionError('Unexpected DNS')):
   self.assertIs(r.connect_pinned([(socket.AF_INET,socket.SOCK_STREAM,6,('93.184.216.34',443))],1),sock)
  sock.connect.assert_called_once_with(('93.184.216.34',443))
 def test_tls_uses_hostname_and_verification(self):
  conn=r.PinnedHTTPS('example.com',443,dns('',443),2); raw=Mock(); context=Mock(); conn._context=context
  with patch.object(r,'connect_pinned',return_value=raw): conn.connect()
  context.wrap_socket.assert_called_once_with(raw,server_hostname='example.com')
  real=r.ssl.create_default_context(); self.assertTrue(real.check_hostname); self.assertEqual(real.verify_mode,r.ssl.CERT_REQUIRED)
 def test_hidden_semantic_ancestor(self):
  result=self.extract('<div hidden><main>Hidden</main></div><p>Visible</p>')
  self.assertEqual(result['text'],'Visible')
 def test_same_cleaning_all_fields(self):
  result=self.extract('<main>Article<a href="/x">News<script>malicious</script></a><table><tr><td>Value<script>bad</script><span hidden>secret</span></td></tr></table></main>')
  self.assertNotIn('malicious',json.dumps(result)); self.assertNotIn('secret',json.dumps(result)); self.assertEqual(result['tables'][0][0][0]['text'],'Value')
 def test_main_and_navigation(self):
  result=self.extract('<nav>Menu</nav><main>Real article</main><div style="display:none">Hidden</div>')
  self.assertEqual(result['text'],'Real article'); self.assertNotIn('Hidden',result['text_all'])
 def test_boolean_style_and_aria(self):
  self.assertEqual(self.extract('<main style aria-hidden>Article</main>')['text'],'Article')
 def test_base_link_reference_not_authorized(self):
  result=self.extract('<head><base href="https://other.example/reports/"></head><a href="next">Next</a>')
  self.assertEqual(result['links'][0]['url'],'https://other.example/reports/next'); self.assertFalse(result['links'][0]['approved_for_fetch'])
 def test_challenge(self): self.assertEqual(self.extract('<title>Verify you are human</title><p>Complete the CAPTCHA</p>')['status'],'blocked')
 def test_empty(self): self.assertEqual(self.extract('<html><body></body></html>')['status'],'empty')
 def test_charset_fallback(self):
  result=self.extract('<main>Article</main>','text/html; charset=unknown-charset')
  self.assertEqual(result['status'],'partial'); self.assertIn('encoding_fallback_utf8',result['warnings'])
 def test_document_depth_budget(self):
  with self.assertRaises(r.ReaderError): self.extract('<div>'*200+'text'+'</div>'*200)
 def test_redirect_to_unapproved_host(self):
  with self.assertRaises(r.ReaderError) as ctx: self.transport([Response(status=302,headers={'Location':'https://bad.example/'})])
  self.assertEqual(ctx.exception.code,'domain_not_allowed')
 def test_https_downgrade(self):
  with self.assertRaises(r.ReaderError) as ctx: self.transport([Response(status=302,headers={'Location':'http://example.com/'})])
  self.assertEqual(ctx.exception.code,'https_downgrade')
 def test_redirect_provenance_and_get_only(self):
  result,conns=self.transport([Response(status=302,headers={'Location':'/next'}),Response()])
  self.assertEqual(result['source_url'],'https://example.com/next'); self.assertEqual(result['redirect_chain'],['https://example.com/next'])
  self.assertEqual(conns[0].request.call_args.args[0],'GET'); self.assertNotIn('Cookie',conns[0].request.call_args.kwargs['headers'])
  self.assertEqual(len(result['content_sha256']),64); self.assertTrue(result['content_is_untrusted_data']); self.assertFalse(result['coverage']['completeness_verified'])
  for conn in conns: conn.close.assert_called_once()
 def test_blocked_http(self):
  for status in [401,403,429]:
   with self.subTest(status=status),self.assertRaises(r.ReaderError) as ctx: self.transport([Response(status=status)])
   self.assertEqual(ctx.exception.status,'blocked')
 def test_response_and_decompression_budgets(self):
  for response in [Response(body=b'x'*11),Response(headers={'Content-Length':'11'}),Response(body=gzip.compress(b'x'*100),headers={'Content-Encoding':'gzip'})]:
   job={**BASE,'max_bytes':10 if response.headers.get('Content-Encoding')!='gzip' else 50}
   with self.assertRaises(r.ReaderError) as ctx: self.transport([response],job)
   self.assertEqual(ctx.exception.code,'body_limit')
 def test_non_html_not_read(self):
  with self.assertRaises(r.ReaderError) as ctx: self.transport([Response(headers={'Content-Type':'application/json'})])
  self.assertEqual(ctx.exception.code,'unsupported_type')
 def test_total_timeout(self):
  with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired('worker',2)):
   self.assertEqual(r.run_job(dict(BASE))['reason'],'deadline')
 def test_actual_child_deadline(self):
  with tempfile.TemporaryDirectory() as directory:
   worker=r.Path(directory)/'worker.py'; worker.write_text('import time; time.sleep(10)',encoding='utf-8')
   started=time.monotonic()
   with patch.object(r,'__file__',str(worker)):
    result=r.run_job({**BASE,'deadline':1})
   self.assertEqual(result['reason'],'deadline'); self.assertLess(time.monotonic()-started,3)
 def test_chunks_no_duplicate_full_text(self):
  result={'status':'ok','text':'x'*25000,'text_all':'extra','coverage':{}}
  with patch.object(subprocess,'run',return_value=Mock(returncode=0,stdout=json.dumps(result))):
   output=r.run_job({**BASE,'chunks':True})
  self.assertNotIn('text',output); self.assertNotIn('text_all',output); self.assertEqual(''.join(output['text_chunks']),'x'*25000)
 def test_output_budget(self):
  result={'status':'ok','text':'x'*5000000,'title':'t'*5000000,'tables':[[]],'coverage':{}}
  output=r.bounded_output(result)
  self.assertEqual(output['status'],'partial'); self.assertLess(len(json.dumps(output)),4*1024*1024); self.assertTrue(output['coverage']['output_truncated'])
 def test_batch_failure_continue_and_dedup(self):
  with patch.object(r,'run_job',side_effect=[{'status':'ok','content_sha256':'same','source_url':'a'},r.failure(BASE,'blocked','blocked','blocked'),{'status':'ok','content_sha256':'same','source_url':'b'}]):
   output=r.batch_jobs([BASE]*3,20)
  self.assertEqual(len(output['sources']),3); self.assertEqual(output['sources'][2]['duplicate_of'],'a'); self.assertEqual(output['counts']['blocked'],1)
 def test_invalid_budgets(self):
  for key,value in [('deadline',0),('deadline',True),('max_bytes',999999999),('redirects',6),('pdf_pages',101)]:
   with self.subTest(key=key),self.assertRaises(r.ReaderError): r.validate_job({**BASE,key:value})
 def test_pdf_page_budget_and_blank(self):
  if not r.importlib.util.find_spec('pypdf'): self.skipTest('pypdf unavailable')
  from pypdf import PdfWriter
  writer=PdfWriter()
  for _ in range(3): writer.add_blank_page(width=100,height=100)
  data=io.BytesIO(); writer.write(data)
  result=r.extract_pdf(data.getvalue(),1)
  self.assertEqual(result['status'],'partial'); self.assertEqual(result['coverage']['total_pages'],3); self.assertEqual(result['pages'][0]['page'],1)
  self.assertEqual(r.extract_pdf(data.getvalue(),3)['status'],'empty')
 def test_pdf_missing_dependency(self):
  with patch.object(r.importlib.util,'find_spec',return_value=None),self.assertRaises(r.ReaderError) as ctx: r.extract_pdf(b'',1)
  self.assertEqual(ctx.exception.code,'pdf_dependency_missing')
 def test_real_pdf_text_and_offsets(self):
  if not r.importlib.util.find_spec('pypdf') or not r.importlib.util.find_spec('reportlab'): self.skipTest('PDF fixture dependencies unavailable')
  from reportlab.pdfgen.canvas import Canvas
  data=io.BytesIO(); canvas=Canvas(data)
  for text in ['First evidence','Second evidence']:
   canvas.drawString(30,700,text); canvas.showPage()
  canvas.save(); result=r.extract_pdf(data.getvalue(),30)
  self.assertEqual(result['status'],'ok'); self.assertIn('Second evidence',result['text'])
  for page in result['pages']:
   self.assertIn(['First evidence','Second evidence'][page['page']-1],result['text'][page['start_char']:page['end_char']])
   self.assertNotIn('text',page)
 def test_encrypted_pdf(self):
  if not r.importlib.util.find_spec('pypdf'): self.skipTest('pypdf unavailable')
  from pypdf import PdfWriter
  writer=PdfWriter(); writer.add_blank_page(width=100,height=100); writer.encrypt('test-only-fixture')
  data=io.BytesIO(); writer.write(data)
  with self.assertRaises(r.ReaderError) as ctx: r.extract_pdf(data.getvalue(),1)
  self.assertEqual(ctx.exception.code,'encrypted_pdf')
 def test_mcp_invalid_arguments(self):
  server=m.Server(['example.com'])
  for args in [{'url':BASE['url'],'deadline':True},{'url':[]},{'urls':[]}]:
   with self.subTest(args=args),self.assertRaises(m.ProtocolError): server.tool('grvis_fetch',args)
  with self.assertRaises(m.ProtocolError): server.handle({'jsonrpc':'2.0','id':{},'method':'ping'})
 def test_mcp_lifecycle_and_domain_config(self):
  server=m.Server(['example.com'])
  with self.assertRaises(m.ProtocolError): server.handle({'jsonrpc':'2.0','id':1,'method':'tools/list'})
  result=server.handle({'jsonrpc':'2.0','id':2,'method':'initialize','params':{'protocolVersion':'2025-06-18'}})
  self.assertEqual(result['protocolVersion'],'2025-06-18')
  server.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
  self.assertEqual(len(server.handle({'jsonrpc':'2.0','id':3,'method':'tools/list'})['tools']),3)
  with self.assertRaises(m.ProtocolError): server.tool('grvis_fetch',{'url':BASE['url'],'domains':['bad.example']})
  blocked=server.tool('grvis_fetch',{'url':'https://bad.example/'})
  self.assertTrue(blocked['isError']); self.assertEqual(json.loads(blocked['content'][0]['text'])['reason'],'domain_not_allowed')
 def test_mcp_actual_stdio_subprocess(self):
  requests=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},
            {'jsonrpc':'2.0','method':'notifications/initialized'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'grvis_fetch','arguments':{'url':'https://bad.example/'}}}]
  proc=subprocess.run([sys.executable,'-m','grvis_safe_web_reader.mcp','--allow-domain','example.com'],input='\n'.join(json.dumps(x) for x in requests)+'\n',capture_output=True,text=True,timeout=5)
  self.assertEqual(proc.returncode,0); lines=[json.loads(line) for line in proc.stdout.splitlines()]
  self.assertEqual(len(lines),3); self.assertEqual(lines[1]['id'],2); self.assertTrue(lines[2]['result']['isError'])

if __name__=='__main__': unittest.main(verbosity=2)
