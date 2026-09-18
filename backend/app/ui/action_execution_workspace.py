ACTION_EXECUTION_HTML = r'''
  <fieldset id="action-execution-workspace" class="wide">
    <legend>Action Execution</legend>
    <p class="note">TEST-142 只把现有 Action Execution canonical contract 接入统一 /app。confirmed Action Decision 本身不会执行；先显式加载当前 Person 的 execution context，只对 execution_status=execution_ready 的 confirmed decision 提供单独的 Record execution 动作。记录 Execution 不会发送消息、自动创建 Outcome 或修改 Relationship。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-execution-heading">
        <h2 id="action-execution-heading">Explicit Execution Record</h2>
        <p class="note">客户端只展示当前 execution_ready 候选；服务端在 POST 时仍会重新校验 confirmed、scope、重复 execution 与 existing Outcome，因此客户端选择不是 authority。</p>
        <button id="load-action-execution-context" class="requires-auth" type="button" disabled>Load execution context</button>
        <label for="action-execution-decision">Execution-ready decision</label>
        <select id="action-execution-decision" disabled>
          <option value="">Load context first</option>
        </select>
        <div id="action-execution-candidate-detail" class="status">No execution-ready decision selected.</div>
        <label for="action-execution-executed-at">Executed at (optional)</label>
        <input id="action-execution-executed-at" class="requires-auth" type="datetime-local" disabled>
        <label for="action-execution-note">Execution note (optional)</label>
        <textarea id="action-execution-note" class="requires-auth" disabled></textarea>
        <button id="record-action-execution" type="button" disabled>Record selected execution</button>
        <div id="action-execution-status" class="status">Select a person, then load execution context.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-execution-history-heading">
        <h2 id="action-execution-history-heading">Decision Execution Status</h2>
        <p class="note">这里读取 canonical execution context，并展示每个 Action Decision 的 execution_status。Outcome 仍由后续独立阶段处理。</p>
        <div id="action-execution-constraints" class="status">No execution constraints loaded.</div>
        <div id="action-execution-decisions" class="status">No decision execution status loaded.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_EXECUTION_SCRIPT = r'''
  const actionExecutionStatus = byId('action-execution-status');
  const actionExecutionSelect = byId('action-execution-decision');
  const actionExecutionCandidateDetail = byId('action-execution-candidate-detail');
  const actionExecutionConstraints = byId('action-execution-constraints');
  const actionExecutionDecisions = byId('action-execution-decisions');
  const recordActionExecutionButton = byId('record-action-execution');
  let actionExecutionCandidates = [];

  function resetActionExecutionWorkspace() {
    actionExecutionCandidates = [];
    actionExecutionSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Load context first';
    actionExecutionSelect.appendChild(placeholder);
    actionExecutionSelect.disabled = true;
    recordActionExecutionButton.disabled = true;
    byId('action-execution-executed-at').value = '';
    byId('action-execution-note').value = '';
    actionExecutionCandidateDetail.replaceChildren();
    actionExecutionCandidateDetail.textContent = 'No execution-ready decision selected.';
    actionExecutionConstraints.replaceChildren();
    actionExecutionConstraints.textContent = 'No execution constraints loaded.';
    actionExecutionDecisions.replaceChildren();
    actionExecutionDecisions.textContent = 'No decision execution status loaded.';
    actionExecutionStatus.textContent = selectedPersonId
      ? 'Click Load execution context to read current Action Decision execution status.'
      : 'Select a person, then load execution context.';
  }

  function renderActionExecutionConstraints(constraints) {
    actionExecutionConstraints.replaceChildren();
    const entries = constraints && typeof constraints === 'object'
      ? Object.entries(constraints)
      : [];
    if (entries.length === 0) {
      actionExecutionConstraints.textContent = 'No execution constraints returned.';
      return;
    }
    entries.forEach(([key, value]) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      row.textContent = `${key}: ${String(value)}`;
      actionExecutionConstraints.appendChild(row);
    });
  }

  function renderActionExecutionDecisions(items) {
    actionExecutionDecisions.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      actionExecutionDecisions.textContent = 'No recorded Action Decisions for this person.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const decision = document.createElement('div');
      const recommendation = document.createElement('div');
      const executionState = document.createElement('div');
      const created = document.createElement('div');
      decision.textContent = `decision=${item.decision || '(unknown)'} · id=${item.id || '(none)'}`;
      recommendation.textContent = `recommendation_id=${item.recommendation_id || '(none)'}`;
      executionState.textContent = `execution_status=${item.execution_status || '(unknown)'}`;
      created.textContent = `created_at=${item.created_at || '(unknown)'}`;
      row.append(decision, recommendation, executionState, created);
      actionExecutionDecisions.appendChild(row);
    });
  }

  function renderActionExecutionCandidates(items) {
    actionExecutionCandidates = Array.isArray(items)
      ? items.filter((item) => (
          item &&
          item.id &&
          item.decision === 'confirmed' &&
          item.execution_status === 'execution_ready'
        ))
      : [];
    actionExecutionSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = actionExecutionCandidates.length
      ? 'Select an execution-ready decision'
      : 'No execution-ready decisions';
    actionExecutionSelect.appendChild(placeholder);
    actionExecutionCandidates.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = `${item.recommendation_id || '(no recommendation)'} · ${item.id}`;
      actionExecutionSelect.appendChild(option);
    });
    actionExecutionSelect.disabled = actionExecutionCandidates.length === 0;
    recordActionExecutionButton.disabled = true;
    actionExecutionCandidateDetail.textContent = actionExecutionCandidates.length
      ? `${actionExecutionCandidates.length} confirmed decision(s) ready for explicit execution recording.`
      : 'No confirmed Action Decision is currently execution_ready.';
  }

  function renderSelectedActionExecutionCandidate() {
    const decisionId = actionExecutionSelect.value;
    const item = actionExecutionCandidates.find((candidate) => candidate.id === decisionId);
    recordActionExecutionButton.disabled = !item;
    actionExecutionCandidateDetail.replaceChildren();
    if (!item) {
      actionExecutionCandidateDetail.textContent = actionExecutionCandidates.length
        ? 'Select an execution-ready decision.'
        : 'No execution-ready decision selected.';
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
    actionExecutionCandidateDetail.append(decision, recommendation, state, note);
  }

  async function loadActionExecutionContext() {
    if (!selectedPersonId) throw new Error('Select a person first');
    actionExecutionStatus.textContent = 'Loading current Action Execution context...';
    const data = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/execution-context`
    );
    renderActionExecutionCandidates(data.decisions);
    renderActionExecutionConstraints(data.execution_constraints);
    renderActionExecutionDecisions(data.decisions);
    const readyCount = Array.isArray(data.decisions)
      ? data.decisions.filter((item) => item && item.decision === 'confirmed' && item.execution_status === 'execution_ready').length
      : 0;
    const decisionCount = Array.isArray(data.decisions) ? data.decisions.length : 0;
    actionExecutionStatus.textContent = `${readyCount} execution-ready decision(s) · ${decisionCount} total decision(s). Nothing was executed automatically.`;
  }

  async function recordActionExecution() {
    if (!selectedPersonId) throw new Error('Select a person first');
    const decisionId = actionExecutionSelect.value;
    const candidate = actionExecutionCandidates.find((item) => item.id === decisionId);
    if (!candidate) throw new Error('Select an execution-ready decision first');

    const payload = {};
    const executedAt = byId('action-execution-executed-at').value;
    if (executedAt) {
      const parsed = new Date(executedAt);
      if (Number.isNaN(parsed.getTime())) throw new Error('Executed at is invalid');
      payload.executed_at = parsed.toISOString();
    }
    const note = byId('action-execution-note').value.trim();
    if (note) payload.note = note;

    actionExecutionStatus.textContent = 'Recording explicit Action Execution...';
    const created = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/executions/${encodeURIComponent(decisionId)}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    );
    byId('action-execution-executed-at').value = '';
    byId('action-execution-note').value = '';
    await loadActionExecutionContext();
    actionExecutionStatus.textContent = `Recorded Action Execution ${created.id}. No message was sent and no Outcome was created.`;
  }

  const baseResetWorkspaceForActionExecution = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionExecution(message);
    resetActionExecutionWorkspace();
  };

  bind('load-action-execution-context', loadActionExecutionContext, actionExecutionStatus);
  bind('record-action-execution', recordActionExecution, actionExecutionStatus);

  actionExecutionSelect.addEventListener('change', renderSelectedActionExecutionCandidate);

  byId('person-select').addEventListener('change', () => {
    resetActionExecutionWorkspace();
  });
'''
