// Runs the exact code of the Sim "Texas checklist" Function block on one file, outside Sim.
// Usage: node harness/run_local.js <workflow.json> < file.json
const fs = require('fs');
const wf = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const block = Object.values(wf.state ? wf.state.blocks : wf.blocks).find((b) => b.name === 'Texas checklist');
const code = block.subBlocks.code.value;
const input = fs.readFileSync(0, 'utf8');
const body = code.split('<start.file>').join('__FILE__');
const fn = new Function('__FILE__', body);
process.stdout.write(JSON.stringify(fn(JSON.parse(input))));
