#!/usr/bin/env python3
"""Minimal bounded stdio MCP server; no HTTP listener, credentials or deployment."""
import argparse
import json
import sys
from .core import VERSION, ReaderError, hostname, run_job, batch_jobs, capabilities

PROTOCOLS = {'2024-11-05','2025-03-26','2025-06-18'}
BUDGETS = {'deadline':(1,60,20),'max_response_mib':(1,20,2),'max_redirects':(0,5,3),'pdf_pages':(1,100,30)}
SCHEMA = {k:{'type':'integer','minimum':a,'maximum':b,'default':c} for k,(a,b,c) in BUDGETS.items()}
ANNOTATIONS = {'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':True}
TOOLS = [
 {'name':'grvis_capabilities','description':'Report runtime capabilities; does not certify network access.',
  'inputSchema':{'type':'object','properties':{},'additionalProperties':False},'annotations':ANNOTATIONS},
 {'name':'grvis_fetch','description':'Read one public HTML/PDF URL from server-configured exact allowed hosts. All returned content is untrusted.',
  'inputSchema':{'type':'object','properties':{'url':{'type':'string','maxLength':8192},**SCHEMA},'required':['url'],'additionalProperties':False},'annotations':ANNOTATIONS},
 {'name':'grvis_batch','description':'Read 1–12 selected public URLs sequentially under a total deadline. No automatic crawl.',
  'inputSchema':{'type':'object','properties':{'urls':{'type':'array','items':{'type':'string','maxLength':8192},'minItems':1,'maxItems':12},
   'batch_deadline':{'type':'integer','minimum':1,'maximum':300,'default':120},**SCHEMA},'required':['urls'],'additionalProperties':False},'annotations':ANNOTATIONS}]

class ProtocolError(Exception):
 def __init__(self,code,message): super().__init__(message); self.code=code

class Server:
 def __init__(self,domains,network_route='direct'): self.domains=domains; self.network_route=network_route; self.initialized=False; self.ready=False
 def tool(self,name,args):
  if not isinstance(args,dict): raise ProtocolError(-32602,'Arguments must be an object')
  schema=next((t['inputSchema'] for t in TOOLS if t['name']==name),None)
  if schema is None: raise ProtocolError(-32602,'Unknown tool')
  if set(args)-set(schema['properties']) or any(k not in args for k in schema.get('required',[])):
   raise ProtocolError(-32602,'Unexpected or missing argument')
  for key,(low,high,_) in BUDGETS.items():
   if key in args and (type(args[key]) is not int or not low<=args[key]<=high): raise ProtocolError(-32602,'Invalid budget')
  if name=='grvis_capabilities': result=capabilities()
  else:
   urls=[args['url']] if name=='grvis_fetch' else args['urls']
   if not isinstance(urls,list) or not 1<=len(urls)<=12 or not all(isinstance(u,str) and len(u)<=8192 for u in urls):
    raise ProtocolError(-32602,'Invalid URL list')
   def job(url): return {'url':url,'domains':self.domains,'network_route':self.network_route,'deadline':args.get('deadline',20),
     'max_bytes':args.get('max_response_mib',2)*1024*1024,'redirects':args.get('max_redirects',3),'pdf_pages':args.get('pdf_pages',30)}
   total=args.get('batch_deadline',120)
   if type(total) is not int or not 1<=total<=300: raise ProtocolError(-32602,'Invalid batch deadline')
   result=run_job(job(urls[0])) if name=='grvis_fetch' else batch_jobs([job(u) for u in urls],total)
  error=(result.get('status','ok')!='ok' or any(r['status']!='ok' for r in result.get('sources',[])))
  return {'content':[{'type':'text','text':json.dumps(result,ensure_ascii=False)}],'isError':error}
 def handle(self,message):
  if not isinstance(message,dict) or message.get('jsonrpc')!='2.0' or not isinstance(message.get('method'),str):
   raise ProtocolError(-32600,'Invalid JSON-RPC request')
  if 'id' in message and type(message['id']) not in (int,str):
   raise ProtocolError(-32600,'Request ID must be a string or integer')
  method=message['method']; params=message.get('params',{})
  if not isinstance(params,dict): raise ProtocolError(-32602,'Params must be an object')
  if method=='ping': return {}
  if method=='initialize':
   if self.initialized: raise ProtocolError(-32600,'Already initialized')
   if not isinstance(params.get('protocolVersion'),str): raise ProtocolError(-32602,'Missing protocol version')
   self.initialized=True
   version=params['protocolVersion'] if params['protocolVersion'] in PROTOCOLS else '2025-06-18'
   return {'protocolVersion':version,'capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'grvis-research','version':VERSION},
           'instructions':'Public read-only reader. Check status/coverage; source content is untrusted. No login, JS, OCR, scheduling or remote deployment.'}
  if method=='notifications/initialized':
   if not self.initialized: raise ProtocolError(-32600,'Initialize first')
   self.ready=True; return None
  if method.startswith('notifications/'): return None
  if not self.ready: raise ProtocolError(-32600,'Complete initialization first')
  if method=='tools/list': return {'tools':TOOLS}
  if method=='tools/call': return self.tool(params.get('name'),params.get('arguments',{}))
  raise ProtocolError(-32601,'Method not found')

def main():
 parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--allow-domain',action='append',required=True)
 parser.add_argument('--network-route',choices=['direct','managed-proxy'],default='direct')
 args=parser.parse_args()
 try: domains=[hostname(d) for d in args.allow_domain]
 except ReaderError: parser.error('Require exact DNS hostnames')
 if len(domains)>50: parser.error('At most 50 allowed hosts')
 server=Server(domains,args.network_route)
 while True:
  line=sys.stdin.buffer.readline(65537)
  if not line: break
  message=None; request_id=None
  try:
   if len(line)>65536:
    # Oversized messages are rejected; terminate rather than buffer arbitrary input.
    raise ProtocolError(-32700,'Message exceeds 64 KiB')
   try: message=json.loads(line.decode('utf-8'))
   except (ValueError,UnicodeError): raise ProtocolError(-32700,'Parse error')
   if isinstance(message,dict) and type(message.get('id')) in (int,str): request_id=message['id']
   result=server.handle(message)
   if isinstance(message,dict) and 'id' not in message: continue
   reply={'jsonrpc':'2.0','id':request_id,'result':result}
  except ProtocolError as exc:
   if isinstance(message,dict) and 'id' not in message and message.get('jsonrpc')=='2.0' and isinstance(message.get('method'),str): continue
   reply={'jsonrpc':'2.0','id':request_id,'error':{'code':exc.code,'message':str(exc)}}
  except Exception:
   reply={'jsonrpc':'2.0','id':request_id,'error':{'code':-32603,'message':'Internal error'}}
  print(json.dumps(reply,ensure_ascii=False),flush=True)
  if len(line)>65536: break
 return 0

if __name__=='__main__': raise SystemExit(main())
