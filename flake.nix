{
  description = "Flake for github.com/n8henrie/fauxmo";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/release-23.11";

  outputs = {
    self,
    nixpkgs,
  }: let
    inherit (nixpkgs) lib;
    systems = ["aarch64-darwin" "x86_64-linux" "aarch64-linux"];
    systemGen = attrs:
      builtins.foldl' (acc: system:
        lib.recursiveUpdate acc (attrs {
          inherit system;
          pkgs = import nixpkgs {
            inherit system;
            overlays = [self.outputs.overlays.default];
          };
        })) {}
      systems;
  in
    {
      overlays.default = _: prev: {
        pythonPackagesExtensions =
          prev.pythonPackagesExtensions
          ++ [(py-final: _: {fauxmo = py-final.callPackage ./. {};})];
      };
    }
    // systemGen ({
      pkgs,
      system,
    }: {
      formatter.${system} = pkgs.alejandra;
      packages.${system} = {
        default = self.outputs.packages.${system}.pythonWithFauxmo;
        pythonWithFauxmo = pkgs.python3.withPackages (ps:
          with ps; [
            self.outputs.packages.${system}.fauxmo
            uvloop
          ]);
        fauxmo = pkgs.callPackage ./. {};
      };

      nixosModules = {
        default = self.outputs.nixosModules.fauxmo;
        fauxmo = import ./module.nix;
      };

      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/python -m fauxmo.cli";
      };

      devShells.${system}.default = pkgs.mkShell {
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
          python38
          python39
          python310
          python311
          python311.pkgs.venvShellHook
        ];
      };

      checks.${system}.integration = import ./integration_test.nix {inherit pkgs;};
    });
}
