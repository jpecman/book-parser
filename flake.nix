{
  description = "book-parser: Python development environment with PyMuPDF";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, pyproject-nix }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});

      # Dependencies are declared in pyproject.toml and resolved from nixpkgs.
      project = pyproject-nix.lib.project.loadPyproject { projectRoot = ./.; };
    in
    {
      devShells = forAllSystems (pkgs:
        let
          python = pkgs.python3;
          pythonEnv = python.withPackages (project.renderers.withPackages { inherit python; });
        in
        {
          default = pkgs.mkShell {
            packages = [ pythonEnv ];

            # Makes the book_parser package importable without an install step.
            shellHook = ''
              export PYTHONPATH="$PWD/src''${PYTHONPATH:+:$PYTHONPATH}"
            '';
          };
        });
    };
}
