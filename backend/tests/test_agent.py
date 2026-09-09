def test_agent_workflows_and_observability(client):
    user_login = client.post("/api/auth/login", json={"email": "user@eventagent.io", "password": "user123"})
    headers = {"Authorization": f"Bearer {user_login.json()['access_token']}"}

    # 1. Search Request
    resp1 = client.post("/api/chat", json={"message": "Find an AI workshop"}, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["detected_intent"] == "SEARCH_EVENT"

    # 2. Multi-step Search & Register Request
    resp2 = client.post("/api/chat", json={"message": "Find an AI workshop and register me"}, headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["detected_intent"] == "MULTI_STEP_SEARCH_AND_REGISTER"

    # 3. Policy RAG Request
    resp3 = client.post("/api/chat", json={"message": "What is the cancellation policy?"}, headers=headers)
    assert resp3.status_code == 200
    assert resp3.json()["detected_intent"] == "POLICY_RAG"

    # 4. Observability Log Check
    obs = client.get("/api/observability/runs", headers=headers)
    assert obs.status_code == 200
    assert len(obs.json()) >= 3
