{
  pkgs,
  config,
  lib,
  ...
}: let
  service_name = "fauxmo";
  cfg = config.services.${service_name};
in
  with lib; {
    options.services.${service_name} = {
      enable = mkEnableOption service_name;
      user = mkOption {
        type = types.str;
        description = "User that fauxmo will run as";
        default = "fauxmo";
      };
      configFile = mkOption {
        type = types.str;
        description = "Path to config.json";
      };
      verbosity = mkOption {
        type = types.enum [0 1 2 3];
        default = 0;
      };

      openFirewall = mkOption {
        type = types.bool;
        default = false;
        description = lib.mdDoc "Whether to open TCP ports in the firewall";
      };
      tcpPortRange = mkOption {
        description = "TCP range to open for fauxmo";
        type = with types;
          submodule {
            options = {
              from = mkOption {
                type = int;
              };
              to = mkOption {
                type = int;
              };
            };
          };
      };
    };

    config = mkIf cfg.enable {
      networking.firewall = mkIf cfg.openFirewall {
        allowedUDPPorts = [
          1900
        ];
        allowedTCPPortRanges = [
          {
            inherit (cfg.tcpPortRange) to from;
          }
        ];
      };
      systemd.services.${service_name} = let
        pythonWithFauxmo =
          pkgs.python3.withPackages
          (ps:
            with ps; [
              fauxmo
              uvloop
            ]);
        after = ["network-online.target"];
      in {
        description = service_name;
        inherit after;
        requires = after;
        script = let
          verbosity =
            if cfg.verbosity == 0
            then ""
            else "-" + lib.concatStrings (builtins.genList (_: "v") cfg.verbosity);
        in ''${pythonWithFauxmo}/bin/python -m fauxmo.cli ${verbosity} -c "${cfg.configFile}"'';
        serviceConfig = {
          User = cfg.user;
          Restart = "on-failure";
          RestartSec = 30;
        };
        wantedBy = ["multi-user.target"];
      };
    };
  }
