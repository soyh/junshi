PRODUCT_MANAGEMENT_HTML = r'''
  <fieldset id="product-management" class="wide">
    <legend>Core Record Management</legend>
    <p class="note">统一管理当前选中的 Person / Relationship / Conversation，并提供 Interaction 编辑删除、Message 显式删除和 Person Profile。所有写操作继续调用现有 canonical API；删除必须由用户显式确认。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="manage-person-heading">
        <h2 id="manage-person-heading">Person management</h2>
        <p class="note">使用 Workspace 中当前选中的 Person。选择后会从服务端重新读取并回填。</p>
        <label for="manage-person-name">Name</label>
        <input id="manage-person-name" class="requires-auth" autocomplete="off" maxlength="200" disabled>
        <label for="manage-person-nickname">Nickname</label>
        <input id="manage-person-nickname" class="requires-auth" autocomplete="off" maxlength="200" disabled>
        <label for="manage-person-notes">Notes</label>
        <textarea id="manage-person-notes" class="requires-auth" disabled></textarea>
        <button id="load-selected-person" class="requires-auth" type="button" disabled>Load selected person</button>
        <button id="update-selected-person" class="requires-auth" type="button" disabled>Save person changes</button>
        <button id="delete-selected-person" class="requires-auth" type="button" disabled>Delete selected person</button>
        <div id="manage-person-status" class="status">Select a person first.</div>
        <div id="person-profile-status" class="status">Person profile not loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="manage-relationship-heading">
        <h2 id="manage-relationship-heading">Relationship management</h2>
        <p class="note">使用当前选中的 Relationship；Person / Relationship scope 一致性仍由服务端校验。</p>
        <label for="manage-relationship-status-value">Status</label>
        <input id="manage-relationship-status-value" class="requires-auth" autocomplete="off" disabled>
        <label for="manage-relationship-stage">Stage</label>
        <input id="manage-relationship-stage" class="requires-auth" autocomplete="off" disabled>
        <label for="manage-relationship-long-term-goal">Long-term goal</label>
        <textarea id="manage-relationship-long-term-goal" class="requires-auth" disabled></textarea>
        <label for="manage-relationship-current-goal">Current goal</label>
        <textarea id="manage-relationship-current-goal" class="requires-auth" disabled></textarea>
        <label for="manage-relationship-notes">Notes</label>
        <textarea id="manage-relationship-notes" class="requires-auth" disabled></textarea>
        <button id="load-selected-relationship" class="requires-auth" type="button" disabled>Load selected relationship</button>
        <button id="update-selected-relationship" class="requires-auth" type="button" disabled>Save relationship changes</button>
        <button id="delete-selected-relationship" class="requires-auth" type="button" disabled>Delete selected relationship</button>
        <div id="manage-relationship-status" class="status">Select a relationship first.</div>
      </section>

      <section class="workspace-card" aria-labelledby="manage-conversation-heading">
        <h2 id="manage-conversation-heading">Conversation management</h2>
        <p class="note">可以修改标题、Relationship 归属与 active / archived 状态；Conversation 仍固定属于原 Person。</p>
        <label for="manage-conversation-title">Title</label>
        <input id="manage-conversation-title" class="requires-auth" autocomplete="off" disabled>
        <label for="manage-conversation-status-value">Status</label>
        <select id="manage-conversation-status-value" class="requires-auth" disabled>
          <option value="active">active</option>
          <option value="archived">archived</option>
        </select>
        <label for="manage-conversation-relationship">Relationship</label>
        <select id="manage-conversation-relationship" class="requires-auth" disabled></select>
        <button id="load-selected-conversation" class="requires-auth" type="button" disabled>Load selected conversation</button>
        <button id="update-selected-conversation" class="requires-auth" type="button" disabled>Save conversation changes</button>
        <button id="archive-selected-conversation" class="requires-auth" type="button" disabled>Archive</button>
        <button id="activate-selected-conversation" class="requires-auth" type="button" disabled>Reactivate</button>
        <button id="delete-selected-conversation" class="requires-auth" type="button" disabled>Delete selected conversation</button>
        <div id="manage-conversation-status" class="status">Select a conversation first.</div>
      </section>

      <section class="workspace-card" aria-labelledby="manage-interaction-heading">
        <h2 id="manage-interaction-heading">Interaction management</h2>
        <p class="note">Interaction 是显式事实记录。可以修正误录内容，也可以显式删除；Timeline 会继续从 canonical records 聚合。</p>
        <button id="load-managed-interactions" class="requires-auth" type="button" disabled>Refresh interactions</button>
        <label for="manage-interaction-select">Interaction</label>
        <select id="manage-interaction-select" class="requires-auth" size="5" disabled></select>
        <label for="manage-interaction-type">Type</label>
        <select id="manage-interaction-type" class="requires-auth" disabled>
          <option value="message">message</option>
          <option value="call">call</option>
          <option value="meeting">meeting</option>
          <option value="date">date</option>
          <option value="gift">gift</option>
          <option value="other">other</option>
        </select>
        <label for="manage-interaction-occurred-at">Occurred at</label>
        <input id="manage-interaction-occurred-at" class="requires-auth" autocomplete="off" disabled>
        <label for="manage-interaction-relationship">Relationship</label>
        <select id="manage-interaction-relationship" class="requires-auth" disabled></select>
        <label for="manage-interaction-content">Content</label>
        <textarea id="manage-interaction-content" class="requires-auth" disabled></textarea>
        <button id="update-selected-interaction" class="requires-auth" type="button" disabled>Save interaction changes</button>
        <button id="delete-selected-interaction" class="requires-auth" type="button" disabled>Delete selected interaction</button>
        <div id="manage-interaction-status" class="status">Select a person first.</div>
      </section>

      <section class="workspace-card" aria-labelledby="manage-message-heading">
        <h2 id="manage-message-heading">Message management</h2>
        <p class="note">历史消息作为 evidence 不提供 PATCH。若录入错误，可显式删除后重新添加，避免静默改写历史证据。</p>
        <button id="load-managed-messages" class="requires-auth" type="button" disabled>Refresh messages</button>
        <label for="manage-message-select">Message</label>
        <select id="manage-message-select" class="requires-auth" size="6" disabled></select>
        <div id="manage-message-detail" class="status">Select a conversation first.</div>
        <button id="delete-selected-message" class="requires-auth" type="button" disabled>Delete selected message</button>
        <div id="manage-message-status" class="status">Select a conversation first.</div>
      </section>
    </div>
  </fieldset>
'''


PRODUCT_MANAGEMENT_SCRIPT = r'''
  const managePersonStatus = byId('manage-person-status');
  const personProfileStatus = byId('person-profile-status');
  const manageRelationshipStatus = byId('manage-relationship-status');
  const manageConversationStatus = byId('manage-conversation-status');
  const manageInteractionStatus = byId('manage-interaction-status');
  const manageMessageStatus = byId('manage-message-status');
  const manageMessageDetail = byId('manage-message-detail');
  let selectedManagedInteractionId = null;
  let selectedManagedMessageId = null;
  let managedMessageItems = [];

  function setFieldValue(id, value) {
    byId(id).value = value == null ? '' : String(value);
  }

  function resetEntitySelect(id, placeholder) {
    resetSelect(id, placeholder);
  }

  function renderEntitySelect(id, items, labelFor, placeholder, selectedValue = null) {
    renderSelect(id, items, labelFor, placeholder, selectedValue);
  }

  function confirmDelete(label) {
    return window.confirm(`Delete ${label}? This action cannot be undone.`);
  }

  function clearPersonManagement(message = 'Select a person first.') {
    setFieldValue('manage-person-name', '');
    setFieldValue('manage-person-nickname', '');
    setFieldValue('manage-person-notes', '');
    managePersonStatus.textContent = message;
    personProfileStatus.textContent = 'Person profile not loaded.';
  }

  function clearRelationshipManagement(message = 'Select a relationship first.') {
    setFieldValue('manage-relationship-status-value', '');
    setFieldValue('manage-relationship-stage', '');
    setFieldValue('manage-relationship-long-term-goal', '');
    setFieldValue('manage-relationship-current-goal', '');
    setFieldValue('manage-relationship-notes', '');
    manageRelationshipStatus.textContent = message;
  }

  function clearConversationManagement(message = 'Select a conversation first.') {
    setFieldValue('manage-conversation-title', '');
    setFieldValue('manage-conversation-status-value', 'active');
    resetEntitySelect('manage-conversation-relationship', 'No relationship');
    manageConversationStatus.textContent = message;
  }

  function clearInteractionManagement(message = 'Select a person first.') {
    selectedManagedInteractionId = null;
    resetEntitySelect('manage-interaction-select', 'No interaction selected');
    resetEntitySelect('manage-interaction-relationship', 'No relationship');
    setFieldValue('manage-interaction-type', 'message');
    setFieldValue('manage-interaction-occurred-at', '');
    setFieldValue('manage-interaction-content', '');
    manageInteractionStatus.textContent = message;
  }

  function clearMessageManagement(message = 'Select a conversation first.') {
    selectedManagedMessageId = null;
    managedMessageItems = [];
    resetEntitySelect('manage-message-select', 'No message selected');
    manageMessageDetail.textContent = message;
    manageMessageStatus.textContent = message;
  }

  function resetProductManagement() {
    clearPersonManagement();
    clearRelationshipManagement();
    clearConversationManagement();
    clearInteractionManagement();
    clearMessageManagement();
  }

  async function currentPersonRelationships() {
    if (!selectedPersonId) return [];
    const items = await api('/api/v1/relationships');
    return items.filter((item) => item.person_id === selectedPersonId);
  }

  async function populateRelationshipChoice(id, selectedValue = null) {
    const items = await currentPersonRelationships();
    renderEntitySelect(
      id,
      items,
      (item) => `${item.status} · ${item.stage}`,
      'No relationship',
      selectedValue,
    );
  }

  async function loadSelectedPersonManagement() {
    if (!selectedPersonId) {
      clearPersonManagement();
      return;
    }
    const item = await api(`/api/v1/persons/${encodeURIComponent(selectedPersonId)}`);
    setFieldValue('manage-person-name', item.name);
    setFieldValue('manage-person-nickname', item.nickname);
    setFieldValue('manage-person-notes', item.notes);
    managePersonStatus.textContent = `Loaded ${item.name}.`;

    const profile = await api(`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/profile`);
    const latest = profile.latest_interaction
      ? `${profile.latest_interaction.type || 'interaction'} @ ${profile.latest_interaction.occurred_at || '(unknown time)'}`
      : 'none';
    personProfileStatus.textContent = `Profile: ${profile.relationships.length} relationship(s) · statistics ${JSON.stringify(profile.statistics)} · latest interaction ${latest}`;
  }

  async function updateSelectedPersonManagement() {
    if (!selectedPersonId) throw new Error('Select a person first');
    const name = byId('manage-person-name').value.trim();
    if (!name) throw new Error('Person name is required');
    const updated = await api(`/api/v1/persons/${encodeURIComponent(selectedPersonId)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        name,
        nickname: nullableText('manage-person-nickname'),
        notes: nullableText('manage-person-notes'),
      }),
    });
    await loadPersons();
    await loadSelectedPersonManagement();
    managePersonStatus.textContent = `Saved ${updated.name}.`;
  }

  async function deleteSelectedPersonManagement() {
    if (!selectedPersonId) throw new Error('Select a person first');
    const deletingId = selectedPersonId;
    if (!confirmDelete('the selected person and any server-defined dependent records')) return;
    await api(`/api/v1/persons/${encodeURIComponent(deletingId)}`, { method: 'DELETE' });
    selectedPersonId = null;
    selectedRelationshipId = null;
    selectedConversationId = null;
    byId('conversation-id').value = '';
    resetProductManagement();
    await loadPersons();
    managePersonStatus.textContent = 'Person deleted.';
  }

  async function loadSelectedRelationshipManagement() {
    if (!selectedRelationshipId) {
      clearRelationshipManagement();
      return;
    }
    const item = await api(`/api/v1/relationships/${encodeURIComponent(selectedRelationshipId)}`);
    setFieldValue('manage-relationship-status-value', item.status);
    setFieldValue('manage-relationship-stage', item.stage);
    setFieldValue('manage-relationship-long-term-goal', item.long_term_goal);
    setFieldValue('manage-relationship-current-goal', item.current_goal);
    setFieldValue('manage-relationship-notes', item.notes);
    manageRelationshipStatus.textContent = `Loaded relationship ${item.status} · ${item.stage}.`;
  }

  async function updateSelectedRelationshipManagement() {
    if (!selectedRelationshipId) throw new Error('Select a relationship first');
    const updated = await api(`/api/v1/relationships/${encodeURIComponent(selectedRelationshipId)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        status: byId('manage-relationship-status-value').value.trim() || 'unknown',
        stage: byId('manage-relationship-stage').value.trim() || 'unknown',
        long_term_goal: nullableText('manage-relationship-long-term-goal'),
        current_goal: nullableText('manage-relationship-current-goal'),
        notes: nullableText('manage-relationship-notes'),
      }),
    });
    await loadRelationships();
    await loadSelectedRelationshipManagement();
    await populateRelationshipChoice('manage-conversation-relationship', selectedRelationshipId);
    await populateRelationshipChoice('manage-interaction-relationship');
    manageRelationshipStatus.textContent = `Saved relationship ${updated.status} · ${updated.stage}.`;
  }

  async function deleteSelectedRelationshipManagement() {
    if (!selectedRelationshipId) throw new Error('Select a relationship first');
    const deletingId = selectedRelationshipId;
    if (!confirmDelete('the selected relationship')) return;
    await api(`/api/v1/relationships/${encodeURIComponent(deletingId)}`, { method: 'DELETE' });
    selectedRelationshipId = null;
    clearRelationshipManagement();
    await loadRelationships();
    await loadConversations();
    await populateRelationshipChoice('manage-conversation-relationship');
    await populateRelationshipChoice('manage-interaction-relationship');
    manageRelationshipStatus.textContent = 'Relationship deleted.';
  }

  async function loadSelectedConversationManagement() {
    if (!selectedConversationId) {
      clearConversationManagement();
      return;
    }
    const item = await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}`);
    setFieldValue('manage-conversation-title', item.title);
    setFieldValue('manage-conversation-status-value', item.status);
    await populateRelationshipChoice('manage-conversation-relationship', item.relationship_id);
    manageConversationStatus.textContent = `Loaded ${item.title || '(untitled)'} · ${item.status}.`;
  }

  async function updateSelectedConversationManagement() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    const updated = await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        relationship_id: byId('manage-conversation-relationship').value || null,
        title: nullableText('manage-conversation-title'),
        status: byId('manage-conversation-status-value').value,
      }),
    });
    await loadConversations();
    byId('conversation-select').value = selectedConversationId;
    await loadSelectedConversationManagement();
    manageConversationStatus.textContent = `Saved ${updated.title || '(untitled)'} · ${updated.status}.`;
  }

  async function setSelectedConversationStatus(status) {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    const updated = await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
    await loadConversations();
    byId('conversation-select').value = selectedConversationId;
    await loadSelectedConversationManagement();
    manageConversationStatus.textContent = `Conversation is now ${updated.status}.`;
  }

  async function deleteSelectedConversationManagement() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    const deletingId = selectedConversationId;
    if (!confirmDelete('the selected conversation and its server-defined dependent records')) return;
    await api(`/api/v1/conversations/${encodeURIComponent(deletingId)}`, { method: 'DELETE' });
    selectedConversationId = null;
    byId('conversation-id').value = '';
    clearConversationManagement();
    clearMessageManagement();
    await loadConversations();
    manageConversationStatus.textContent = 'Conversation deleted.';
  }

  async function loadManagedInteractions() {
    if (!selectedPersonId) {
      clearInteractionManagement();
      return;
    }
    const items = await api(`/api/v1/interactions?person_id=${encodeURIComponent(selectedPersonId)}`);
    if (!items.some((item) => item.id === selectedManagedInteractionId)) selectedManagedInteractionId = null;
    renderEntitySelect(
      'manage-interaction-select',
      items,
      (item) => `${item.occurred_at} · ${item.type}`,
      'No interaction selected',
      selectedManagedInteractionId,
    );
    if (selectedManagedInteractionId) {
      await loadSelectedManagedInteraction();
    } else {
      await populateRelationshipChoice('manage-interaction-relationship');
    }
    manageInteractionStatus.textContent = `${items.length} interaction(s) available.`;
  }

  async function loadSelectedManagedInteraction() {
    selectedManagedInteractionId = byId('manage-interaction-select').value || null;
    if (!selectedManagedInteractionId) {
      setFieldValue('manage-interaction-occurred-at', '');
      setFieldValue('manage-interaction-content', '');
      manageInteractionStatus.textContent = 'Select an interaction.';
      return;
    }
    const item = await api(`/api/v1/interactions/${encodeURIComponent(selectedManagedInteractionId)}`);
    setFieldValue('manage-interaction-type', item.type);
    setFieldValue('manage-interaction-occurred-at', item.occurred_at);
    setFieldValue('manage-interaction-content', item.content);
    await populateRelationshipChoice('manage-interaction-relationship', item.relationship_id);
    manageInteractionStatus.textContent = `Loaded ${item.type} interaction.`;
  }

  async function updateSelectedManagedInteraction() {
    if (!selectedManagedInteractionId) throw new Error('Select an interaction first');
    const occurredAt = byId('manage-interaction-occurred-at').value.trim();
    if (!occurredAt) throw new Error('Interaction occurred_at is required');
    const updated = await api(`/api/v1/interactions/${encodeURIComponent(selectedManagedInteractionId)}`, {
      method: 'PATCH',
      body: JSON.stringify({
        relationship_id: byId('manage-interaction-relationship').value || null,
        type: byId('manage-interaction-type').value,
        occurred_at: occurredAt,
        content: nullableText('manage-interaction-content'),
      }),
    });
    await loadManagedInteractions();
    byId('manage-interaction-select').value = selectedManagedInteractionId;
    await loadSelectedManagedInteraction();
    await loadInteractions();
    await loadTimeline();
    manageInteractionStatus.textContent = `Saved ${updated.type} interaction.`;
  }

  async function deleteSelectedManagedInteraction() {
    if (!selectedManagedInteractionId) throw new Error('Select an interaction first');
    const deletingId = selectedManagedInteractionId;
    if (!confirmDelete('the selected interaction')) return;
    await api(`/api/v1/interactions/${encodeURIComponent(deletingId)}`, { method: 'DELETE' });
    selectedManagedInteractionId = null;
    await loadManagedInteractions();
    await loadInteractions();
    await loadTimeline();
    manageInteractionStatus.textContent = 'Interaction deleted.';
  }

  function renderManagedMessageDetail(item) {
    if (!item) {
      manageMessageDetail.textContent = 'Select a message.';
      return;
    }
    manageMessageDetail.textContent = `${item.sent_at} · ${item.sender_type}\n${item.content}`;
  }

  async function loadManagedMessages() {
    if (!selectedConversationId) {
      clearMessageManagement();
      return;
    }
    managedMessageItems = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/messages`
    );
    if (!managedMessageItems.some((item) => item.id === selectedManagedMessageId)) selectedManagedMessageId = null;
    renderEntitySelect(
      'manage-message-select',
      managedMessageItems,
      (item) => `${item.sent_at} · ${item.sender_type} · ${String(item.content).slice(0, 48)}`,
      'No message selected',
      selectedManagedMessageId,
    );
    renderManagedMessageDetail(
      managedMessageItems.find((item) => item.id === selectedManagedMessageId) || null
    );
    manageMessageStatus.textContent = `${managedMessageItems.length} message(s) available.`;
  }

  function selectManagedMessage() {
    selectedManagedMessageId = byId('manage-message-select').value || null;
    renderManagedMessageDetail(
      managedMessageItems.find((item) => item.id === selectedManagedMessageId) || null
    );
  }

  async function deleteSelectedManagedMessage() {
    if (!selectedManagedMessageId) throw new Error('Select a message first');
    const deletingId = selectedManagedMessageId;
    if (!confirmDelete('the selected message evidence record')) return;
    await api(`/api/v1/messages/${encodeURIComponent(deletingId)}`, { method: 'DELETE' });
    selectedManagedMessageId = null;
    await loadManagedMessages();
    await loadMessages();
    manageMessageStatus.textContent = 'Message deleted. Historical messages are not silently edited.';
  }

  async function refreshManagementForPerson() {
    if (!selectedPersonId) {
      resetProductManagement();
      return;
    }
    await loadSelectedPersonManagement();
    clearRelationshipManagement();
    clearConversationManagement();
    await loadManagedInteractions();
    clearMessageManagement();
  }

  const baseResetWorkspaceForProductManagement = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForProductManagement(message);
    resetProductManagement();
  };

  bind('load-selected-person', loadSelectedPersonManagement, managePersonStatus);
  bind('update-selected-person', updateSelectedPersonManagement, managePersonStatus);
  bind('delete-selected-person', deleteSelectedPersonManagement, managePersonStatus);
  bind('load-selected-relationship', loadSelectedRelationshipManagement, manageRelationshipStatus);
  bind('update-selected-relationship', updateSelectedRelationshipManagement, manageRelationshipStatus);
  bind('delete-selected-relationship', deleteSelectedRelationshipManagement, manageRelationshipStatus);
  bind('load-selected-conversation', loadSelectedConversationManagement, manageConversationStatus);
  bind('update-selected-conversation', updateSelectedConversationManagement, manageConversationStatus);
  bind('archive-selected-conversation', () => setSelectedConversationStatus('archived'), manageConversationStatus);
  bind('activate-selected-conversation', () => setSelectedConversationStatus('active'), manageConversationStatus);
  bind('delete-selected-conversation', deleteSelectedConversationManagement, manageConversationStatus);
  bind('load-managed-interactions', loadManagedInteractions, manageInteractionStatus);
  bind('update-selected-interaction', updateSelectedManagedInteraction, manageInteractionStatus);
  bind('delete-selected-interaction', deleteSelectedManagedInteraction, manageInteractionStatus);
  bind('load-managed-messages', loadManagedMessages, manageMessageStatus);
  bind('delete-selected-message', deleteSelectedManagedMessage, manageMessageStatus);

  byId('manage-interaction-select').addEventListener('change', async () => {
    try { await loadSelectedManagedInteraction(); }
    catch (error) { manageInteractionStatus.textContent = error instanceof Error ? error.message : String(error); }
  });
  byId('manage-message-select').addEventListener('change', selectManagedMessage);

  byId('person-select').addEventListener('change', async () => {
    try { await refreshManagementForPerson(); }
    catch (error) { managePersonStatus.textContent = error instanceof Error ? error.message : String(error); }
  });
  byId('relationship-select').addEventListener('change', async () => {
    try { await loadSelectedRelationshipManagement(); }
    catch (error) { manageRelationshipStatus.textContent = error instanceof Error ? error.message : String(error); }
  });
  byId('conversation-select').addEventListener('change', async () => {
    try {
      await loadSelectedConversationManagement();
      await loadManagedMessages();
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      manageConversationStatus.textContent = message;
      manageMessageStatus.textContent = message;
    }
  });
'''
