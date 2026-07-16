import esbuild from 'esbuild';
import fs from 'node:fs/promises';
import path from 'node:path';

const outdir = 'dist';
await fs.mkdir(outdir, { recursive: true });
const result = await esbuild.build({
  entryPoints: ['src/stage79/app.js'],
  bundle: true,
  minify: true,
  format: 'iife',
  globalName: 'Stage79GraphControlExplorer',
  outfile: path.join(outdir, 'stage79_graph_control_explorer.iife.js'),
  metafile: true,
  legalComments: 'none',
  logLevel: 'silent',
});
await fs.writeFile(path.join(outdir, 'metafile-stage79.json'), JSON.stringify(result.metafile, null, 2) + '\n');
