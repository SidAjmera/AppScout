// Export the curated catalog as SQL for Supabase's SQL editor or CLI seed.
import { readFile, writeFile } from 'node:fs/promises';
const apps = JSON.parse(await readFile(new URL('../src/data/catalog.json', import.meta.url), 'utf8'));
const quote = value => "'" + value.replaceAll("'", "''") + "'";
const delimiter = '$appscout_catalog$';
const rows = apps.map(app => {
  const json = JSON.stringify(app);
  if (json.includes(delimiter)) throw new Error('Catalog conflicts with SQL delimiter.');
  return '(' + [quote(app.id), quote(app.name), quote(app.category), delimiter + json + delimiter + '::jsonb'].join(',') + ')';
});
const sql = '-- Generated from src/data/catalog.json. No credentials or personal data.\n' +
  'begin;\ninsert into public.apps (id,name,category,data) values\n' + rows.join(',\n') +
  '\non conflict (id) do update set name=excluded.name,category=excluded.category,data=excluded.data,updated_at=now();\ncommit;\n';
await writeFile(new URL('../supabase/seed.sql', import.meta.url), sql);
console.log('Exported SQL for ' + apps.length + ' apps to supabase/seed.sql.');
