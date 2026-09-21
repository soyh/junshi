ACTION_OUTCOME_HTML = r'''
  <fieldset id="action-outcome-workspace" class="wide">
    <legend>Outcome</legend>
    <p class="note">TEST-143 只把现有 canonical Action Outcome contract 接入统一 /app。Outcome 只能由用户基于已执行的 confirmed Action Decision 显式记录；Execution 不会自动生成 Outcome，Outcome 也不会自动触发 Feedback、Learning、Re-analysis、发送消息或修改 Relationship。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-outcome-heading">
        <h2 id="action-outcome-heading">Explicit Outcome Record</h2>
        <p class="note">客户端只把 execution_status=executed 的 confirmed decision 作为候选；服务端 POST 时仍会重新校验 decision scope、confirmed、Execution 存在与 duplicate Outcome，因此客户端不是 authority。</p>
        <button id="load-action-outcome-context" class="requires-auth" type="button" disabled>Load outcome context</button>
        <label for="action-outcome-decision">Executed decision without Outcome</label>
        <select id="action-outcome-decision" disabled>
          <option value="">Load context first</option>
        </select>
        <div id="action-outcome-candidate-detail" class="status">No outcome-ready decision selected.</div>
        <label for="action-outcome-state">Outcome</label>
        <select id="action-outcome-state" class="requires-auth" disabled>
          <option value="completed">completed</option>
          <option value="skipped">skipped</option>
          <option value="failed">failed</option>
        </select>
        <label for="action-outcome-note">Outcome note (optional)</label>
        <textarea id="action-outcome-note" class="requires-auth" disabled></textarea>
        <button id="record-action-outcome" type="button" disabled>Record selected outcome</button>
        <div id="action-outcome-status" class="status">Select a person, then load outcome context.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-outcome-history-heading">
        <h2 id="action-outcome-history-heading">Outcome History</h2>
        <p class="note">这里读取当前 Person 的 canonical Outcome history。Feedback / Learning / Re-analysis 仍保持独立后续阶段。</p>
        <div id="action-outcome-history" class="status">No Outcome history loaded.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_OUTCOME_SCRIPT = r'''
  const actionOutcomeStatus = byId('action-outcome-status');
  const actionOutcomeSelect = byId('action-outcome-decision');
  const actionOutcomeCandidateDetail = byId('action-outcome-candidate-detail');
  const actionOutcomeHistory = byId('action-outcome-history');
  const recordActionOutcomeButton = byId('record-action-outcome');
  let actionOutcomeCandidates = [];

  function resetActionOutcomeWorkspace() {
    actionOutcomeCandidates = [];
    actionOutcomeSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Load context first';
    actionOutcomeSelect.appendChild(placeholder);
    actionOutcomeSelect.disabled = true;
    recordActionOutcomeButton.disabled = true;
    byId('action-outcome-state').value = 'completed';
    byId('action-outcome-note').value = '';
    actionOutcomeCandidateDetail.replaceChildren();
    actionOutcomeCandidateDetail.textContent = 'No outcome-ready decision selected.';
    actionOutcomeHistory.replaceChildren();
    actionOutcomeHistory.textContent = 'No Outcome history loaded.';
    actionOutcomeStatus.textContent = selectedPersonId
      ? 'Click Load outcome context to read executed decisions and Outcome history.'
      : 'Select a person, then load outcome context.';
  }

  function renderActionOutcomeCandidates(decisions) {
    actionOutcomeCandidates = Array.isArray(decisions)
      ? decisions.filter((item) => (
          item &&
          item.id &&
          item.decision === 'confirmed' &&
          item.execution_status === 'executed'
        ))
      : [];
    actionOutcomeSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = actionOutcomeCandidates.length
      ? 'Select an executed decision'
      : 'No executed decision awaiting Outcome';
    actionOutcomeSelect.appendChild(placeholder);
    actionOutcomeCandidates.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = `${item.recommendation_id || '(no recommendation)'} · ${item.id}`;
      actionOutcomeSelect.appendChild(option);
    });
    actionOutcomeSelect.disabled = actionOutcomeCandidates.length === 0;
    recordActionOutcomeButton.disabled = true;
    actionOutcomeCandidateDetail.textContent = actionOutcomeCandidates.length
      ? `${actionOutcomeCandidates.length} executed confirmed decision(s) ready for explicit Outcome recording.`
      : 'No executed confirmed Action Decision currently needs an Outcome.';
  }

  function renderSelectedActionOutcomeCandidate() {
    const decisionId = actionOutcomeSelect.value;
    const item = actionOutcomeCandidates.find((candidate) => candidate.id === decisionId);
    recordActionOutcomeButton.disabled = !item;
    actionOutcomeCandidateDetail.replaceChildren();
    if (!item) {
      actionOutcomeCandidateDetail.textContent = actionOutcomeCandidates.length
        ? 'Select an executed decision.'
        : 'No outcome-ready decision selected.';
      return;
    }
    const decision = document.createElement('div');
    const recommendation = document.createElement('div');
    const state = document.createElement('div');
    const note = document.createElement('div');
    decision.textContent = `decision=${item.decision} · id=${item.id}`;
    recommendation.textContent = `recommendation_id=${item.recommendation_id || '(none)'}`;
    state.textContent = `execution_status=${item.execution_status}`;
    note.textContent = `decision_note=${item.note || '(none)'}`;
    actionOutcomeCandidateDetail.append(decision, recommendation, state, note);
  }

  function renderActionOutcomeHistory(items) {
    actionOutcomeHistory.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      actionOutcomeHistory.textContent = 'No Outcome recorded for this person.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const outcome = document.createElement('div');
      const decision = document.createElement('div');
      const note = document.createElement('div');
      const created = document.createElement('div');
      outcome.textContent = `outcome=${item.outcome || '(unknown)'} · id=${item.id || '(none)'}`;
      decision.textContent = `decision_id=${item.decision_id || '(none)'}`;
      note.textContent = `note=${item.note || '(none)'}`;
      created.textContent = `created_at=${item.created_at || '(unknown)'}`;
      row.append(outcome, decision, note, created);
      actionOutcomeHistory.appendChild(row);
    });
  }

  async function loadActionOutcomeContext() {
    if (!selectedPersonId) throw new Error('Select a person first');
    actionOutcomeStatus.textContent = 'Loading executed decisions and Outcome history...';
    const executionContext = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/execution-context`
    );
    const outcomes = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/outcomes`
    );
    renderActionOutcomeCandidates(executionContext.decisions);
    renderActionOutcomeHistory(outcomes);
    actionOutcomeStatus.textContent = `${actionOutcomeCandidates.length} outcome-ready decision(s) · ${Array.isArray(outcomes) ? outcomes.length : 0} recorded Outcome(s). Nothing was created automatically.`;
  }

  async function recordActionOutcome() {
    if (!selectedPersonId) throw new Error('Select a person first');
    const decisionId = actionOutcomeSelect.value;
    const candidate = actionOutcomeCandidates.find((item) => item.id === decisionId);
    if (!candidate) throw new Error('Select an executed decision first');

    const outcome = byId('action-outcome-state').value;
    if (!['completed', 'skipped', 'failed'].includes(outcome)) {
      throw new Error('Outcome must be completed, skipped, or failed');
    }
    const payload = {outcome};
    const note = byId('action-outcome-note').value.trim();
    if (note) payload.note = note;

    actionOutcomeStatus.textContent = 'Recording explicit Outcome...';
    const created = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/outcomes/${encodeURIComponent(decisionId)}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    );
    byId('action-outcome-state').value = 'completed';
    byId('action-outcome-note').value = '';
    await loadActionOutcomeContext();
    actionOutcomeStatus.textContent = `Recorded Outcome ${created.id}. Feedback, Learning and Re-analysis will refresh automatically in the guided workflow.`;
    window.dispatchEvent(new CustomEvent('junshi:outcome-recorded', {
      detail: { decision_id: decisionId, outcome_id: created.id },
    }));
  }

  const baseResetWorkspaceForActionOutcome = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionOutcome(message);
    resetActionOutcomeWorkspace();
  };

  bind('load-action-outcome-context', loadActionOutcomeContext, actionOutcomeStatus);
  bind('record-action-outcome', recordActionOutcome, actionOutcomeStatus);

  actionOutcomeSelect.addEventListener('change', renderSelectedActionOutcomeCandidate);

  byId('person-select').addEventListener('change', () => {
    resetActionOutcomeWorkspace();
  });
'''
