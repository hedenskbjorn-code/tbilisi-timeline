// Site settings that are not data. Nothing here is secret: this file is public.
window.TT_CONFIG = {
  // GitHub repository used for bug reports (issues) and shown in the "About" text
  repo: "hedenskbjorn-code/tbilisi-timeline",
  // The form "Report a problem" (worker/submit.js, POST /feedback): the message goes to the private queue of the owner (no GitHub account is needed);
  // GitHub issues are the reserve when the service cannot be reached. Leave empty to use GitHub issues only.
  feedbackEndpoint: "https://tbilisi-photos.hedenskbjorn.workers.dev/feedback",
  // The form "send a photo" (worker/submit.js; the owner checks every photo before it is shown). The site key of Turnstile is public by design.
  // photoOpen: true opens the form for every visitor; false shows it only in a browser where the link with ?club=1 was opened (?club=0 hides it again).
  photoOpen: true,
  photoEndpoint: "https://tbilisi-photos.hedenskbjorn.workers.dev/submit",
  turnstileSitekey: "0x4AAAAAAGIkp2dhOAPSyLv-"
};
