from app.services import vector_store


def test_search_is_scoped_to_workspace(monkeypatch):
    captured = {}

    class FakeQueryResult:
        points = [
            {
                "payload": {
                    "workspace_id": 1,
                    "document_id": 10,
                    "chunk_index": 0,
                    "text": "workspace one",
                }
            }
        ]

    def fake_query_points(**kwargs):
        captured.update(kwargs)
        return FakeQueryResult()

    monkeypatch.setattr(
        vector_store.client,
        "query_points",
        fake_query_points,
    )

    results = vector_store.search(
        workspace_id=1,
        query_vector=[0.1] * 768,
        limit=5,
    )

    assert results == FakeQueryResult.points

    query_filter = captured["query_filter"]

    assert len(query_filter.must) == 1
    assert query_filter.must[0].key == "workspace_id"
    assert query_filter.must[0].match.value == 1

