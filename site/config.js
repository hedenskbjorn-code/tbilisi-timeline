// Site settings that are not data. Nothing here is secret: this file is public.
window.TT_CONFIG = {
  // GitHub repository used for bug reports (issues) and shown in the "About" text
  repo: "hedenskbjorn-code/tbilisi-timeline",
  // Optional: URL of a form-collecting service (e.g. a Formspree endpoint) that accepts a JSON POST.
  // Leave empty to use GitHub issues only.
  feedbackEndpoint: "",
  // The form "send a photo" (worker/submit.js; the owner checks every photo before it is shown). The site key of Turnstile is public by design.
  // photoOpen: true opens the form for every visitor; false shows it only in a browser where the link with ?club=1 was opened (?club=0 hides it again).
  photoOpen: true,
  photoEndpoint: "https://tbilisi-photos.hedenskbjorn.workers.dev/submit",
  turnstileSitekey: "0x4AAAAAAGIkp2dhOAPSyLv-"
};
