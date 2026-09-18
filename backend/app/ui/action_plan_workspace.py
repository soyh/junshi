ACTION_PLAN_HTML = r'''
  <fieldset id="action-plan-workspace" class="wide">
    <legend>Action Plan</legend>
    <p class="note">TEST-140 区分“显式生成并持久化”与“只读查看已保存 Action Plan”。Conversation 级 generation 会运行现有 analysis → recommendation → action-plan orchestration，并可能写入 action_plan_snapshots；只有点击 Generate & save 时才调用。生成结果仍是 proposed，必须等待后续显式 user decision，绝不自动确认或执行。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-plan-generate-heading">
        <h2 id="action-plan-generate-heading">Generate from Conversation</h2>
        <p class="note">需要先选择 Conversation。这个动作可能调用 LLM/provider 并持久化 evidence-backed Action Plan snapshot，因此不会在登录、Person/Conversation 切换或 Recommendation 加载时自动执行。</p>
        <button id="generate-action-plan" class="requires-auth" type="button" disabled>Generate &amp; save action plan</button>
        <div id="action-plan-generate-status" class="status">Select a conversation first.</div>
        <div id="generated-action-plan-summary" class="status">No action plan generated.</div>
        <div id="generated-action-plan-list" class="status">No generated actions.</div>
        <div id="generated-action-plan-constraints" class="status">No action constraints loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="saved-action-plan-heading">
        <h2 id="saved-action-plan-heading">Saved Action Plans</h2>
        <p class="note">只读读取当前 Person 已持久化且仍被当前 canonical evidence 支持的 Action Plan。这里不创建 Action Decision，不提供 Confirm/Reject，也不调用 Execution。</p>
        <button id="load-saved-action-plan" class="requires-auth" type="button" disabled>Refresh saved plans</button>
        <div id="saved-action-plan-status" class="status">Select a person first.</div>
        <div id="saved-action-plan-list" class="status">No saved action plans loaded.</div>
        <div id="saved-action-plan-constraints" class="status">No action constraints loaded.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_PLAN_SCRIPT = r'''
  const actionPlanGenerateStatus = byId('action-plan-generate-status');
  const generatedActionPlanSummary = byId('generated-action-plan-summary');
  const generatedActionPlanList = byId('generated-action-plan-list');
  const generatedActionPlanConstraints = byId('generated-action-plan-constraints');
  const savedActionPlanStatus = byId('saved-action-plan-status');
  const savedActionPlanList = byId('saved-action-plan-list');
  const savedActionPlanConstraints = byId('saved-action-plan-constraints');

  function resetActionPlanWorkspace() {
    generatedActionPlanSummary.replaceChildren();
    generatedActionPlanSummary.textContent = 'No action plan generated.';
    generatedActionPlanList.replaceChildren();
    generatedActionPlanList.textContent = 'No generated actions.';
    generatedActionPlanConstraints.replaceChildren();
    generatedActionPlanConstraints.textContent = 'No action constraints loaded.';
    savedActionPlanList.replaceChildren();
    savedActionPlanList.textContent = 'No saved action plans loaded.';
    savedActionPlanConstraints.replaceChildren();
    savedActionPlanConstraints.textContent = 'No action constraints loaded.';
    actionPlanGenerateStatus.textContent = selectedConversationId
      ? 'Generation is explicit. Click Generate & save when you intend to persist a proposed Action Plan.'
      : 'Select a conversation first.';
    savedActionPlanStatus.textContent = selectedPersonId
      ? 'Click Refresh saved plans to read current persisted proposals.'
      : 'Select a person first.';
  }

  function renderActionPlanConstraintRows(container, constraints) {
    container.replaceChildren();
    const entries = constraints && typeof constraints === 'object'
      ? Object.entries(constraints)
      : [];
    if (entries.length === 0) {
      container.textContent = 'No action constraints returned.';
      return;
    }
    entries.forEach(([key, value]) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      row.textContent = `${key}: ${String(value)}`;
      container.appendChild(row);
    });
  }

  function renderActionPlanItems(container, items, emptyMessage) {
    container.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      container.textContent = emptyMessage;
      return;
    }
    items.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const action = document.createElement('div');
      const state = document.createElement('div');
      const evidence = document.createElement('div');
      const timing = document.createElement('div');
      action.textContent = item.action || '(no action text)';
      state.textContent = `recommendation_id=${item.recommendation_id || '(none)'} · status=${item.status || '(unknown)'} · requires_user_confirmation=${String(item.requires_user_confirmation === true)}`;
      evidence.textContent = `Evidence: ${(item.evidence_source_ids || []).join(', ') || '(none)'}`;
      timing.textContent = `priority=${item.priority || '(none)'} · horizon=${item.time_horizon || '(none)'}`;
      row.append(action, state, evidence, timing);
      container.appendChild(row);
    });
  }

  function renderGeneratedActionPlan(data) {
    generatedActionPlanSummary.replaceChildren();
    const summary = document.createElement('div');
    const recommendationCount = document.createElement('div');
    const sourceBacked = document.createElement('div');
    const analysis = data && data.structured_analysis ? data.structured_analysis : {};
    const inputs = data && data.action_plan_inputs ? data.action_plan_inputs : {};
    const recommendations = data && Array.isArray(data.recommendations) ? data.recommendations : [];
    summary.textContent = `Analysis summary: ${analysis.summary || inputs.summary || '(none)'}`;
    recommendationCount.textContent = `Recommendation inputs: ${recommendations.length}`;
    sourceBacked.textContent = `Recommendations source-backed: ${String(inputs.recommendations_are_source_backed === true)}`;
    generatedActionPlanSummary.append(summary, recommendationCount, sourceBacked);
    renderActionPlanItems(
      generatedActionPlanList,
      data ? data.action_plan : null,
      'No evidence-backed action was promoted to an Action Plan.',
    );
    renderActionPlanConstraintRows(
      generatedActionPlanConstraints,
      data ? data.action_constraints : null,
    );
  }

  function renderSavedActionPlan(data) {
    renderActionPlanItems(
      savedActionPlanList,
      data ? data.action_plan : null,
      'No persisted Action Plan is currently supported by canonical evidence.',
    );
    renderActionPlanConstraintRows(
      savedActionPlanConstraints,
      data ? data.action_constraints : null,
    );
  }

  async function generateActionPlan() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    actionPlanGenerateStatus.textContent = 'Generating evidence-backed Action Plan and saving eligible proposals...';
    const data = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/action-plan/context`
    );
    renderGeneratedActionPlan(data);
    const count = Array.isArray(data.action_plan) ? data.action_plan.length : 0;
    actionPlanGenerateStatus.textContent = `${count} proposed action(s) generated. User confirmation is still required; nothing was confirmed or executed.`;
  }

  async function loadSavedActionPlan() {
    if (!selectedPersonId) throw new Error('Select a person first');
    savedActionPlanStatus.textContent = 'Loading persisted Action Plan proposals...';
    const data = await api(
      `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/context`
    );
    renderSavedActionPlan(data);
    const count = Array.isArray(data.action_plan) ? data.action_plan.length : 0;
    savedActionPlanStatus.textContent = `${count} saved proposal(s) loaded. This read did not create a user decision or execute an action.`;
  }

  const baseResetWorkspaceForActionPlan = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionPlan(message);
    resetActionPlanWorkspace();
  };

  bind('generate-action-plan', generateActionPlan, actionPlanGenerateStatus);
  bind('load-saved-action-plan', loadSavedActionPlan, savedActionPlanStatus);

  byId('conversation-select').addEventListener('change', () => {
    resetActionPlanWorkspace();
  });

  byId('person-select').addEventListener('change', () => {
    resetActionPlanWorkspace();
  });
'''
