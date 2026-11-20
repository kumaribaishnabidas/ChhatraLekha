# ChhatraLekha for Linux

This directory contains a Linux desktop shell for the existing ChhatraLekha web portal. It is an online desktop client, not a separate native implementation: the remote web app and API remain responsible for authentication, authorization, tenant isolation, and student data. The desktop package does not keep student records offline.

## Run from source

Requirements: Node.js 22 or later (through Node 26), npm, and a graphical Linux desktop session.

```bash
cd linux/desktop
npm ci
npm test
npm start
```

By default the app opens `https://chhatralekha.vercel.app/`. Developers can point it at the local Vite server with `CHHATRALEKHA_WEB_URL=http://localhost:5173 npm start`. The desktop shell permits only the official HTTPS portal or the local Vite development server as its in-app origin. Links to other HTTP(S) sites open in the system browser; other schemes are blocked.

## Build Linux installers

```bash
cd linux/desktop
npm ci
npm test
npm run dist:linux
```

The build emits Linux x64 AppImage and Debian `.deb` packages under `release/`. The AppImage is portable; the `.deb` installs a launcher and appears in the desktop application menu. Build artifacts are platform-specific and should be built on Linux.

## Security

The renderer has Node integration disabled, context isolation enabled, and sandboxing enabled. The app restricts top-level navigation and redirects to the configured portal origin, denies pop-up windows, and delegates ordinary external HTTP(S) links to the operating system browser. It does not embed API credentials. Use the web app's existing HTTPS login and server-side access controls.

The app uses an in-memory browser session. Login tokens and site storage are cleared when the desktop app exits, so users should sign in again when they reopen it.

Do not enter production credentials if the official portal is unavailable or displays a deployment error. Check the live deployment status before distributing packages. The desktop app is only useful while the configured web service is reachable.

## Tests

`npm test` exercises portal URL validation, allowed origins, credential rejection, and external-origin navigation denial. CI builds the two Linux package formats on Ubuntu and retains them as workflow artifacts. A successful package build verifies packaging only; it does not verify production website availability or application workflows.
