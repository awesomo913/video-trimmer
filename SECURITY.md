# Security Policy

## Supported versions

Only the latest released version of Video Trimmer is supported with security fixes.

## Reporting a vulnerability

Please report security issues using **[GitHub's private vulnerability reporting](https://github.com/awesomo913/video-trimmer/security/advisories/new)** (Security tab, "Report a vulnerability") rather than a public issue, so it can be triaged before details are public.

If private reporting isn't available for you, open a regular GitHub issue with as much detail as you're comfortable sharing publicly, and note that it's a security concern in the title.

Please include:

- A description of the issue and its potential impact
- Steps to reproduce, if possible
- The Video Trimmer version and Windows version you're running

## Scope notes

- Video Trimmer runs entirely on your computer. It makes no network connections, has no account, and sends no telemetry. Your videos are never uploaded.
- It starts two helper programs: the bundled `ffmpeg` (to export) and, only if you have it installed, `ffplay` (to play preview sound).
- The release `.exe` is unsigned. SmartScreen or antivirus false-positive reports are useful context but are not vulnerabilities; see the README FAQ (verify the checksum, or build from source).
