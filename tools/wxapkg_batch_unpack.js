#!/usr/bin/env node
"use strict";

const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

function printUsage() {
  console.log(`
Usage:
  node tools/wxapkg_batch_unpack.js --input <wxid_dir> [--output <dir>] [--wxid <wxid>] [--clean] [--recursive] [--report <json>]

Examples:
  node tools/wxapkg_batch_unpack.js --input input/wx6d78da7ea5b43968 --clean
  node tools/wxapkg_batch_unpack.js --input input/wx6d78da7ea5b43968 --output input/wx6d78da7ea5b43968/13_unpack --report logs/wx6d78/unpack.json

Notes:
  - If --wxid is omitted, this script uses basename(--input) as wxid.
  - Output default: <input>/unpack
  - Supports encrypted and plain .wxapkg.
`);
}

function parseArgs(argv) {
  const opts = {
    clean: false,
    recursive: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") {
      opts.help = true;
      continue;
    }
    if (a === "--clean") {
      opts.clean = true;
      continue;
    }
    if (a === "--recursive") {
      opts.recursive = true;
      continue;
    }
    if (a.startsWith("--input=")) {
      opts.input = a.slice("--input=".length);
      continue;
    }
    if (a.startsWith("--output=")) {
      opts.output = a.slice("--output=".length);
      continue;
    }
    if (a.startsWith("--wxid=")) {
      opts.wxid = a.slice("--wxid=".length);
      continue;
    }
    if (a.startsWith("--report=")) {
      opts.report = a.slice("--report=".length);
      continue;
    }
    if (a === "--input" || a === "--output" || a === "--wxid" || a === "--report") {
      if (i + 1 >= argv.length) {
        throw new Error(`Missing value for ${a}`);
      }
      const v = argv[++i];
      if (a === "--input") opts.input = v;
      if (a === "--output") opts.output = v;
      if (a === "--wxid") opts.wxid = v;
      if (a === "--report") opts.report = v;
      continue;
    }
    throw new Error(`Unknown argument: ${a}`);
  }
  if (!opts.help && !opts.input) {
    throw new Error("--input is required");
  }
  return opts;
}

function listWxapkgFiles(inputDir, recursive) {
  const out = [];
  if (!recursive) {
    for (const name of fs.readdirSync(inputDir)) {
      const abs = path.join(inputDir, name);
      if (!fs.statSync(abs).isFile()) continue;
      if (name.toLowerCase().endsWith(".wxapkg")) out.push(abs);
    }
    return out.sort();
  }
  const stack = [inputDir];
  while (stack.length) {
    const cur = stack.pop();
    const entries = fs.readdirSync(cur, { withFileTypes: true });
    for (const e of entries) {
      const abs = path.join(cur, e.name);
      if (e.isDirectory()) {
        stack.push(abs);
      } else if (e.isFile() && e.name.toLowerCase().endsWith(".wxapkg")) {
        out.push(abs);
      }
    }
  }
  return out.sort();
}

function decryptIfNeeded(buf, wxid) {
  const isPlain = buf.length >= 14 && buf.readUInt8(0) === 0xbe && buf.readUInt8(13) === 0xed;
  if (isPlain) return { buffer: buf, decrypted: false };

  if (buf.length < 1031) {
    throw new Error(`Encrypted package too small: ${buf.length}`);
  }
  if (!wxid || !wxid.trim()) {
    throw new Error("wxid is required for encrypted package");
  }

  const iv = Buffer.from("the iv: 16 bytes");
  const salt = Buffer.from("saltiest");
  const key = crypto.pbkdf2Sync(wxid, salt, 1000, 32, "sha1");
  const decipher = crypto.createDecipheriv("aes-256-cbc", key, iv);
  const first1024 = Buffer.concat([decipher.update(buf.subarray(6, 1030)), decipher.final()]);

  const xorKey = wxid.length >= 2 ? wxid.charCodeAt(wxid.length - 2) : 0x66;
  const tail = Buffer.alloc(buf.length - 1030);
  for (let i = 0; i < tail.length; i++) {
    tail[i] = buf[1030 + i] ^ xorKey;
  }

  const plain = Buffer.concat([first1024, tail]);
  if (!(plain.length >= 14 && plain.readUInt8(0) === 0xbe && plain.readUInt8(13) === 0xed)) {
    throw new Error("Decryption failed: magic number mismatch");
  }
  return { buffer: plain, decrypted: true };
}

function parseHeader(buf) {
  if (buf.length < 14) throw new Error("Invalid package: header too short");
  const firstMark = buf.readUInt8(0);
  const infoListLength = buf.readUInt32BE(5);
  const dataLength = buf.readUInt32BE(9);
  const lastMark = buf.readUInt8(13);
  if (firstMark !== 0xbe || lastMark !== 0xed) {
    throw new Error(`Invalid package magic: first=0x${firstMark.toString(16)} last=0x${lastMark.toString(16)}`);
  }
  if (14 + infoListLength > buf.length) {
    throw new Error(`Invalid package: info list overflow (${infoListLength})`);
  }
  if (14 + infoListLength + dataLength > buf.length + 16) {
    // Some packages have non-strict dataLength, keep as warning only.
  }
  return { infoListLength, dataLength };
}

function parseFileList(infoBuf) {
  if (infoBuf.length < 4) throw new Error("Invalid package: file list too short");
  const fileCount = infoBuf.readUInt32BE(0);
  const files = [];
  let off = 4;
  for (let i = 0; i < fileCount; i++) {
    if (off + 4 > infoBuf.length) throw new Error("Invalid package: name length overflow");
    const nameLen = infoBuf.readUInt32BE(off);
    off += 4;
    if (off + nameLen + 8 > infoBuf.length) throw new Error("Invalid package: file entry overflow");
    const name = infoBuf.toString("utf8", off, off + nameLen);
    off += nameLen;
    const dataOff = infoBuf.readUInt32BE(off);
    off += 4;
    const size = infoBuf.readUInt32BE(off);
    off += 4;
    files.push({ name, off: dataOff, size });
  }
  return files;
}

function normalizeRelPath(p) {
  let rel = p.replace(/\\/g, "/");
  while (rel.startsWith("/")) rel = rel.slice(1);
  rel = rel.replace(/^(\.\/)+/, "");
  return rel;
}

function ensureSafePath(baseDir, targetAbs) {
  const base = path.resolve(baseDir);
  const target = path.resolve(targetAbs);
  const prefix = base.endsWith(path.sep) ? base : base + path.sep;
  if (target !== base && !target.startsWith(prefix)) {
    throw new Error(`Unsafe output path: ${target}`);
  }
}

function unpackOne(wxapkgFile, outputRoot, wxid) {
  const raw = fs.readFileSync(wxapkgFile);
  const dec = decryptIfNeeded(raw, wxid);
  const pkg = dec.buffer;
  const hdr = parseHeader(pkg);
  const fileList = parseFileList(pkg.subarray(14, 14 + hdr.infoListLength));

  const pkgName = path.basename(wxapkgFile).replace(/\.wxapkg$/i, "");
  const pkgOutDir = path.join(outputRoot, pkgName);
  fs.mkdirSync(pkgOutDir, { recursive: true });

  for (const f of fileList) {
    const rel = normalizeRelPath(f.name);
    const dst = path.join(pkgOutDir, rel);
    ensureSafePath(pkgOutDir, dst);
    const parent = path.dirname(dst);
    fs.mkdirSync(parent, { recursive: true });
    if (f.off + f.size > pkg.length) {
      throw new Error(`Invalid file range: ${f.name} off=${f.off} size=${f.size}`);
    }
    fs.writeFileSync(dst, pkg.subarray(f.off, f.off + f.size));
  }

  return {
    package: path.basename(wxapkgFile),
    out_dir: pkgOutDir,
    file_count: fileList.length,
    decrypted: dec.decrypted,
  };
}

function main() {
  let opts;
  try {
    opts = parseArgs(process.argv.slice(2));
  } catch (e) {
    console.error(`[wxapkg] ${e.message}`);
    printUsage();
    process.exit(2);
    return;
  }

  if (opts.help) {
    printUsage();
    return;
  }

  const inputDir = path.resolve(opts.input);
  if (!fs.existsSync(inputDir) || !fs.statSync(inputDir).isDirectory()) {
    console.error(`[wxapkg] input directory not found: ${inputDir}`);
    process.exit(2);
    return;
  }

  const wxid = opts.wxid || path.basename(inputDir);
  const outputDir = path.resolve(opts.output || path.join(inputDir, "unpack"));

  if (opts.clean && fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true, force: true });
  }
  fs.mkdirSync(outputDir, { recursive: true });

  const files = listWxapkgFiles(inputDir, opts.recursive);
  if (!files.length) {
    console.error(`[wxapkg] no .wxapkg found in: ${inputDir}`);
    process.exit(3);
    return;
  }

  const report = {
    input_dir: inputDir,
    output_dir: outputDir,
    wxid,
    total_packages: files.length,
    packages: [],
    failed: [],
  };

  console.log(`[wxapkg] input=${inputDir}`);
  console.log(`[wxapkg] output=${outputDir}`);
  console.log(`[wxapkg] wxid=${wxid}`);
  console.log(`[wxapkg] packages=${files.length}`);

  for (const file of files) {
    const rel = path.relative(inputDir, file);
    try {
      const r = unpackOne(file, outputDir, wxid);
      report.packages.push(r);
      console.log(`[wxapkg] ok ${rel} -> ${path.relative(process.cwd(), r.out_dir)} (${r.file_count} files, decrypted=${r.decrypted})`);
    } catch (e) {
      report.failed.push({ package: rel, error: String(e.message || e) });
      console.error(`[wxapkg] fail ${rel}: ${e.message}`);
    }
  }

  report.ok_count = report.packages.length;
  report.fail_count = report.failed.length;
  if (opts.report) {
    const reportPath = path.resolve(opts.report);
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`[wxapkg] report=${reportPath}`);
  }

  if (report.fail_count > 0) {
    console.error(`[wxapkg] done with failures: ok=${report.ok_count}, fail=${report.fail_count}`);
    process.exit(1);
    return;
  }
  console.log(`[wxapkg] done: ok=${report.ok_count}, fail=0`);
}

main();
