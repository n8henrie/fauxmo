{
  fauxmo,
  nixosTest,
  overlay,
}:
nixosTest {
  name = "fauxmo-integration";
  nodes.system1 = {
    imports = [
      ./module.nix
    ];
    nixpkgs.overlays = [ overlay ];

    environment.systemPackages = [ fauxmo ];

    services.fauxmo = {
      enable = true;
      configFile = "/dev/null";
    };
  };

  testScript = ''
    system1.wait_for_unit("fauxmo.service")

    # system1.wait_until_succeeds("pgrep -f 'agetty.*tty1'")
    # system1.sleep(2)
    # system1.send_key("alt-f2")
    # system1.wait_until_succeeds("[ $(fgconsole) = 2 ]")
    # system1.wait_for_unit("getty@tty2.service")
    # system1.wait_until_succeeds("pgrep -f 'agetty.*tty2'")
    # system1.wait_until_tty_matches("2", "login: ")

    # userDo = lambda input : f"sudo -u user1 -- bash -c 'set -eou pipefail; cd /tmp/secrets; {input}'"

    # before_hash = system1.succeed(userDo('sha256sum passwordfile-user1.age')).split()
    # print(system1.succeed(userDo('agenix -r -i /home/user1/.ssh/id_ed25519')))
    # after_hash = system1.succeed(userDo('sha256sum passwordfile-user1.age')).split()

    # # Ensure we actually have hashes
    # for h in [before_hash, after_hash]:
    #     assert len(h) == 2, "hash should be [hash, filename]"
    #     assert h[1] == "passwordfile-user1.age", "filename is incorrect"
    #     assert len(h[0].strip()) == 64, "hash length is incorrect"
    # assert before_hash[0] != after_hash[0], "hash did not change with rekeying"

    # # user1 can edit passwordfile-user1.age
    # system1.succeed(userDo("EDITOR=cat agenix -e passwordfile-user1.age"))

    # # user1 can edit even if bogus id_rsa present
    # system1.succeed(userDo("echo bogus > ~/.ssh/id_rsa"))
    # system1.fail(userDo("EDITOR=cat agenix -e passwordfile-user1.age"))
    # system1.succeed(userDo("EDITOR=cat agenix -e passwordfile-user1.age -i /home/user1/.ssh/id_ed25519"))
    # system1.succeed(userDo("rm ~/.ssh/id_rsa"))

    # # user1 can edit a secret by piping in contents
    # system1.succeed(userDo("echo 'secret1234' | agenix -e passwordfile-user1.age"))

    # # and get it back out via --decrypt
    # assert "secret1234" in system1.succeed(userDo("agenix -d passwordfile-user1.age"))

    # # finally, the plain text should not linger around anywhere in the filesystem.
    # system1.fail("grep -r secret1234 /tmp")
  '';
}
