{
  description = "Flake for github.com/n8henrie/fauxmo";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/release-23.11";

  outputs = {
    self,
    nixpkgs,
  }: let
    inherit (nixpkgs) lib;
    pname = "fauxmo";
    systems = ["aarch64-darwin" "x86_64-linux" "aarch64-linux"];
    systemGen = attrs:
      builtins.foldl' (acc: system:
        lib.recursiveUpdate acc (attrs {
          inherit system;
          pkgs = import nixpkgs {inherit system;};
        })) {}
      systems;
  in
    systemGen ({
      pkgs,
      system,
    }: {
      formatter.${system} = pkgs.alejandra;
      packages.${system} = {
        default = self.packages.${system}.${pname};
        ${pname} = pkgs.python311.withPackages (ps:
          with ps; [
            uvloop
            (buildPythonPackage {
              inherit pname;
              version =
                builtins.head
                (lib.findFirst (v: v != null)
                  null (builtins.map
                    (builtins.match "^__version__ = \"(.*)\"")
                    (lib.splitString "\n" (builtins.readFile ./src/fauxmo/__init__.py))));
              src = ./.;
              format = "pyproject";
              propagatedBuildInputs = [setuptools];
            })
          ]);
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.${pname}}/bin/python -m ${pname}.cli";
      };

      devShells.${system}.default = let
        py = pkgs.python311;
      in
        pkgs.mkShell {
          # Provides GCC for building brotli
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc];

          venvDir = ".venv";
          postVenvCreation = ''
            unset SOURCE_DATE_EPOCH
            pip install -e .[dev,test]
          '';
          postShellHook = ''
            export SSL_CERT_FILE=$NIX_SSL_CERT_FILE;
          '';
          buildInputs = with pkgs; [
            py
            py.pkgs.venvShellHook
            python38
            python39
            python310
          ];
        };
    });
}
