// Renderizador de las vistas SVG generadas desde el mismo modelo que el archivo draw.io.
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('sharp');
const root = path.resolve(__dirname, '..', 'docs', 'modelo_20_cu', 'vistas');
(async () => {
  for (const name of (await fs.readdir(root)).filter(x => x.endsWith('.svg')).sort()) {
    await sharp(path.join(root, name), { density: 140 }).resize({width: 2600}).png().toFile(path.join(root, name.replace(/\.svg$/, '.png')));
    process.stdout.write('Vista renderizada: '+name+'\n');
  }
})();
