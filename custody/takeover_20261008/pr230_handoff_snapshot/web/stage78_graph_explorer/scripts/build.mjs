import esbuild from 'esbuild';
import fs from 'node:fs/promises';
import path from 'node:path';

const outdir = 'dist';
await fs.rm(outdir, { recursive: true, force: true });
await fs.mkdir(outdir, { recursive: true });
const result = await esbuild.build({
  entryPoints: ['src/app.js'],
  bundle: true,
  minify: true,
  format: 'iife',
  globalName: 'Stage78GraphExplorer',
  outfile: path.join(outdir, 'stage78_graph_explorer.iife.js'),
  metafile: true,
  legalComments: 'none',
  logLevel: 'silent',
});
await fs.writeFile(path.join(outdir, 'metafile.json'), JSON.stringify(result.metafile, null, 2) + '\n');
