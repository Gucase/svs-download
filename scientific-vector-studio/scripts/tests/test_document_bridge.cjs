// Node-only mock tests; real Illustrator rendering must be verified separately.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '..', 'illustrator_document_bridge.jsx'), 'utf8');
function run(options = {}) {
    const state = {closed: 0, removed: 0, duplicates: [], exports: 0, saves: 0};
    const group = {pageItems: [], remove() { state.removed++; },
        transform(matrix, a, b, c, d, strokeScale) { state.matrix = matrix; state.strokeScale = strokeScale; }};
    const target = {name: 'Existing', artboards: Object.assign([[10, 210, 410, 10]], {getActiveArtboardIndex() {return 0;}}),
        activeLayer: {locked: !!options.locked, visible: true, groupItems: {add() {return group;}}}};
    target.artboards[0] = {artboardRect: [10, 210, 410, 10]};
    function root(name, parent = 'Layer') {
        return {parent: {typename: parent}, duplicate() {
            if (options.copyFailure) throw new Error('copy failed');
            state.duplicates.unshift(name); group.pageItems.push(name);
        }};
    }
    const imported = {name: 'Review', rasterItems: options.raster ? [1] : [], placedItems: [], pathItems: [1, 2],
        textFrames: options.lostText ? [] : [1], gradients: [1], artboards: [{artboardRect: [0, 100, 200, 0]}],
        pageItems: [root('top'), root('nested', 'GroupItem'), root('bottom')],
        close() {state.closed++;}, exportFile() {state.exports++;}, saveAs() {state.saves++;}};
    Object.assign(target, {exportFile: imported.exportFile, saveAs: imported.saveAs});
    const job = Object.assign({source: 'temporary.svg', mode: 'append', placement: 'center', widthFraction: 1,
        heightFraction: 1, expectedText: 1, groupName: 'SVS-test'}, options.job);
    const context = {SVS_DOCUMENT_JOB: job, app: {documents: [target], activeDocument: target,
        open() {state.opened = true; return imported;}, getIdentityMatrix() {return {}; }},
        File: function () {this.exists = !!options.exists;}, IllustratorSaveOptions: function () {},
        ExportOptionsPNG24: function () {}, ExportType: {PNG24: 1},
        UserInteractionLevel: {DONTDISPLAYALERTS: 0}, DocumentColorSpace: {RGB: 1},
        ElementPlacement: {PLACEATBEGINNING: 1}, Transformation: {DOCUMENTORIGIN: 1}, SaveOptions: {DONOTSAVECHANGES: 1}};
    return {result: vm.runInNewContext(source, context), state};
}
let test = run();
assert.match(test.result, /^SVS_IMPORT_OK/);
assert.deepEqual(test.state.duplicates, ['top', 'bottom']);
assert.equal(test.state.matrix.mValueA, 2);
assert.equal(test.state.matrix.mValueTX, 10);
assert.equal(test.state.matrix.mValueTY, 10);
assert.equal(test.state.strokeScale, 200);
assert.equal(test.state.closed, 1);
test = run({job: {mode: 'review'}});
assert.match(test.result, /^SVS_IMPORT_OK/);
assert.equal(test.state.closed, 0);
assert.deepEqual(test.state.duplicates, []);
for (const option of [{raster: true}, {lostText: true}, {copyFailure: true}]) {
    test = run(option);
    assert.match(test.result, /^SVS_IMPORT_FAILED/);
    assert.equal(test.state.closed, 1);
}
assert.equal(run({copyFailure: true}).state.removed, 1);
assert.equal(run({locked: true}).state.opened, undefined);
test = run({exists: true, job: {outputAi: 'protected.ai'}});
assert.match(test.result, /^SVS_IMPORT_OK/); // Optional export failure does not destroy editable output.
assert.match(decodeURIComponent(test.result), /already exists/);
assert.equal(test.state.saves, 0);
assert.equal(test.state.removed, 0);
console.log('PASS: native transfer order, affine fit, review, rollback, protected exports (8 scenarios)');
