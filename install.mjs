#!/usr/bin/env node
/**
 * Активация dsh-moduleapi в профиле DeepSeek Harness.
 *
 * Делает две вещи:
 *  1. добавляет зависимость dsh-moduleapi в ~/.dsh/profiles/desktop/package.json
 *     (git-зависимость, устанавливается через `pnpm add github:Skeltx/dsh-moduleapi`);
 *  2. добавляет "dsh-moduleapi" в dsh.profile.bundles, чтобы патч-слой
 *     применился при каждом запуске.
 *
 * Запуск (после `pnpm add github:Skeltx/dsh-moduleapi`):
 *   node install.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const PROFILE = join(homedir(), ".dsh", "profiles", "desktop");
const MANIFEST = join(PROFILE, "package.json");
const SPEC = "github:Skeltx/dsh-moduleapi";

const manifest = JSON.parse(readFileSync(MANIFEST, "utf8"));
manifest.dependencies ??= {};
manifest.dependencies["dsh-moduleapi"] = SPEC;
if (typeof manifest.dependencies !== "object") throw new Error("profile package.json: unexpected dependencies field");
manifest.dsh = manifest.dsh ?? {};
manifest.dsh.profile = manifest.dsh.profile ?? {};
const bundles = manifest.dsh.profile.bundles;
if (!Array.isArray(bundles)) throw new Error("profile package.json: missing dsh.profile.bundles");
if (!bundles.includes("dsh-moduleapi")) bundles.push("dsh-moduleapi");
writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + "\n");
console.log("OK: dsh-moduleapi активирован. Перезапустите DeepSeek Harness.");
