def test_interaction_refresh_reloads_selected_record_before_editing(client):
    html = client.get("/app").text
    start = html.index("async function loadManagedInteractions()")
    end = html.index("async function loadSelectedManagedInteraction()")
    fragment = html[start:end]

    assert "if (selectedManagedInteractionId)" in fragment
    assert "await loadSelectedManagedInteraction();" in fragment
    assert "await populateRelationshipChoice('manage-interaction-relationship');" in fragment


def test_interaction_selected_record_load_restores_relationship_value(client):
    html = client.get("/app").text
    start = html.index("async function loadSelectedManagedInteraction()")
    end = html.index("async function updateSelectedManagedInteraction()")
    fragment = html[start:end]

    assert "item.relationship_id" in fragment
    assert "await populateRelationshipChoice('manage-interaction-relationship', item.relationship_id);" in fragment
