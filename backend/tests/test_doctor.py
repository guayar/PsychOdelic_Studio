from psychodelic.doctor import CONFIRMED, UNAVAILABLE, UNVERIFIED, run_doctor


def test_summary_counts_match_items(tmp_path):
    rep = run_doctor(tmp_path, comfy_url="http://127.0.0.1:9")
    total = sum(rep["summary"].values())
    assert total == len(rep["items"])
    assert all(it["status"] in (CONFIRMED, UNVERIFIED, UNAVAILABLE) for it in rep["items"])


def test_unwritable_data_dir_is_unavailable(tmp_path):
    f = tmp_path / "plik"
    f.write_text("x")
    rep = run_doctor(f / "podkatalog", comfy_url="http://127.0.0.1:9")  # sciezka pod plikiem
    st = {it["name"]: it["status"] for it in rep["items"]}
    assert st["data_dir zapisywalny"] == UNAVAILABLE
