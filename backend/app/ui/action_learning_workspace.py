ACTION_LEARNING_HTML = r'''
  <fieldset id="action-learning-workspace" class="wide">
    <legend>Learning</legend>
    <p class="note">TEST-145 将现有 canonical Learning / Memory Update contract 接入统一 /app。Learning proposal 只来自已观察 Outcome，并保留 provenance 与 unknowns；不会自动持久化、调用 LLM、触发 Re-analysis、发送消息或修改 Relationship。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-learning-heading">
        <h2 id="action-learning-heading">Learning Proposals</h2>
        <p class="note">只有显式点击 Load learning 才读取当前 Person 的 source-backed learning synthesis。proposal 不是已保存事实，也不会自动应用到策略。</p>
        <button id="load-action-learning" class="requires-auth" type="button" disabled>Load learning</button>
        <label for="action-learning-candidate">Learning memory proposal</label>
        <select id="action-learning-candidate" disabled>
          <option value="">Load learning first</option>
        </select>
        <div id="action-learning-candidate-detail" class="status">No learning proposal selected.</div>
        <button id="persist-action-learning" type="button" disabled>Persist selected learning memory</button>
        <div id="action-learning-status" class="status">Select a person, then load learning.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-learning-persisted-heading">
        <h2 id="action-learning-persisted-heading">Persist Result</h2>
        <p class="note">当前 canonical API 没有 persisted-memory history GET。这里仅显示本页显式 persist 的服务端返回；重复 persist 由服务端 candidate-level idempotency 保证。</p>
        <div id="action-learning-persisted" class="status">No learning memory persisted in this page session.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_LEARNING_SCRIPT = r'''
  const actionLearningStatus = byId('action-learning-status');
  const actionLearningSelect = byId('action-learning-candidate');
  const actionLearningCandidateDetail = byId('action-learning-candidate-detail');
  const actionLearningPersisted = byId('action-learning-persisted');
  const persistActionLearningButton = byId('persist-action-learning');
  let actionLearningCandidates = [];

  function resetActionLearningWorkspace() {
    actionLearningCandidates = [];
    actionLearningSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Load learning first';
    actionLearningSelect.appendChild(placeholder);
    actionLearningSelect.disabled = true;
    persistActionLearningButton.disabled = true;
    actionLearningCandidateDetail.replaceChildren();
    actionLearningCandidateDetail.textContent = 'No learning proposal selected.';
    actionLearningPersisted.replaceChildren();
    actionLearningPersisted.textContent = 'No learning memory persisted in this page session.';
    actionLearningStatus.textContent = selectedPersonId
      ? 'Click Load learning to read source-backed learning proposals.'
      : 'Select a person, then load learning.';
  }

  function appendLearningField(parent, label, value) {
    const line = document.createElement('div');
    line.textContent = `${label}=${value === null || value === undefined || value === '' ? '(none)' : value}`;
    parent.appendChild(line);
  }

  function renderActionLearningCandidates(body) {
    actionLearningCandidates = body && Array.isArray(body.updates) ? body.updates : [];
    actionLearningSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = actionLearningCandidates.length
      ? 'Select a learning memory proposal'
      : 'No source-backed learning proposal';
    actionLearningSelect.appendChild(placeholder);

    actionLearningCandidates.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.source_candidate_id || '';
      const outcome = item.memory && item.memory.action_outcome ? item.memory.action_outcome : 'unknown';
      option.textContent = `${outcome} · ${item.source_candidate_id || '(no candidate id)'}`;
      actionLearningSelect.appendChild(option);
    });

    actionLearningSelect.disabled = actionLearningCandidates.length === 0;
    persistActionLearningButton.disabled = true;
    actionLearningCandidateDetail.textContent = actionLearningCandidates.length
      ? `${actionLearningCandidates.length} proposed learning memory item(s). Select one to inspect provenance.`
      : 'No observed Outcome currently produces a learning memory proposal.';
  }

  function renderSelectedActionLearningCandidate() {
    const candidateId = actionLearningSelect.value;
    const item = actionLearningCandidates.find((candidate) => candidate.source_candidate_id === candidateId);
    persistActionLearningButton.disabled = !item;
    actionLearningCandidateDetail.replaceChildren();
    if (!item) {
      actionLearningCandidateDetail.textContent = actionLearningCandidates.length
        ? 'Select a learning memory proposal.'
        : 'No learning proposal selected.';
      return;
    }

    const provenance = item.learning_provenance || {};
    appendLearningField(actionLearningCandidateDetail, 'status', item.status);
    appendLearningField(actionLearningCandidateDetail, 'category', item.category);
    appendLearningField(actionLearningCandidateDetail, 'source_candidate_id', item.source_candidate_id);
    appendLearningField(actionLearningCandidateDetail, 'source_decision_id', item.source_decision_id);
    appendLearningField(actionLearningCandidateDetail, 'source_outcome_id', item.source_outcome_id);
    appendLearningField(actionLearningCandidateDetail, 'observed_outcome', item.memory && item.memory.action_outcome);
    appendLearningField(actionLearningCandidateDetail, 'provenance_status', provenance.status);
    appendLearningField(actionLearningCandidateDetail, 'recommendation_id', provenance.recommendation_id);
    appendLearningField(actionLearningCandidateDetail, 'outcome_observed_count', provenance.outcome_observed_count);
    appendLearningField(actionLearningCandidateDetail, 'outcome_unknown_count', provenance.outcome_unknown_count);
    appendLearningField(actionLearningCandidateDetail, 'unknowns', Array.isArray(item.unknowns) ? item.unknowns.join(', ') : 'unknown');
  }

  function renderPersistedLearning(item) {
    actionLearningPersisted.replaceChildren();
    if (!item) {
      actionLearningPersisted.textContent = 'No learning memory persisted in this page session.';
      return;
    }
    appendLearningField(actionLearningPersisted, 'status', item.status);
    appendLearningField(actionLearningPersisted, 'id', item.id);
    appendLearningField(actionLearningPersisted, 'category', item.category);
    appendLearningField(actionLearningPersisted, 'person_id', item.person_id);
    appendLearningField(actionLearningPersisted, 'source_candidate_id', item.source_candidate_id);
    appendLearningField(actionLearningPersisted, 'source_decision_id', item.source_decision_id);
    appendLearningField(actionLearningPersisted, 'source_outcome_id', item.source_outcome_id);
    appendLearningField(actionLearningPersisted, 'action_outcome', item.memory && item.memory.action_outcome);
    appendLearningField(actionLearningPersisted, 'created_at', item.created_at);
  }

  async function loadActionLearning() {
    if (!selectedPersonId) throw new Error('Select a person first');
    actionLearningStatus.textContent = 'Loading source-backed learning proposals...';
    const body = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/memory-updates/learning-synthesis`
    );
    renderActionLearningCandidates(body);
    renderPersistedLearning(null);
    actionLearningStatus.textContent = `${actionLearningCandidates.length} learning proposal(s) loaded. Nothing was persisted, re-analyzed, executed, or sent automatically.`;
  }

  async function persistSelectedActionLearning() {
    if (!selectedPersonId) throw new Error('Select a person first');
    const candidateId = actionLearningSelect.value;
    const candidate = actionLearningCandidates.find((item) => item.source_candidate_id === candidateId);
    if (!candidate) throw new Error('Select a learning memory proposal first');

    actionLearningStatus.textContent = 'Persisting selected learning memory explicitly...';
    const created = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/memory-updates/${encodeURIComponent(candidateId)}/persist`,
      {method: 'POST'},
    );
    renderPersistedLearning(created);
    actionLearningStatus.textContent = `Learning memory ${created.id} is persisted. No Re-analysis, strategy application, LLM call, message send, or Relationship change was started.`;
  }

  const baseResetWorkspaceForActionLearning = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionLearning(message);
    resetActionLearningWorkspace();
  };

  bind('load-action-learning', loadActionLearning, actionLearningStatus);
  bind('persist-action-learning', persistSelectedActionLearning, actionLearningStatus);

  actionLearningSelect.addEventListener('change', renderSelectedActionLearningCandidate);

  byId('person-select').addEventListener('change', () => {
    resetActionLearningWorkspace();
  });
'''
