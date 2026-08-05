import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

const runtimeExtensions = new Set(['.js', '.jsx', '.ts', '.tsx']);
const localApiHost = `http://${['localhost', '8000'].join(':')}`;

function listRuntimeFiles(directory: string): string[] {
  const files: string[] = [];

  for (const entry of readdirSync(directory)) {
    const path = join(directory, entry);
    const stat = statSync(path);

    if (stat.isDirectory()) {
      files.push(...listRuntimeFiles(path));
      continue;
    }

    if (entry.includes('.test.') || entry.includes('.spec.')) {
      continue;
    }

    const extension = entry.slice(entry.lastIndexOf('.'));
    if (runtimeExtensions.has(extension)) {
      files.push(path);
    }
  }

  return files;
}

describe('runtime API hosts', () => {
  it('uses the local backend API host without malformed URL joins', () => {
    const sourceRoot = join(process.cwd(), 'src');
    const runtimeSources = listRuntimeFiles(sourceRoot).map((path) => ({
      path,
      source: readFileSync(path, 'utf8'),
    }));
    const malformedUrls = runtimeSources.filter(({ source }) =>
      /http:\s*\/\/\s*\/api/.test(source) || source.includes(`${localApiHost}http://`),
    );
    const localApiUrls = runtimeSources.filter(({ source }) => source.includes(localApiHost));

    expect(
      malformedUrls.map(({ path }) => relative(process.cwd(), path).replace(/\\/g, '/')),
    ).toEqual([]);
    expect(
      localApiUrls.map(({ path }) => relative(process.cwd(), path).replace(/\\/g, '/')),
    ).not.toEqual([]);
  });
});
