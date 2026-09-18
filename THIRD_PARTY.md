# Third-party components

This repository contains the SimpleAirPlay controller source only. The controller invokes a separate, unmodified UxPlay Windows application as a subprocess.

The optional setup script downloads:

- Project: https://github.com/leapbtw/uxplay-windows
- Release: https://github.com/leapbtw/uxplay-windows/releases/tag/2.0.0.1736
- Archive: `uxplay-windows.zip` (x64)
- SHA-256: `9d3a51c15fc9db857351195e7eb7bbb21700d9ae25d936a54bcf8536b62cca18`
- Release source: https://github.com/leapbtw/uxplay-windows/tree/2.0.0.1736
- Core upstream: https://github.com/FDH2/UxPlay

The archive includes UxPlay, GStreamer, FFmpeg, Qt and other dependencies. They retain their respective licenses. The setup script preserves the archive contents, including `LICENSE.rtf`. The controller's MIT license does not relicense any of these components.

If you redistribute a complete binary bundle, you are responsible for satisfying each component's license, including applicable source-code and notice obligations. A link to upstream alone should not be assumed to satisfy every redistribution obligation. This repository does not publish a combined binary release.

Python, Tkinter/Tcl/Tk, psutil and PyInstaller also retain their own licenses. Building with PyInstaller copies the Python runtime and required libraries into the build output.
