"use strict";
var fs = require("fs"), path = require("path");
var html = fs.readFileSync(path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v002.html"), "utf-8");
function extractJson(id) {
  var re = new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>');
  var m = html.match(re);
  return JSON.parse(m[1]);
}
var dailySplit = extractJson("uawso-daily-aggregates-split");
var dates = dailySplit.map(function(r){ return r.calendar_date; }).sort();
console.log("Row count:", dailySplit.length);
console.log("Min date:", dates[0]);
console.log("Max date:", dates[dates.length-1]);
