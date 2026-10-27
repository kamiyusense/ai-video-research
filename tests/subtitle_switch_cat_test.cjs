'use strict';
const assert = require('node:assert/strict');
const {direction, frameAt, bodyOffset, Play} = require('../automation/subtitle-switch/web/cat.js');
const vectors = [[1,0],[1,1],[0,1],[-1,1],[-1,0],[-1,-1],[0,-1],[1,-1]];
vectors.forEach(([x,y], i) => assert.equal(direction(x,y), i));
assert.equal(direction(100,-.01),0);
assert.equal(direction(100,40),0);
assert.equal(direction(100,45),1);
assert.equal(frameAt({frames: 6, fps: 5, loop: true}, 1400), 1);
for (const elapsed of [900, 1500, 99999]) assert.equal(frameAt({frames: 6, fps: 6, loop: false, hold_last: true}, elapsed), 5);
assert(bodyOffset(2000,220) > bodyOffset(1000,220)); // increasing right offset moves a left-facing cat left
assert.equal(bodyOffset(500,220,true),0);
const manifest = {look:{directions:8}, punch_left:{frames:4,fps:10}, punch_right:{frames:4,fps:10},punch_radius_px:70,punch_cooldown_sec:.6};
const p = new Play(manifest);
assert.equal(p.sample(0),null);
p.pointer(221,0,0);
assert.equal(p.sample(0),null);
p.pointer(200,0,1);
assert.deepEqual(p.sample(1),{group:'look',index:0});
p.pointer(-70,0,10);
assert.deepEqual(p.sample(10),{group:'punch_left',index:0});
assert.deepEqual(p.sample(210),{group:'punch_left',index:2});
p.pointer(0,0,110); // cannot interrupt an active punch
assert.deepEqual(p.sample(110),{group:'punch_left',index:1});
p.pointer(60,0,500); // finished, but still within cooldown
assert.equal(p.sample(500).group,'look');
p.pointer(70,0,610); // exact radius and cooldown boundaries are inclusive
assert.deepEqual(p.sample(610),{group:'punch_right',index:0});
assert.equal(p.sample(3610),null);
const outside = new Play(manifest);
outside.pointer(71,0,0);
assert.equal(outside.sample(1).group,'look');
const absent = new Play(null);
absent.pointer(1,1,0);
assert.equal(absent.sample(0),null);
