import { Database } from "bun:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";

/**
 * Schema migrations, applied in order. The index + 1 is the schema version stored in
 * `PRAGMA user_version`. Only ever append — never edit a migration that has shipped.
 */
const MIGRATIONS: string[] = [
  // 1: generic todo list
  `CREATE TABLE todos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    text       TEXT    NOT NULL,
    done       INTEGER NOT NULL DEFAULT 0,
    position   INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
  );`,
];

export const DEFAULT_DB_PATH = process.env.DB_PATH ?? "data/note-it.sqlite";

export function openDb(path: string = DEFAULT_DB_PATH): Database {
  if (path !== ":memory:") mkdirSync(dirname(path), { recursive: true });

  const db = new Database(path, { create: true, strict: true });
  db.exec("PRAGMA journal_mode = WAL;");
  db.exec("PRAGMA foreign_keys = ON;");
  migrate(db);
  return db;
}

export function migrate(db: Database): void {
  const { user_version: current } = db.query("PRAGMA user_version").get() as { user_version: number };
  if (current > MIGRATIONS.length) {
    throw new Error(`Database schema v${current} is newer than this app (v${MIGRATIONS.length})`);
  }

  for (let version = current + 1; version <= MIGRATIONS.length; version++) {
    db.transaction(() => {
      db.exec(MIGRATIONS[version - 1]!);
      db.exec(`PRAGMA user_version = ${version};`);
    })();
  }
}
