{
  pkgs,
  config,
  lib,
  ...
}:
let
  service_name = "fauxmo";
  cfg = config.services.${service_name};
  settingsFormat = pkgs.formats.json { };
in
{
  options.services.${service_name} = with lib; {
    enable = mkEnableOption service_name;
    user = mkOption {
      type = types.str;
      description = "User that fauxmo will run as";
      default = "fauxmo";
    };
    ip_address = mkOption {
      type = types.str;
      description = "IP addresses that will be advertised to the Alexa";
      default = "auto";
    };
    plugins = mkOption {
      inherit (settingsFormat) type;
      description = ''Plugins and plugin settings for fauxmo. Example: <https://github.com/n8henrie/fauxmo/blob/master/config-sample.json>'';
      default = { };
    };
    secretsFile = mkOption {
      type = lib.types.path;
      description = ''
        JSON file containing secret keys that will be merged into the config. A dummy example:
        ```
        {
            "PLUGINS": {
                HomeAssistantPlugin: {
                    "ha_token": "abc123..."
                }
            }
        }
        ```
      '';
    };
    verbosity = mkOption {
      type = types.enum [
        0
        1
        2
        3
      ];
      default = 0;
    };

    openFirewall = mkOption {
      type = types.bool;
      default = false;
      description = lib.mdDoc "Whether to open TCP ports in the firewall";
    };
  };

  config =
    let
      inherit (lib) mkIf;
    in
    mkIf cfg.enable {
      networking.firewall = mkIf cfg.openFirewall {
        allowedUDPPorts = [
          1900
        ];
        allowedTCPPorts = builtins.concatMap (plugin: builtins.map (d: d.port) plugin.DEVICES) (
          builtins.attrValues cfg.plugins
        );
      };
      systemd.services.${service_name} =
        let
          after = [ "network-online.target" ];
        in
        {
          description = service_name;
          inherit after;
          requires = after;
          script =
            let
              pythonWithFauxmo = lib.getExe (
                pkgs.python3.withPackages (
                  ps: with ps; [
                    fauxmo
                    uvloop
                  ]
                )
              );
              verbosity =
                if cfg.verbosity == 0 then
                  ""
                else
                  "-" + lib.concatStrings (builtins.genList (_: "v") cfg.verbosity);
            in
            "${pythonWithFauxmo} -m fauxmo.cli ${verbosity} -c /run/fauxmo/config.json";
          serviceConfig = {
            ExecStartPre =
              let
                configFile = settingsFormat.generate "config.json" {
                  FAUXMO.ip_address = cfg.ip_address;
                  PLUGINS = cfg.plugins;
                };
              in
              ''
                /bin/sh -c "${pkgs.jq}/bin/jq -s '.[0] * .[1]' ${configFile} %d/secrets.json > /run/fauxmo/config.json"
              '';
            LoadCredential = "secrets.json:${cfg.secretsFile}";
            User = "fauxmo";
            RuntimeDirectory = "fauxmo";
            DynamicUser = true;
            Restart = "on-failure";
            RestartSec = 30;
          };
          wantedBy = [ "multi-user.target" ];
        };
    };
}
