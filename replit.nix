{pkgs}: {
  deps = [
    pkgs.nodePackages.prettier
    pkgs.tmux
    pkgs.mypy
  ];
}
