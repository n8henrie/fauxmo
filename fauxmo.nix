{
  lib,
  python3Packages,
}: let
  inherit (python3Packages) buildPythonPackage setuptools-scm;
in
  buildPythonPackage {
    pname = "fauxmo";
    version =
      builtins.head
      (lib.findFirst (v: v != null) null
        (builtins.map
          (builtins.match "^__version__ = \"(.*)\"")
          (lib.splitString "\n" (builtins.readFile ./src/fauxmo/__init__.py))));
    src = lib.cleanSource ./.;
    format = "pyproject";
    propagatedBuildInputs = [setuptools-scm];
  }
