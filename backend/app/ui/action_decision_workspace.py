ACTION_DECISION_HTML = r'''
  <fieldset id="action-decision-workspace" class="wide">
    <legend>Action Decision</legend>
    <p class="note">TEST-141 只把现有 Action Decision canonical contract 接入统一 /app。先显式加载当前 Person 的 decision context，再对仍为 proposed 且 requires_user_confirmation=true 的 Action Plan proposal 做 Confirm / Reject。记录 confirmed 只表示用户明确决定，不会自动执行、发送消息、创建 Outcome 或修改 Relationship。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-decision-heading">
        <h2 id="action-decision-heading">Explicit User Decision</h2>
        <p class="note">Action Plan 可能在加载后发生变化；服务端会在 POST 时再次校验 proposal 是否仍可用，因此客户端选择不是 authority。</p>
        <button id="load-action-decision-context" class="requires-auth" type="button" disabled>Load decision context</button>
        <label for="action-decision-recommendation">Proposed action</label>
        <select id="action-decision-recommendation" disabled>
          <option value="">Load context first</option>
        </select>
        <div id="action-decision-candidate-detail" class="status">No proposal selected.</div>
        <label for="action-decision-note">Decision note (optional)</label>
        <textarea id="action-decision-note" class="requires-auth" disabled></textarea>
        <button id="confirm-action-decision" type="button" disabled>Confirm selected proposal</button>
        <button id="reject-action-decision" type="button" disabled>Reject selected proposal</button>
        <div id="action-decision-status" class="status">Select a person, then load decision context.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-decision-history-heading">
        <h2 id="action-decision-history-heading">Decision History</h2>
        <p class="note">History 来自 canonical action_decisions，按 created_at DESC / id DESC。这里不提供 Execution 控件。</p>
        <div id="action-decision-constraints" class="status">No decision constraints loaded.</div>
        <div id="action-decision-history" class="status">No decision history loaded.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_DECISION_SCRIPT = r'''
  const actionDecisionStatus = byId('action-decision-status');
  const actionDecisionSelect = byId('action-decision-recommendation');
  const actionDecisionCandidateDetail = byId('action-decision-candidate-detail');
  const actionDecisionConstraints = byId('action-decision-constraints');
  const actionDecisionHistory = byId('action-decision-history');
  const confirmActionDecisionButton = byId('confirm-action-decision');
  const rejectActionDecisionButton = byId('reject-action-decision');
  let actionDecisionCandidates = [];

  function resetActionDecisionWorkspace() {
    actionDecisionCandidates = [];
    actionDecisionSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Load context first';
    actionDecisionSelect.appendChild(placeholder);
    actionDecisionSelect.disabled = true;
    confirmActionDecisionButton.disabled = true;
    rejectActionDecisionButton.disabled = true;
    byId('action-decision-note').value = '';
    actionDecisionCandidateDetail.replaceChildren();
    actionDecisionCandidateDetail.textContent = 'No proposal selected.';
    actionDecisionConstraints.replaceChildren();
    actionDecisionConstraints.textContent = 'No decision constraints loaded.';
    actionDecisionHistory.replaceChildren();
    actionDecisionHistory.textContent = 'No decision history loaded.';
    actionDecisionStatus.textContent = selectedPersonId
      ? 'Click Load decision context to read current proposed actions and decision history.'
      : 'Select a person, then load decision context.';
  }

  function renderActionDecisionConstraints(constraints) {
    actionDecisionConstraints.replaceChildren();
    const entries = constraints && typeof constraints === 'object'
      ? Object.entries(constraints)
      : [];
    if (entries.length === 0) {
      actionDecisionConstraints.textContent = 'No decision constraints returned.';
      return;
    }
    entries.forEach(([key, value]) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      row.textContent = `${key}: ${String(value)}`;
      actionDecisionConstraints.appendChild(row);
    });
  }

  function renderActionDecisionHistory(items) {
    actionDecisionHistory.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      actionDecisionHistory.textContent = 'No recorded Action Decisions for this person.';
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const decision = document.createElement('div');
      const recommendation = document.createElement('div');
      const note = document.createElement('div');
      const created = document.createElement('div');
      decision.textContent = `decision=${item.decision || '(unknown)'} · id=${item.id || '(none)'}`;
      recommendation.textContent = `recommendation_id=${item.recommendation_id || '(none)'}`;
      note.textContent = `note=${item.note || '(none)'}`;
      created.textContent = `created_at=${item.created_at || '(unknown)'}`;
      row.append(decision, recommendation, note, created);
      actionDecisionHistory.appendChild(row);
    });
  }

  function renderActionDecisionCandidates(items) {
    actionDecisionCandidates = Array.isArray(items)
      ? items.filter((item) => (
          item &&
          item.recommendation_id &&
          item.status === 'proposed' &&
          item.requires_user_confirmation === true
        ))
      : [];
    actionDecisionSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = actionDecisionCandidates.length
      ? 'Select a proposed action'
      : 'No available proposed actions';
    actionDecisionSelect.appendChild(placeholder);
    actionDecisionCandidates.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.recommendation_id;
      option.textContent = item.action || item.recommendation_id;
      actionDecisionSelect.appendChild(option);
    });
    actionDecisionSelect.disabled = actionDecisionCandidates.length === 0;
    confirmActionDecisionButton.disabled = true;
    rejectActionDecisionButton.disabled = true;
    actionDecisionCandidateDetail.textContent = actionDecisionCandidates.length
      ? `${actionDecisionCandidates.length} proposal(s) available. Select one to record an explicit decision.`
      : 'No currently available proposed Action Plan item requires confirmation.';
  }

  function renderSelectedActionDecisionCandidate() {
    const recommendationId = actionDecisionSelect.value;
    const item = actionDecisionCandidates.find(
      (candidate) => candidate.recommendation_id === recommendationId
    );
    const hasSelection = Boolean(item);
    confirmActionDecisionButton.disabled = !hasSelection;
    rejectActionDecisionButton.disabled = !hasSelection;
    actionDecisionCandidateDetail.replaceChildren();
    if (!item) {
      actionDecisionCandidateDetail.textContent = actionDecisionCandidates.length
        ? 'Select a proposed action.'
        : 'No proposal selected.';
      return;
    }
    const action = document.createElement('div');
    const state = document.createElement('div');
    const evidence = document.createElement('div');
    action.textContent = item.action || '(no action text)';
    state.textContent = `status=${item.status} · requires_user_confirmation=${String(item.requires_user_confirmation === true)}`;
    evidence.textContent = `Evidence: ${(item.evidence_source_ids || []).join(', ') || '(none)'}`;
    actionDecisionCandidateDetail.append(action, state, evidence);
  }

  async function loadActionDecisionContext() {
    if (!selectedPersonId) throw new Error('Select a person first');
    actionDecisionStatus.textContent = 'Loading current Action Decision context...';
    const data = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/decisions/context`
    );
    renderActionDecisionCandidates(data.action_plan);
    renderActionDecisionConstraints(data.action_constraints);
    renderActionDecisionHistory(data.decisions);
    const proposalCount = Array.isArray(data.action_plan)
      ? data.action_plan.filter((item) => item && item.status === 'proposed' && item.requires_user_confirmation === true).length
      : 0;
    const decisionCount = Array.isArray(data.decisions) ? data.decisions.length : 0;
    actionDecisionStatus.textContent = `${proposalCount} proposal(s) available · ${decisionCount} recorded decision(s). Nothing was executed.`;
  }

  async function submitActionDecision(decision) {
    if (!selectedPersonId) throw new Error('Select a person first');
    const recommendationId = actionDecisionSelect.value;
    if (!recommendationId) throw new Error('Select a proposed action first');
    if (decision !== 'confirmed' && decision !== 'rejected') {
      throw new Error('Unsupported action decision');
    }
    const note = byId('action-decision-note').value.trim();
    actionDecisionStatus.textContent = `Recording ${decision} decision...`;
    const payload = {
      recommendation_id: recommendationId,
      decision,
    };
    if (note) payload.note = note;
    const created = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/decisions`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    );
    byId('action-decision-note').value = '';
    await loadActionDecisionContext();
    actionDecisionStatus.textContent = `Recorded ${created.decision} Action Decision ${created.id}. No execution was started.`;
    window.dispatchEvent(new CustomEvent('junshi:decision-recorded', {
      detail: { decision: created.decision, decision_id: created.id },
    }));
  }

  const baseResetWorkspaceForActionDecision = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionDecision(message);
    resetActionDecisionWorkspace();
  };

  bind('load-action-decision-context', loadActionDecisionContext, actionDecisionStatus);
  bind('confirm-action-decision', () => submitActionDecision('confirmed'), actionDecisionStatus);
  bind('reject-action-decision', () => submitActionDecision('rejected'), actionDecisionStatus);

  actionDecisionSelect.addEventListener('change', renderSelectedActionDecisionCandidate);

  byId('person-select').addEventListener('change', () => {
    resetActionDecisionWorkspace();
  });
'''
