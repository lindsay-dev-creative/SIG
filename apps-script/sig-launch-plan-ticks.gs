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
 * It also keeps the owner tags (You, Matt, Morgan, Both, Claude) changed on
 * the internal plan, in a second tab called Owners, so the client plan
 * shows them too.
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
 *
 * UPDATING (after pasting a new version of this file)
 * ---------------------------------------------------
 * Deploy > Manage deployments > pencil icon > Version: New version > Deploy.
 * The URL stays the same. The Owners tab is made on first use.
 */

var SHEET_NAME = 'Ticks';
var HEADER = ['Task ID', 'Done', 'Updated'];
var WHO_SHEET = 'Owners';
var WHO_HEADER = ['Task ID', 'Owners', 'Updated'];
var WHO_RE = /^((you|matt|morgan|both|claude)(,(you|matt|morgan|both|claude))*)?$/;

function setup() {
  var ss = SpreadsheetApp.create('SIG launch plan ticks');
  var sh = ss.getSheets()[0];
  sh.setName(SHEET_NAME);
  sh.appendRow(HEADER);
  sh.setFrozenRows(1);
  PropertiesService.getScriptProperties().setProperty('SHEET_ID', ss.getId());
  Logger.log('Sheet: ' + ss.getUrl());
}

function book_() {
  var id = PropertiesService.getScriptProperties().getProperty('SHEET_ID');
  if (!id) throw new Error('Run setup() first.');
  return SpreadsheetApp.openById(id);
}

function sheet_() {
  return book_().getSheetByName(SHEET_NAME);
}

function whoSheet_() {
  var ss = book_();
  var sh = ss.getSheetByName(WHO_SHEET);
  if (!sh) {
    sh = ss.insertSheet(WHO_SHEET);
    sh.appendRow(WHO_HEADER);
    sh.setFrozenRows(1);
    sh.getRange('B:B').setNumberFormat('@');
  }
  return sh;
}

// Write [id, value] pairs into a sheet, one row per task ID
function upsert_(sh, pairs) {
  var values = sh.getDataRange().getValues();
  var rowOf = {};
  for (var i = 1; i < values.length; i++) rowOf[String(values[i][0])] = i + 1;
  var now = new Date();
  pairs.forEach(function (p) {
    if (rowOf[p[0]]) {
      sh.getRange(rowOf[p[0]], 2, 1, 2).setValues([[p[1], now]]);
    } else {
      sh.appendRow([p[0], p[1], now]);
      rowOf[p[0]] = sh.getLastRow();
    }
  });
}

function json_(data) {
  return ContentService.createTextOutput(JSON.stringify(data)).setMimeType(ContentService.MimeType.JSON);
}

// GET: every task's state, as { "d14-1": true, ..., "_who": { "d14-1": "you,matt" } }
function doGet() {
  var out = {};
  sheet_().getDataRange().getValues().slice(1).forEach(function (row) {
    if (row[0]) out[String(row[0])] = row[1] === true;
  });
  var who = {}, any = false;
  whoSheet_().getDataRange().getValues().slice(1).forEach(function (row) {
    if (row[0]) { who[String(row[0])] = String(row[1]); any = true; }
  });
  if (any) out._who = who;
  return json_(out);
}

// POST: [{ "id": "d14-1", "done": true }, { "id": "d14-2", "who": "you,matt" }, ...]
// (or one object). "who": "" means no owner tag.
function doPost(e) {
  var body;
  try { body = JSON.parse(e.postData.contents); } catch (err) { return json_({ ok: false, error: 'bad json' }); }
  var items = (Array.isArray(body) ? body : [body]).filter(function (it) {
    return it && /^[a-z0-9-]{1,24}$/.test(it.id);
  }).slice(0, 300);
  var ticks = items.filter(function (it) { return typeof it.done === 'boolean'; });
  var owners = items.filter(function (it) { return typeof it.who === 'string' && WHO_RE.test(it.who); });
  if (!ticks.length && !owners.length) return json_({ ok: false, error: 'nothing to save' });

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    if (ticks.length) upsert_(sheet_(), ticks.map(function (it) { return [it.id, it.done]; }));
    if (owners.length) upsert_(whoSheet_(), owners.map(function (it) { return [it.id, it.who]; }));
  } finally {
    lock.releaseLock();
  }
  return json_({ ok: true, saved: ticks.length + owners.length });
}
