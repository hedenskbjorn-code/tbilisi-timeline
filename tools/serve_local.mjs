// A local copy of the site for testing before the publication: the folder site/ is served with gzip, as GitHub Pages does.
// Usage: node tools/serve_local.mjs [port]      (default 8090)   then open http://localhost:8090/
// Nothing is cached by the browser (cache-control: no-store), so a change of a file shows at once. Stop it with Ctrl+C.
import { startServer } from "../tests/e2e/helpers.mjs";

const port = Number(process.argv[2] || 8090);
const { srv } = await startServer(port, "127.0.0.1");          // this computer only: the local network cannot reach it
console.log(`The site is served at http://localhost:${port}/  (Ctrl+C stops it)`);
process.on("SIGINT", () => { srv.close(); process.exit(0); });
