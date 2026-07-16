"use strict";
var fs = require("fs"), path = require("path"), vm = require("vm");
var html = fs.readFileSync(path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-14_utharsika_new_v002.html"), "utf-8");
var scripts = [];
var re = /<script>([\s\S]*?)<\/script>/g;
var m;
while ((m = re.exec(html)) !== null) scripts.push(m[1]);
var sandbox = { module: { exports: {} }, self: {} };
vm.createContext(sandbox);
vm.runInContext(scripts[0], sandbox);
var Engine = sandbox.module.exports;
var bounds = { selectableStart: "2026-01-01", selectableEnd: "2026-07-13", historyStart: "2025-01-01", historyEnd: "2026-07-13", latestCompleted: "2026-07-13" };
console.log("MONTH Jan2026:", JSON.stringify(Engine.resolvePeriod("MONTH", {month:"2026-01"}, bounds)));
console.log("DAILY Jan-1-2025 (should fail - before selectable range):");
try { console.log(JSON.stringify(Engine.resolvePeriod("DAILY", {date:"2025-01-01"}, bounds))); } catch(e) { console.log("Error (expected, outside selectable range):", e.message); }
