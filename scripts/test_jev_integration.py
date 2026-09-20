"""Offline integration tests. No outbound API calls and no Codex execution."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
S=ROOT/'skills'/'workflow'
sys.path.insert(0,str(S/'scripts'))
import jev_z80 as engine
import jev_runtime as rt


class JevCase(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='z80-jev-test-')
        self.addCleanup(self.temp.cleanup)
        self.policy=rt.load_policy()
        self.session=Path(rt.init_task(self.policy,Path(self.temp.name))['task_dir'])
        self.client=Path(self.temp.name)/'client.py'
        self.client.write_text('# placeholder; runner is simulated\n')
        self.calls=[]
        self.levels={'A':1,'B':4}
        self.confidences={}
        self.choice=None
        self.corrupt=None

    def packet(self,domain='optimize'):
        return rt.read_json(S/'examples'/f'jev-{domain}.json')

    def route(self):
        return rt.read_json(S/'examples'/'jev-route.json')

    def fake(self,client,command,request,model,policy):
        payload=rt.read_json(request)
        self.calls.append((command,deepcopy(payload)))
        if command=='check':
            return {'ok':True,'requests_sent':0,'mode':'offline-schema-check','model':model,
                    'questions':len(payload['questions'])}
        answers={}
        for key,q in payload['questions'].items():
            if q['type']=='score':
                ident,dim=key.rsplit('__',1)
                level=self.levels.get(ident,2)
                probs={str(i):float(i==level) for i in range(len(q['criteria']))}
                answers[key]={'type':'score','score':level,'confidence':self.confidences.get(key,1.0),
                              'probabilities':probs}
            else:
                choice=self.choice or next(k for k in q['criteria'] if k!='coordinator')
                answers[key]={'type':'choice','choice':choice,'confidence':self.confidences.get(key,1.0),
                              'probabilities':{k:float(k==choice) for k in q['criteria']}}
        result={'ok':True,'requests_sent':1,'http_status':200,'requested_model':model,
                'endpoint':rt.ENDPOINT,'request_sha256':hashlib.sha256(rt.encode(payload)).hexdigest(),
                'response':{'model':'jev-1.13','answers':answers,'usage':{'input_tokens':100,'output_tokens':10}}}
        if self.corrupt:
            self.corrupt(result)
        return result

    def score(self,packet=None,**kw):
        return engine.score_packet(packet or self.packet(),self.session,self.policy,self.client,self.fake,**kw)

    def call_route(self,packet=None):
        return engine.route_packet(packet or self.route(),self.session,self.policy,self.client,self.fake)

    def test_scoring_all_domains_four_dimensions(self):
        for domain in ('audit','shrink','optimize'):
            with self.subTest(domain=domain):
                self.session=Path(rt.init_task(self.policy,Path(self.temp.name))['task_dir'])
                result=self.score(self.packet(domain))
                self.assertEqual(result['baseline_order'],['A','B'])
                self.assertEqual(result['recommended_order'],['B','A'])
                rows={c['id']:c for c in result['candidates']}
                self.assertEqual(rows['A']['jev']['score_0_100'],25)
                self.assertEqual(rows['B']['jev']['score_0_100'],100)
                self.assertEqual(set(rows['A']['jev']['dimensions']),set(engine.DIMENSIONS))
                self.assertFalse(result['scores_are_measurements'])
                self.assertEqual(result['receipts'][0]['query_status'],'received')

    def test_native_receipt_matches_actual_wire_bytes(self):
        result=self.score()
        run=self.calls[-1][1]
        self.assertEqual(result['receipts'][0]['original_request_sha256'],hashlib.sha256(rt.encode(run)).hexdigest())
        self.assertEqual(len(run['questions']),8)
        self.assertTrue(all(q['type']=='score' for q in run['questions'].values()))

    def test_request_omits_baseline_permissions_and_rank(self):
        packet=self.packet()
        packet['candidates'][0]['baseline']['private_marker']='DO_NOT_SEND_THIS_BASELINE'
        self.score(packet)
        wire=rt.encode(self.calls[-1][1]).decode()
        self.assertNotIn('DO_NOT_SEND_THIS_BASELINE',wire)
        self.assertNotIn('policy_allowed',wire)
        self.assertNotIn('baseline',self.calls[-1][1]['state']['items']['A'])
        self.assertIn("state.items['A']",self.calls[-1][1]['questions']['A__support']['instructions'])

    def test_input_records_not_mutated(self):
        packet=self.packet()
        before=deepcopy(packet)
        self.score(packet)
        self.assertEqual(before,packet)

    def test_existing_optimizer_numeric_score_preserved(self):
        packet=self.packet()
        packet['candidates'][0]['baseline']['speed']=99
        expected=deepcopy(packet['candidates'][0]['baseline'])
        m=engine.optimize_module()
        expected['score']=m.score(expected,'speed',set(),'')
        result=self.score(packet,profile='speed')
        row=next(x for x in result['candidates'] if x['id']=='A')
        self.assertEqual(row['baseline'],expected)
        self.assertIn('schema_warnings',row['baseline'])

    def test_original_evidence_demotion_not_jev_promotion(self):
        packet=self.packet()
        packet['candidates'][0]['baseline'].update(confidence='PROVEN',evidence=[])
        result=self.score(packet)
        row=next(x for x in result['candidates'] if x['id']=='A')
        self.assertEqual(row['baseline']['confidence'],'SPECULATIVE')
        self.assertIn('evidence_gate',row['baseline'])

    def test_original_policy_veto(self):
        packet=self.packet()
        packet['candidates'][1]['baseline'].update(tags=['smc'],lane='DANGEROUS')
        result=self.score(packet,forbidden='smc')
        row=next(x for x in result['candidates'] if x['id']=='B')
        self.assertEqual(row['baseline']['score'],-999)
        self.assertFalse(row['eligible'])
        self.assertIsNone(row['jev']['score_0_100'])
        self.assertNotIn('B',self.calls[-1][1]['state']['items'])

    def test_wrong_target_and_overlay_constraints(self):
        packet=self.packet()
        packet['candidates'][0]['baseline']['targets']=['zx-next']
        p=Path(self.temp.name)/'z80opt.toml'
        p.write_text('target = "zx48"\n[constraints]\noverlay_size = 100\n')
        packet['candidates'][1]['baseline'].update(tags=['banking_changes'],overlay_after=101)
        result=self.score(packet,policy_path=str(p))
        self.assertTrue(all(not x['eligible'] for x in result['candidates']))
        self.assertEqual(self.calls,[])

    def test_low_dimension_confidence_preserves_entire_group(self):
        self.confidences['A__support']=.84
        result=self.score()
        self.assertEqual(result['recommended_order'],['A','B'])
        self.assertEqual(result['candidates'][0]['jev']['status'],'coordinator_review')
        self.assertEqual(result['candidates'][0]['jev']['score_0_100'],25)
        self.assertNotEqual(result['candidates'][0]['jev']['score_0_100'],0)

    def test_exact_threshold_admitted(self):
        for ident in ('A','B'):
            for dim,threshold in self.policy['scoring']['optimize']['thresholds'].items():
                self.confidences[ident+'__'+dim]=threshold
        self.assertEqual(self.score()['recommended_order'],['B','A'])

    def test_zero_score_is_real_not_missing(self):
        self.levels['A']=0
        result=self.score()
        self.assertEqual(result['candidates'][0]['jev']['score_0_100'],0)
        self.assertEqual(result['candidates'][0]['jev']['status'],'accepted')

    def test_equal_scores_stable_order(self):
        self.levels['B']=1
        self.assertEqual(self.score()['recommended_order'],['A','B'])

    def test_audit_cannot_cross_severity_confidence_type(self):
        for field,value in [('severity','LOW'),('confidence','SUSPICIOUS'),('type','OBSERVATION')]:
            with self.subTest(field=field):
                self.session=Path(rt.init_task(self.policy,Path(self.temp.name))['task_dir'])
                packet=self.packet('audit')
                packet['candidates'][1]['baseline'][field]=value
                result=self.score(packet)
                self.assertEqual(result['recommended_order'],['A','B'])
                self.assertEqual(result['candidates'][1]['baseline'][field],value)

    def test_shrink_cannot_cross_safety_certainty_pressure_or_net(self):
        for field,value in [('safety','AGGRESSIVE'),('certainty','REQUIERE BUILD'),
                            ('pressure_target','peak RAM'),('net_bytes',500)]:
            with self.subTest(field=field):
                self.session=Path(rt.init_task(self.policy,Path(self.temp.name))['task_dir'])
                packet=self.packet('shrink')
                packet['candidates'][1]['baseline'][field]=value
                self.assertEqual(self.score(packet)['recommended_order'],['A','B'])

    def test_shrink_dependencies_preserved_no_totals(self):
        packet=self.packet('shrink')
        packet['candidates'][1]['baseline']['dependency']='exclusive_with:A'
        result=self.score(packet)
        self.assertEqual(result['candidates'][1]['baseline']['dependency'],'exclusive_with:A')
        self.assertNotIn('total_bytes',result)

    def test_optimizer_cannot_cross_native_score(self):
        packet=self.packet()
        packet['candidates'][0]['baseline']['latency']=5
        self.assertEqual(self.score(packet)['recommended_order'],['A','B'])

    def test_gate_false_prevents_network_for_that_card(self):
        for gate in engine.SCORE_GATES:
            with self.subTest(gate=gate):
                self.session=Path(rt.init_task(self.policy,Path(self.temp.name))['task_dir'])
                packet=self.packet()
                packet['candidates'][0]['gates'][gate]=False
                result=self.score(packet)
                self.assertEqual(result['recommended_order'],['A','B'])
                self.assertNotIn('A',self.calls[-1][1]['state']['items'])

    def test_empty_or_stale_evidence_unscored(self):
        for evidence in ([],[{'ref':'source:1','excerpt':'old','current':False}]):
            packet=self.packet()
            packet['candidates'][0]['context']['evidence']=evidence
            result=self.score(packet)
            self.assertEqual(result['candidates'][0]['jev']['reason'],'current_excerpt_required')
            self.assertIsNone(result['candidates'][0]['jev']['score_0_100'])

    def test_no_external_authorization(self):
        packet=self.packet()
        packet['external_data_authorized']=False
        result=self.score(packet)
        self.assertEqual(self.calls,[])
        self.assertEqual(result['recommended_order'],['A','B'])
        self.assertEqual(result['receipts'][0]['reason'],'external_data_not_authorized')

    def test_cache_reuse_even_if_network_now_disallowed(self):
        first=self.score()
        packet=self.packet()
        packet['external_data_authorized']=False
        second=self.score(packet)
        self.assertEqual(second['receipts'][0]['query_status'],'cache_hit')
        self.assertEqual(second['receipts'][0]['requests_sent'],0)
        self.assertEqual(second['receipts'][0]['usage'],{})
        self.assertEqual(first['recommended_order'],second['recommended_order'])
        self.assertEqual(len(self.calls),2)

    def test_snapshot_change_invalidates_cache(self):
        self.score()
        packet=self.packet()
        packet['snapshot']='new-dirty-source-hash'
        second=self.score(packet)
        self.assertEqual(second['receipts'][0]['query_status'],'received')
        self.assertEqual(second['receipts'][0]['calls_reserved'],2)

    def test_new_gate_reapplied_after_prior_call(self):
        self.score()
        packet=self.packet()
        packet['candidates'][1]['gates']['policy_allowed']=False
        second=self.score(packet)
        self.assertFalse(second['candidates'][1]['eligible'])
        self.assertEqual(second['recommended_order'],['A','B'])

    def test_shared_routing_scoring_budget(self):
        self.call_route()
        self.score()
        packet=self.route()
        packet['snapshot']='new-route'
        third=self.call_route(packet)
        self.assertEqual(third['receipt']['reason'],'task_call_budget_exhausted')
        self.assertEqual(len([x for x in self.calls if x[0]=='run']),2)

    def test_batch_32_questions_and_never_drops_unscored(self):
        self.call_route()
        packet=self.packet()
        template=packet['candidates'][0]
        packet['candidates']=[{**deepcopy(template),'id':f'C{i}'} for i in range(19)]
        result=self.score(packet)
        self.assertEqual(len(result['candidates']),19)
        run=[p for command,p in self.calls if command=='run']
        self.assertEqual(len(run),2)
        self.assertEqual(len(run[1]['questions']),32)
        statuses=[r['jev']['status'] for r in result['candidates']]
        self.assertEqual(statuses.count('accepted'),8)
        self.assertEqual(statuses.count('not_scored'),11)
        self.assertEqual(result['baseline_order'],result['recommended_order'])

    def test_zero_budget(self):
        self.session=Path(rt.init_task(self.policy,Path(self.temp.name),max_calls=0)['task_dir'])
        result=self.score()
        self.assertEqual(self.calls,[])
        self.assertEqual(result['receipts'][0]['reason'],'task_call_budget_exhausted')

    def test_http_failure_no_retry(self):
        def runner(*args):
            if args[1]=='run':
                self.calls.append(('failed_run',{}))
                raise rt.RouterError('http_500')
            return self.fake(*args)
        first=engine.score_packet(self.packet(),self.session,self.policy,self.client,runner)
        self.assertEqual(first['receipts'][0]['http_status'],500)
        packet=self.packet();packet['snapshot']='changed'
        second=engine.score_packet(packet,self.session,self.policy,self.client,runner)
        self.assertEqual(second['receipts'][0]['reason'],'service_disabled_for_task')
        self.assertEqual(len([x for x in self.calls if x[0]=='failed_run']),1)

    def test_network_unknown_count_not_invented(self):
        def runner(*args):
            if args[1]=='run':raise rt.RouterError('client_timeout')
            return self.fake(*args)
        result=engine.score_packet(self.packet(),self.session,self.policy,self.client,runner)
        receipt=result['receipts'][0]
        self.assertIsNone(receipt['requests_sent'])
        self.assertTrue(receipt['network_attempted'])
        self.assertEqual(receipt['calls_reserved'],1)

    def test_missing_client_keeps_baseline(self):
        result=engine.score_packet(self.packet(),self.session,self.policy,Path(self.temp.name)/'absent.py')
        self.assertEqual(result['receipts'][0]['reason'],'client_not_found')
        self.assertEqual(result['recommended_order'],['A','B'])
        self.assertEqual(result['receipts'][0]['requests_sent'],0)

    def test_invalid_native_receipts_fail_closed(self):
        cases={
          'hash':lambda r:r.update(request_sha256='0'*64),
          'endpoint':lambda r:r.update(endpoint='https://invalid.example'),
          'model':lambda r:r['response'].update(model='some-other-model'),
          'bool_http':lambda r:r.update(http_status=True),
          'missing_answer':lambda r:r['response']['answers'].pop('A__support'),
          'nan':lambda r:r['response']['answers']['A__support'].update(confidence=float('nan')),
          'wrong_type':lambda r:r['response']['answers']['A__support'].update(type='choice'),
          'mismatched_score':lambda r:r['response']['answers']['A__support'].update(score=3.8),
          'probabilities':lambda r:r['response']['answers']['A__support'].update(probabilities={'0':1}),
          'out_of_scale':lambda r:r['response']['answers']['A__support'].update(score=9),
          'bool_score':lambda r:r['response']['answers']['A__support'].update(score=True),
          'requests_count':lambda r:r.update(requests_sent=0)}
        for case,change in cases.items():
            with self.subTest(case=case):
                self.session=Path(rt.init_task(self.policy,Path(self.temp.name))['task_dir'])
                self.corrupt=change
                result=self.score()
                self.assertEqual(result['receipts'][0]['query_status'],'failed')
                self.assertEqual(result['recommended_order'],['A','B'])
                self.assertTrue(all(c['jev']['score_0_100'] is None for c in result['candidates']))

    def test_routing_returns_real_route_and_threshold(self):
        result=self.call_route()
        self.assertEqual(result['decisions'][0]['route'],'locate_sources')
        self.assertEqual(result['decisions'][0]['threshold'],.9)
        self.assertEqual(result['decisions'][0]['source'],'jev')

    def test_low_confidence_route_coordinator_not_astra(self):
        self.confidences['next_step']=.89
        result=self.call_route()
        self.assertEqual(result['decisions'][0]['route'],'coordinator')
        self.assertNotIn('astra',rt.encode(result).decode())

    def test_explicit_route_no_network(self):
        packet=self.route()
        packet['decisions'][0]['required_route']='locate_sources'
        result=self.call_route(packet)
        self.assertEqual(self.calls,[])
        self.assertEqual(result['decisions'][0]['source'],'rule')

    def test_assignment_light_medium_never_delegates(self):
        for level in ('light','medium'):
            packet=self.route();packet['level']=level
            item=packet['decisions'][0]
            item.update(action='assignment',allowed_routes=['mechanical','coding','synthesis','causal'])
            item['gates'].update(dispatch_gate=True,model_selection_available=True)
            result=self.call_route(packet)
            self.assertEqual(result['decisions'][0]['route'],'coordinator')
        self.assertEqual(self.calls,[])

    def test_assignment_uses_existing_roles_table(self):
        packet=self.route();packet['level']='heavy'
        item=packet['decisions'][0]
        item.update(action='assignment',allowed_routes=['mechanical','coding','synthesis','causal'])
        item['gates'].update(dispatch_gate=True,model_selection_available=True)
        self.choice='causal'
        result=self.call_route(packet)
        row=result['decisions'][0]['model_preference']
        self.assertEqual(row['requested_model'],'gpt-5.6-sol')
        self.assertEqual(row['requested_effort'],'xhigh')
        self.assertFalse(row['runtime_confirmed']);self.assertFalse(row['worker_spawned'])

    def test_explicit_model_choice_not_overridden(self):
        packet=self.route();packet['level']='heavy'
        item=packet['decisions'][0]
        item.update(action='assignment',allowed_routes=['mechanical','coding','synthesis','causal'])
        item['gates'].update(dispatch_gate=True,model_selection_available=True,explicit_model_selection=True)
        self.call_route(packet)
        self.assertEqual(self.calls,[])

    def test_unavailable_route_not_forced_to_cheaper_class(self):
        packet=self.route()
        packet['decisions'][0]['allowed_routes']=['locate_sources']
        self.choice='code_review'
        result=self.call_route(packet)
        self.assertEqual(result['decisions'][0]['route'],'coordinator')
        self.assertEqual(result['decisions'][0]['reason'],'route_not_authorized')
        self.assertIn('code_review',self.calls[-1][1]['questions']['next_step']['criteria'])

    def test_confirmation_and_ambiguous_intent_no_network(self):
        packet=self.route()
        packet['decisions'][0]['gates']['confirmation_required']=True
        self.call_route(packet)
        packet=self.route();item=packet['decisions'][0]
        item.update(action='specialist',allowed_routes=['audit-z80','optimize-z80'])
        item['gates']['ambiguous_primary']=True
        self.call_route(packet)
        self.assertEqual(self.calls,[])

    def test_specialist_route_only_existing_skill(self):
        packet=self.route();item=packet['decisions'][0]
        item.update(action='specialist',allowed_routes=['audit-z80','debug-z80'])
        self.choice='audit-z80'
        result=self.call_route(packet)
        self.assertEqual(result['decisions'][0]['route'],'audit-z80')
        for route in self.policy['actions']['specialist']['routes']:
            self.assertTrue((ROOT/'skills'/route/'SKILL.md').is_file())

    def test_failed_offline_schema_check_never_sends(self):
        def runner(*args):
            self.assertEqual(args[1],'check')
            return {'ok':False}
        result=engine.score_packet(self.packet(),self.session,self.policy,self.client,runner)
        self.assertEqual(result['receipts'][0]['requests_sent'],0)
        self.assertEqual(result['receipts'][0]['calls_reserved'],0)

    def test_status_and_audit_no_raw_excerpts(self):
        packet=self.packet()
        packet['candidates'][0]['context']['evidence'][0]['excerpt']='SECRET_SOURCE_MARKER_FOR_TEST'
        self.score(packet)
        before=len(self.calls)
        result=rt.inspect_task(self.session,self.policy)
        self.assertEqual(len(self.calls),before)
        self.assertNotIn('SECRET_SOURCE_MARKER_FOR_TEST',rt.encode(result).decode())
        self.assertNotIn('SECRET_SOURCE_MARKER_FOR_TEST',(self.session/'state.json').read_text())
        self.assertTrue(any(e.get('operation')=='score' for e in result['entries']))
        self.assertEqual(list(self.session.glob('request-*')),[])

    def test_policy_change_invalidates_session(self):
        altered=deepcopy(self.policy)
        altered['scoring']['audit']['thresholds']['support']=.86
        with self.assertRaises(rt.RouterError):
            rt.task_model(self.session,altered)

    def test_stale_lock_blocks_extra_calls(self):
        (self.session/'.router.lock').touch()
        with self.assertRaises(rt.RouterError):self.score()
        self.assertEqual(self.calls,[])

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for raw in (b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":1e999}',b'not-json'):
            with self.subTest(raw=raw),self.assertRaises(rt.RouterError):rt.decode(raw)

    def test_invalid_packets(self):
        changes=[lambda p:p.update(external_data_authorized=1),lambda p:p.update(snapshot=''),
          lambda p:p.update(schema_version=True),lambda p:p.update(candidates=[]),
          lambda p:p['candidates'][1].update(id='A'),lambda p:p['candidates'][0].update(id='../A'),
          lambda p:p['candidates'][0]['gates'].update(current_anchor=1),
          lambda p:p['candidates'][0]['context']['evidence'][0].update(current='yes')]
        for change in changes:
            packet=self.packet();change(packet)
            with self.subTest(change=change),self.assertRaises(rt.RouterError):self.score(packet)
        self.assertEqual(self.calls,[])

    def test_malformed_field_types_fail_as_validation_errors(self):
        for field,value in [('domain',[]),('domain',{}),('objective',[]),('snapshot',False)]:
            packet=self.packet();packet[field]=value
            with self.subTest(field=field,value=value),self.assertRaises(rt.RouterError):self.score(packet)
        for field in ('severity','confidence','type'):
            packet=self.packet('audit');packet['candidates'][0]['baseline'][field]=[]
            with self.subTest(field=field),self.assertRaises(rt.RouterError):self.score(packet)
        for field in ('safety','certainty'):
            packet=self.packet('shrink');packet['candidates'][0]['baseline'][field]={}
            with self.subTest(field=field),self.assertRaises(rt.RouterError):self.score(packet)
        packet=self.route();packet['level']=[]
        with self.assertRaises(rt.RouterError):self.call_route(packet)
        self.assertEqual(self.calls,[])

    def test_payload_size_splits_without_truncating_evidence(self):
        packet=self.packet()
        extra=(self.policy['max_packet_bytes']-len(rt.encode(packet))-2000)//2
        for item in packet['candidates']:
            item['context']['evidence'][0]['excerpt']='x'*extra
        self.assertLess(len(rt.encode(packet)),self.policy['max_packet_bytes'])
        result=self.score(packet)
        self.assertEqual(len(result['receipts']),2)
        self.assertTrue(all(r['query_status']=='received' for r in result['receipts']))
        for command,payload in self.calls:
            self.assertLessEqual(len(rt.encode(payload)),self.policy['max_packet_bytes'])
            self.assertEqual(len(next(iter(payload['state']['items'].values()))['evidence'][0]['excerpt']),extra)

    def test_local_model_rows_all_match_original_defaults(self):
        expected=[('gpt-5.6-luna','max'),('gpt-5.6-sol','high'),
                  ('gpt-5.6-sol','high'),('gpt-5.6-sol','xhigh')]
        for number,(model,effort) in enumerate(expected,1):
            result=engine.model_preference(number)
            self.assertEqual((result['requested_model'],result['requested_effort']),(model,effort))
            self.assertFalse(result['worker_spawned'])

    def test_cli_from_arbitrary_cwd_and_space_path(self):
        directory=Path(self.temp.name)/'path with spaces';directory.mkdir()
        script=S/'scripts'/'jev_z80.py'
        init=subprocess.run([sys.executable,str(script),'init','--max-calls','0'],cwd=directory,
                            capture_output=True,text=True)
        self.assertEqual(init.returncode,0,init.stderr)
        task=Path(json.loads(init.stdout)['task_dir'])
        import shutil
        self.addCleanup(shutil.rmtree,task)
        result=subprocess.run([sys.executable,str(script),'score','--task-dir',str(task),
                               '--input',str(S/'examples'/'jev-optimize.json')],cwd=directory,
                               capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        data=json.loads(result.stdout)
        self.assertEqual(data['receipts'][0]['reason'],'task_call_budget_exhausted')
        self.assertEqual(list(directory.iterdir()),[])

    def test_no_paid_model_escalation(self):
        with self.assertRaises(rt.RouterError):rt.init_task(self.policy,Path(self.temp.name),model='gpt-6-astra')
        self.assertEqual(rt.task_model(self.session,self.policy),'jev-1.13-free')

    def test_client_override_is_explicit_path_only(self):
        with patch.dict(os.environ,{'Z80_JEV_CLIENT':str(self.client)}):
            self.assertEqual(rt.locate_client(),self.client.resolve())

    def test_original_functions_not_edited_contract(self):
        # This scorer remains a complete independent CLI with its original names.
        module=engine.optimize_module()
        for name in ('score','load_policy_data','load_forbidden','load_target','load_constraints','main'):
            self.assertTrue(callable(getattr(module,name)))

    def test_hooks_exist_and_output_yaml_unchanged_by_hook(self):
        for skill in ('audit-z80','shrink-z80','optimize-z80'):
            text=(ROOT/'skills'/skill/'SKILL.md').read_text()
            self.assertIn('## Automatic proposal scoring',text)
            self.assertIn('jev-scoring.md',text)
        self.assertIn('Apply [Jev](references/jev.md) for unresolved routing.',(S/'SKILL.md').read_text())
        self.assertTrue((S/'agents'/'openai.yaml').is_file())


if __name__=='__main__':unittest.main()
