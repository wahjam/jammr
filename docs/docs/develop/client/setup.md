The classic Wahjam client is available at
[https://github.com/wahjam/wahjam](https://github.com/wahjam/wahjam). This is
the stable client that has been in use.

Prerequisites
-------------

First, a general overview of the dependencies. Note that you may wish to review
how to build releases on your platform of choice, since there might be
platform-specific ways of easily installing these dependencies.

1. Install a C++ compiler. GCC or clang are recommended.
1. Install the [Qt5 cross-platform application and UI toolkit](https://doc.qt.io/qt-5/index.html).
1. Install the [Ogg and Vorbis audio codec libraries](https://xiph.org/).
1. Install the [PortAudio](https://github.com/PortAudio/portaudio) cross-platform audio library.
1. Install the [PortMIDI](https://github.com/PortMidi/PortMidi) cross-platform MIDI library.
1. Install the [QtKeychain](https://github.com/PortMidi/PortMidi) cross-platform keyring library.

### Windows

The client has historically been cross-compiled under [MXE](https://mxe.cc/) on
Linux. It should also compile natively on Windows, but these instructions are
for MXE.

```
$ git clone https://github.com/mxe/mxe.git
```

Historically the build environment was set up manually, so these steps will
point you in the right direction but some changes may be necessary for your
environment. Note that Wahjam2 has a more reproducible build environment called
[wahjam2-windows-build](https://github.com/wahjam/wahjam2-windows-build) that
uses containers. You may wish to use that as a starting point instead of
manually setting up a Wahjam build environment that cannot be reproduced by
others.

Set up MXE's settings.mk file as follows:

- Enable x86-64 dynamically linked builds with `MXE_TARGETS :=
  x86_64-w64-mingw32.shared`. Although statically linking is technically
  possible, be aware that it has potential effects on the software licenses of
  Qt and anything LGPL.
- Enable job parallelism to decrease build times: `JOBS := 8`

The following MXE packages must be installed:

```
mxe$ make gcc ogg vorbis portaudio portmidi qt5 qtkeychain
```

### Linux

Install git, make, gcc, and the following development packages for your distro:
libogg, libvorbis, PortAudio, PortMIDI, Qt5, and QtKeychain.

### Mac

The client has historically been compiled with the Xcode Command Line Tools:

```
$ xcode-select --install
```

Do not build against Homebrew because its libraries are not intended to be
redistributable. Instead, build the dependencies from source such that they can
be distributed as an application. Use
[wahjam2-mac-build](https://github.com/wahjam/wahjam2-mac-build) as a starting
point but note that it is intended for Wahjam2, not Wahjam. The main difference
is that Wahjam uses Qt5 while Wahjam2 uses Qt6.

Building
--------

Prepare for compilation by running `qmake CONFIG+=jammr CONFIG+=qtclient` (this
may also be called `qmake-qt5` on your machine).

Then compile code by running `make`. The executable is called `jammr` or
`jammr.exe`, depending on your platform.

Wahjam2 alpha client
--------------------
There is an alpha-quality client at
[https://github.com/wahjam/wahjam2](https://github.com/wahjam/wahjam2) with a
modern user interface that was written from scratch.
