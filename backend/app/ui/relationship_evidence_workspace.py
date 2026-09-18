RELATIONSHIP_EVIDENCE_HTML = r'''
  <fieldset id="relationship-evidence" class="wide">
    <legend>Relationship Evidence & Timeline</legend>
    <p class="note">TEST-138 只复用现有 Interaction 与 Person Timeline canonical API。Interaction 是用户显式记录的关系事件；Timeline 是只读聚合视图，不创建第二套事件数据。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="interaction-heading">
        <h2 id="interaction-heading">Interactions</h2>
        <p class="note">事件始终绑定当前 Person；当前 Relationship 可选。Relationship 是否属于 Person 继续由服务端 canonical service 校验。</p>
        <label for="interaction-type">Type</label>
        <select id="interaction-type" class="requires-auth" disabled>
          <option value="message">message</option>
          <option value="call">call</option>
          <option value="meeting">meeting</option>
          <option value="date">date</option>
          <option value="gift">gift</option>
          <option value="other">other</option>
        </select>
        <label for="interaction-occurred-at">Occurred at (ISO 8601)</label>
        <input id="interaction-occurred-at" class="requires-auth" autocomplete="off" placeholder="2026-09-18T12:00:00+00:00" disabled>
        <label for="interaction-content">Content (optional)</label>
        <textarea id="interaction-content" class="requires-auth" disabled></textarea>
        <button id="load-interactions" class="requires-auth" type="button" disabled>Refresh interactions</button>
        <button id="create-interaction" class="requires-auth" type="button" disabled>Add interaction</button>
        <div id="interaction-status" class="status">Select a person first.</div>
        <div id="interaction-list" class="status">No person selected.</div>
      </section>

      <section class="workspace-card" aria-labelledby="timeline-heading">
        <h2 id="timeline-heading">Person Timeline</h2>
        <p class="note">只读聚合当前 Person 的 Conversation、Message 与 Interaction evidence；顺序、分页、source metadata 均由现有 TimelineService 决定。</p>
        <button id="load-timeline" class="requires-auth" type="button" disabled>Refresh timeline</button>
        <div id="timeline-status" class="status">Select a person first.</div>
        <div id="timeline-list" class="status">No person selected.</div>
      </section>
    </div>
  </fieldset>
'''


RELATIONSHIP_EVIDENCE_SCRIPT = r'''
  const interactionStatus = byId('interaction-status');
  const interactionList = byId('interaction-list');
  const timelineStatus = byId('timeline-status');
  const timelineList = byId('timeline-list');

  function resetRelationshipEvidence(message = 'Select a person first.') {
    interactionList.replaceChildren();
    interactionList.textContent = 'No person selected.';
    timelineList.replaceChildren();
    timelineList.textContent = 'No person selected.';
    interactionStatus.textContent = message;
    timelineStatus.textContent = message;
    byId('interaction-occurred-at').value = '';
    byId('interaction-content').value = '';
  }

  function renderInteractions(items) {
    interactionList.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      interactionList.textContent = 'No interactions for the selected person.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const meta = document.createElement('div');
      const body = document.createElement('div');
      const relationship = item.relationship_id ? ` · relationship ${item.relationship_id}` : '';
      meta.textContent = `${item.occurred_at} · ${item.type}${relationship}`;
      body.textContent = item.content || '(no content)';
      row.append(meta, body);
      interactionList.appendChild(row);
    });
  }

  async function loadInteractions() {
    if (!selectedPersonId) {
      resetRelationshipEvidence();
      return;
    }
    interactionStatus.textContent = 'Loading interactions...';
    const items = await api(`/api/v1/interactions?person_id=${encodeURIComponent(selectedPersonId)}`);
    renderInteractions(items);
    interactionStatus.textContent = `${items.length} interaction(s) loaded for the selected person.`;
  }

  async function createInteraction() {
    if (!selectedPersonId) throw new Error('Select a person first');
    const occurredAt = byId('interaction-occurred-at').value.trim();
    if (!occurredAt) throw new Error('Interaction occurred_at is required');
    const payload = {
      person_id: selectedPersonId,
      relationship_id: selectedRelationshipId,
      type: byId('interaction-type').value,
      occurred_at: occurredAt,
      content: nullableText('interaction-content'),
    };
    const created = await api('/api/v1/interactions', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    byId('interaction-occurred-at').value = '';
    byId('interaction-content').value = '';
    await loadInteractions();
    await loadTimeline();
    interactionStatus.textContent = `Added ${created.type} interaction at ${created.occurred_at}.`;
  }

  function renderTimeline(data) {
    timelineList.replaceChildren();
    const items = data && Array.isArray(data.items) ? data.items : [];
    if (items.length === 0) {
      timelineList.textContent = 'No timeline events for the selected person.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const meta = document.createElement('div');
      const title = document.createElement('div');
      const body = document.createElement('div');
      meta.textContent = `${item.occurred_at} · ${item.event_type} · ${item.source_type}`;
      title.textContent = item.title || `${item.source_type}:${item.source_id}`;
      body.textContent = item.content || '';
      row.append(meta, title, body);
      timelineList.appendChild(row);
    });
  }

  async function loadTimeline() {
    if (!selectedPersonId) {
      resetRelationshipEvidence();
      return;
    }
    timelineStatus.textContent = 'Loading timeline...';
    const data = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/timeline?limit=50&offset=0`
    );
    renderTimeline(data);
    timelineStatus.textContent = `${data.items.length} of ${data.total} timeline event(s) loaded.`;
  }

  async function loadRelationshipEvidence() {
    if (!selectedPersonId) {
      resetRelationshipEvidence();
      return;
    }
    await loadInteractions();
    await loadTimeline();
  }

  const baseResetWorkspaceForEvidence = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForEvidence(message);
    resetRelationshipEvidence();
  };

  bind('load-interactions', loadInteractions, interactionStatus);
  bind('create-interaction', createInteraction, interactionStatus);
  bind('load-timeline', loadTimeline, timelineStatus);

  byId('person-select').addEventListener('change', async () => {
    try { await loadRelationshipEvidence(); }
    catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      interactionStatus.textContent = message;
      timelineStatus.textContent = message;
    }
  });

  byId('relationship-select').addEventListener('change', () => {
    interactionStatus.textContent = selectedPersonId
      ? (selectedRelationshipId
        ? 'New interactions will bind to the selected relationship.'
        : 'New interactions will be person-level unless a relationship is selected.')
      : 'Select a person first.';
  });
'''
