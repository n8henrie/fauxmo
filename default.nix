{
  lib,
  buildPythonPackage,
  setuptools-scm,
}:
buildPythonPackage {
  pname = "fauxmo";
  version = builtins.head (
    lib.findFirst (v: v != null) null (
      builtins.map (builtins.match "^__version__ = \"(.*)\"") (
        lib.splitString "\n" (builtins.readFile ./src/fauxmo/__init__.py)
      )
    )
  );
  src = lib.cleanSource ./.;
  format = "pyproject";
  propagatedBuildInputs = [ setuptools-scm ];
}
