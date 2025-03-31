{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.ffmpeg-full
    pkgs.xsimd
    pkgs.pkg-config
    pkgs.libxcrypt
    pkgs.portaudio
    pkgs.postgresql
  ];
}
