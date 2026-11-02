def test_prompt_roundtrip_and_traversal_blocked(client):
    pid = client.post("/api/projects", json={"name": "P"}).json()["id"]
    r = client.put(f"/api/projects/{pid}/prompts/s1", json={"content": "Gardener stands still."})
    assert r.status_code == 200 and r.json()["rel_path"] == "prompts/s1.txt"
    assert client.get(f"/api/projects/{pid}/prompts/s1").json()["content"] == "Gardener stands still."
    assert [p["name"] for p in client.get(f"/api/projects/{pid}/prompts").json()] == ["s1.txt"]
    assert client.put(f"/api/projects/{pid}/prompts/..%2Fevil", json={"content": "x"}).status_code in (404, 422)
    assert client.get(f"/api/projects/{pid}/prompts/nope").status_code == 404
