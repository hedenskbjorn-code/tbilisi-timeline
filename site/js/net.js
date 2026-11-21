// Loading of the data files of the site.
//
// The data files are requested all at once as soon as the page starts (prefetchJSON) and not one after another after the base map has loaded;
// getJSON takes the request that is already on its way and, if that one failed, falls back to its own retries (a dropped connection must not leave
// a layer silently empty).
const prefetched = new Map();

export function prefetchJSON(urls) {
  for (const u of urls) {
    const p = fetch(u).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
    p.catch(() => {});                                                 // the failure is handled by getJSON, nothing is left unhandled
    prefetched.set(u, p);
  }
}

export async function getJSON(url, tries = 4) {
  const pre = prefetched.get(url);
  if (pre) { prefetched.delete(url); try { return await pre; } catch (e) { /* retry below */ } }
  for (let k = 0; ; k++) {
    try {
      const r = await fetch(url);
      if (!r.ok) throw new Error(r.status);
      return await r.json();
    } catch (e) {
      if (k >= tries - 1) throw e;
      await new Promise((res) => setTimeout(res, 400 * (k + 1)));
    }
  }
}
