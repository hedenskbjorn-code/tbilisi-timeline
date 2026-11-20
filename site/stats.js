// Cloudflare Web Analytics (anonymous counting of visits, no cookies) is loaded from here and not by a tag in the page, so that the author can switch it off
// in his own browser and his tests do not mix with the visits of the visitors: open the page once with ?nostats=1 (the choice is kept in localStorage);
// ?nostats=0 switches the counting on again. A script of the page itself is allowed by the Content-Security-Policy, an inline one is not.
(function () {
  try {
    const q = new URLSearchParams(location.search).get("nostats");
    if (q === "1") localStorage.setItem("noStats", "1");
    else if (q === "0") localStorage.removeItem("noStats");
    if (localStorage.getItem("noStats") === "1") return;
  } catch (e) { /* no localStorage: count as usual */ }
  const s = document.createElement("script");
  s.type = "module";
  s.src = "https://static.cloudflareinsights.com/beacon.min.js";
  s.setAttribute("data-cf-beacon", '{"token": "f4945adf4d994802bcb88c6ce54c4c32"}');
  document.body.appendChild(s);
})();
