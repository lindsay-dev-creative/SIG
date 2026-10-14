/**
 * SIGNATURE SOCIETY · LAUNCH PLAN TICKS
 * =============================================================
 * One Google Apps Script web app behind the two launch plans:
 *   sig-2026-wbd-launch-plan.html      (client)
 *   sig-2026-wbd-int-launch-plan.html  (internal)
 *
 * It keeps one shared list of ticked tasks in a Google Sheet, so a task
 * ticked by anyone, on either page, in any browser, shows as ticked for
 * everyone. The pages poll it every 30 seconds.
 *
 * WHO CAN READ AND WRITE
 * ----------------------
 * There is no passcode. The /exec URL sits in the page source, so anyone
 * who finds it can tick or untick tasks. It only ever stores task IDs and
 * true/false, so nothing in it matters if it were public.
 *
 * DEPLOYING (once)
 * ----------------
 * 1. Sign in to Google as lindsay@lindsaydev.com.
 * 2. script.google.com > New project. Paste this file in.
 *    Name it "SIG launch plan ticks".
 * 3. Pick setup in the function menu and click Run. Allow the access it
 *    asks for. The log prints the new Sheet's link.
 * 4. Deploy > New deployment > type: Web app.
 *    Execute as: Me. Who has access: Anyone. Click Deploy.
 * 5. Copy the Web app URL (ends in /exec) and send it to Claude.
 */

var SHEET_NAME = 'Ticks';
var HEADER = ['Task ID', 'Done', 'Updated'];

function setup() {
  var ss = SpreadsheetApp.create('SIG launch plan ticks');
  var sh = ss.getSheets()[0];
  sh.setName(SHEET_NAME);
  sh.appendRow(HEADER);
  sh.setFrozenRows(1);
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());
  Logger.log('Sheet: ' + ss.getUrl());
}

function sheet_() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!id) throw new Error('Run setup() first.');
  return SpreadsheetApp.openById(id).getSheetByName(SHEET_NAME);
}

function json_(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}

// GET: every task's state, as { "d14-1": true, ... }
function doGet() {
  var out = {};
  sheet_().getDataRange().getValues().slice(1).forEach(function (row) {
    if (row[0]) out[String(row[0])] = row[1] === true;
  });
  return json_(out);
}

// POST: [{ "id": "d14-1", "done": true }, ...] (or one object)
function doPost(e) {
  var body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return json_({ ok: false, error: 'bad json' }); }
  var items = (Array.isArray(body) ? body : [body]).filter(function (it) {
    return it && /^[a-z0-9-]{1,24}$/.test(it.id) && typeof it.done === 'boolean';
  }).slice(0, 300);
  if (!items.length) return json_({ ok: false, error: 'nothing to save' });

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    var sh = sheet_();
    var values = sh.getDataRange().getValues();
    var rowOf = {};
    for (var i = 1; i < values.length; i++) rowOf[String(values[i][0])] = i + 1;
    var now = new Date();
    items.forEach(function (it) {
      if (rowOf[it.id]) {
        sh.getRange(rowOf[it.id], 2, 1, 2).setValues([[it.done, now]]);
      } else {
        sh.appendRow([it.id, it.done, now]);
        rowOf[it.id] = sh.getLastRow();
      }
    });
  } finally {
    lock.releaseLock();
  }
  return json_({ ok: true, saved: items.length });
}
