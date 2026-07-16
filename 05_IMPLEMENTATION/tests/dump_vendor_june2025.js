"use strict";
var fs = require("fs");
var path = require("path");

var HTML_PATH = path.join(__dirname, "..", "..", "09_OUTPUTS", "2026-07-10_utharsika_v001.html");
var html = fs.readFileSync(HTML_PATH, "utf-8");

function extractJson(id) {
  var re = new RegExp('<script type="application/json" id="' + id + '">([\\s\\S]*?)</script>');
  var m = html.match(re);
  return JSON.parse(m[1]);
}

var vp = extractJson("uawso-vendor-periods");
var june25 = vp.filter(function (v) { return !(v.end_date < "2025-06-01" || v.start_date > "2025-06-30"); });
june25.sort(function (a, b) { return a.asin < b.asin ? -1 : 1; });
console.log("HTML-embedded overlapping rows count:", june25.length);
console.log(JSON.stringify(june25, null, 2));
