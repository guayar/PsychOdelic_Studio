from psy_extender.cli import main


def test_cli_builds_tree_and_dry_run(tmp_path, capsys):
    chain = str(tmp_path / "chain.json")
    assert main(["--chain", chain, "add", "Ogród", "--id", "r"]) == 0
    assert main(["--chain", chain, "add", "Scena 2", "--parent", "r", "--id", "s2"]) == 0
    assert main(["--chain", chain, "ref", "r", "add", "gardener.png"]) == 0
    assert main(["--chain", chain, "tree"]) == 0
    out = capsys.readouterr().out
    assert "Ogród" in out and "Scena 2" in out
    assert main(["--chain", chain, "run", "s2"]) == 0  # tylko podglad, bez --execute
    assert "gen_extender_refine.py" in capsys.readouterr().out


def test_cli_refuses_execute_without_oug(tmp_path):
    chain = str(tmp_path / "chain.json")
    main(["--chain", chain, "add", "A", "--id", "a"])
    assert main(["--chain", chain, "run", "a", "--execute"]) == 2
