{
  description = "Flake for github.com/n8henrie/fauxmo";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/release-23.11";

  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      systems = [
        "aarch64-darwin"
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-linux"
      ];
      eachSystem =
        with nixpkgs.lib;
        f: foldAttrs mergeAttrs { } (map (s: mapAttrs (_: v: { ${s} = v; }) (f s)) systems);
    in
    {
      overlays.default = _: prev: {
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (py-final: _: { fauxmo = py-final.callPackage ./. { }; })
        ];
      };
      nixosModules = {
        default = self.outputs.nixosModules.fauxmo;
        fauxmo = ./module.nix;
      };
    }
    // (eachSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        formatter = pkgs.nixfmt-rfc-style;
        packages = {
          default = self.outputs.packages.${system}.pythonWithFauxmo;
          pythonWithFauxmo = pkgs.python3.withPackages (
            ps: with ps; [
              self.outputs.packages.${system}.fauxmo
              uvloop
            ]
          );
          fauxmo = pkgs.callPackage ./. {
            inherit (pkgs.python3Packages)
              buildPythonPackage
              setuptools-scm
              ;
          };
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/python -m fauxmo.cli";
        };

        devShells.default = pkgs.mkShell {
          # Provides GCC for building brotli
          LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc ];

          venvDir = ".venv";
          postVenvCreation = ''
            unset SOURCE_DATE_EPOCH
            pip install -e .[dev,test]
          '';
          postShellHook = ''
            export SSL_CERT_FILE=$NIX_SSL_CERT_FILE;
          '';
          buildInputs = with pkgs; [
            python39
            python310
            python312.pkgs.venvShellHook
            python313
          ];
        };

        checks.integration =
          let
            fauxmoPkgs = import nixpkgs {
              inherit system;
              overlays = [ self.outputs.overlays.default ];
            };
          in
          fauxmoPkgs.callPackage ./integration_test.nix {
            inherit (fauxmoPkgs.python3Packages) fauxmo;
          };
      }
    ));
}
