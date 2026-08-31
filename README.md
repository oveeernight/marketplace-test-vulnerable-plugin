# Android Reverse Engineering

Plugin for decompiling Android applications and extracting their HTTP API surface. It supports APK, XAPK, JAR, and AAR files, traces call flows from the UI down to the network layer, and documents Retrofit, OkHttp, Volley, Ktor, and Apollo endpoints.

## What it does

- Fingerprints an APK/XAPK before decompiling (framework, HTTP stack, obfuscation level, native libs).
- Decompiles with jadx and/or Fernflower/Vineflower.
- Recovers original Kotlin class names from R8-obfuscated binaries.
- Extracts HTTP endpoints, hardcoded URLs, auth headers, and request-signing schemes.
- Traces call flows and analyzes the manifest, packages, and architecture.

## Requirements

- Java JDK 17+
- jadx (CLI)

Optional (recommended): Vineflower or Fernflower, and dex2jar.

## Structure

```
plugin.json
skills/android-reverse-engineering/
├── SKILL.md                 # core workflow
├── references/              # setup guide and usage docs
└── scripts/                 # dependency check, decompile, fingerprint, API extraction
```

## License

Apache-2.0. This plugin is adapted from https://github.com/SimoneAvogadro/android-reverse-engineering-skill.

Provided strictly for lawful purposes (security research, authorized testing, interoperability, malware analysis, education). You are responsible for complying with applicable law.
