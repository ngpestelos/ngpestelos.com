"""Exercise the RoPE playground's shipped script with deterministic frames."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / 'eli5/rotary-position-embeddings/index.html'


class RopePlaygroundTests(unittest.TestCase):
    def test_controls_and_relative_score(self):
        html = PAGE.read_text()
        script = re.search(r'<script id="ropePlayground">(.*?)</script>', html, re.S).group(1)
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required to exercise the playground JavaScript')
        harness = r'''
const vm = require('node:vm'), assert = require('node:assert/strict');
function exercise(reduced) {
  const elements = {}, events = {}, frames = new Map();
  let frameId = 0;
  for (const id of ['separation','gapValue','queryArrow','keyArrow','angleArc',
    'queryPosition','keyPosition','queryAngle','keyAngle','relativeAngle','pairScore',
    'dialDesc','queryToken','keyToken','shiftBoth','playPause','reset','motionNote','shiftReadout']) {
    elements[id] = {value:'2', textContent:'', disabled:false, hidden:false, attrs:{},
      setAttribute(k,v) {this.attrs[k]=String(v);},
      addEventListener(k,f) {this[k]=f;}};
  }
  const media = {matches:reduced, addEventListener(k,f){this[k]=f;}};
  const document = {hidden:false, getElementById:id=>elements[id],
    addEventListener:(k,f)=>events[k]=f};
  vm.runInNewContext(SOURCE, {document, matchMedia:()=>media,
    requestAnimationFrame:f=>{frames.set(++frameId,f);return frameId;},
    cancelAnimationFrame:id=>frames.delete(id)});
  const click = id=>elements[id].click();
  const tick = time=>{const queued=[...frames.values()];frames.clear();queued.forEach(f=>f(time));};
  const gap = n=>{elements.separation.value=String(n);elements.separation.input();};
  const score = ()=>Number(elements.pairScore.textContent);
  const position = id=>Number(elements[id].textContent);
  assert.equal(frames.size,0, 'no autoplay');
  gap(0);assert.equal(score(),1);
  gap(8);assert.ok(Math.abs(score()-Math.cos(8*Math.PI/6))<0.001);
  gap(3);const before=score();
  click('shiftBoth');
  if (!reduced) {tick(0);tick(600);assert.ok(position('queryPosition')>0);tick(1200);}
  assert.equal(score(),before,'common shift preserves pair score');
  assert.equal(position('queryPosition'),1);
  assert.equal(position('keyPosition'),4);
  assert.equal(frames.size,0,'shift ends at integer positions');
  click('playPause');
  if (reduced) {assert.equal(frames.size,0);assert.equal(position('queryPosition'),2);}
  else {
    tick(1500);tick(1800);
    click('playPause');const paused=position('queryPosition');
    assert.equal(frames.size,0);tick(3000);assert.equal(position('queryPosition'),paused);
    click('playPause');assert.equal(frames.size,1);
    assert.equal(position('queryPosition'),paused,'resume preserves paused position');
    document.hidden=true;events.visibilitychange();assert.equal(frames.size,0);
    document.hidden=false;click('playPause');
    media.matches=true;media.change();assert.equal(frames.size,0,'motion preference change stops playback');
    assert.ok(Number.isInteger(position('queryPosition')));
    media.matches=false;media.change();click('playPause');
  }
  click('reset');assert.equal(frames.size,0);
  assert.equal(elements.separation.value,'2');
  assert.equal(position('queryPosition'),0);assert.equal(position('keyPosition'),2);
  assert.ok(Math.abs(score()-0.5)<0.001);
  gap(1);gap(7);gap(0);assert.equal(score(),1,'repeated slider changes');
}
exercise(false);exercise(true);
console.log('PASS: slider extremes/repeats, common-shift invariance, integer endpoints, pause/resume, hidden tab, reduced motion, reset, no autoplay');
'''
        result = subprocess.run([node, '-e', 'const SOURCE = ' + json.dumps(script) + ';\n' + harness],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
