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
          # Adds packages that nixpkgs does not have, built from their PyPI source.
          python = pkgs.python3.override {
            self = python;
            packageOverrides = pyFinal: pyPrev: {
              # Czech lemmatizer (C++ library with Python bindings).
              ufal-morphodita = pyFinal.buildPythonPackage rec {
                pname = "ufal.morphodita";
                version = "1.11.3.3";
                pyproject = true;
                src = pyFinal.fetchPypi {
                  pname = "ufal_morphodita";
                  inherit version;
                  hash = "sha256-JvWb5zQifS+AFxMelNxRmPzLTXHX8/rQsE87+hhY1Zs=";
                };
                build-system = [ pyFinal.setuptools ];
                pythonImportsCheck = [ "ufal.morphodita" ];
              };
            };
          };
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
