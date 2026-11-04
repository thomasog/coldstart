const t=require('node:test');const a=require('node:assert');const {add}=require('../src/index.js');
t.test('add',()=>a.equal(add(2,2),4));
