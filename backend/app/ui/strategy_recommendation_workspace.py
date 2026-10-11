STRATEGY_RECOMMENDATION_HTML = r'''
  <fieldset id="strategy-recommendation" class="wide">
    <legend>Strategy & Recommendation</legend>
    <p class="note">TEST-139 只读取现有 Strategy / Recommendation context。结果属于 derived decision support，不是 canonical truth；不会自动选择、执行、发送消息或创建 Action Plan。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="strategy-workspace-heading">
        <h2 id="strategy-workspace-heading">Strategy Context</h2>
        <p class="note">需要先选择 Conversation。为避免无意触发 LLM/API 消耗，切换 Conversation 不会自动加载，必须显式点击。</p>
        <button id="load-strategy-context" class="requires-auth" type="button" disabled>Load strategy</button>
        <div id="strategy-context-status" class="status">Select a conversation first.</div>
        <div id="strategy-context-summary" class="status">No strategy loaded.</div>
        <div id="strategy-candidate-list" class="status">No strategy candidates loaded.</div>
        <div id="strategy-constraint-list" class="status">No strategy constraints loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="recommendation-workspace-heading">
        <h2 id="recommendation-workspace-heading">Recommendations</h2>
        <p class="note">Recommendation 必须保持 evidence-backed provenance，并继续遵守 must_not_auto_select / must_not_auto_execute。这里仅展示，不提供选择或执行按钮。</p>
        <button id="load-recommendation-context" class="requires-auth" type="button" disabled>Load recommendations</button>
        <div id="recommendation-context-status" class="status">Select a conversation first.</div>
        <div id="recommendation-list" class="status">No recommendations loaded.</div>
        <div id="recommendation-constraint-list" class="status">No recommendation constraints loaded.</div>
      </section>
    </div>
  </fieldset>
'''


STRATEGY_RECOMMENDATION_SCRIPT = r'''
  const strategyContextStatus = byId('strategy-context-status');
  const strategyContextSummary = byId('strategy-context-summary');
  const strategyCandidateList = byId('strategy-candidate-list');
  const strategyConstraintList = byId('strategy-constraint-list');
  const recommendationContextStatus = byId('recommendation-context-status');
  const recommendationList = byId('recommendation-list');
  const recommendationConstraintList = byId('recommendation-constraint-list');

  function resetStrategyRecommendation(message = 'Select a conversation first.') {
    strategyContextSummary.replaceChildren();
    strategyContextSummary.textContent = 'No strategy loaded.';
    strategyCandidateList.replaceChildren();
    strategyCandidateList.textContent = 'No strategy candidates loaded.';
    strategyConstraintList.replaceChildren();
    strategyConstraintList.textContent = 'No strategy constraints loaded.';
    recommendationList.replaceChildren();
    recommendationList.textContent = 'No recommendations loaded.';
    recommendationConstraintList.replaceChildren();
    recommendationConstraintList.textContent = 'No recommendation constraints loaded.';
    strategyContextStatus.textContent = message;
    recommendationContextStatus.textContent = message;
  }

  function appendConstraintRows(container, constraints) {
    container.replaceChildren();
    const entries = constraints && typeof constraints === 'object'
      ? Object.entries(constraints)
      : [];
    if (entries.length === 0) {
      container.textContent = 'No constraints returned.';
      return;
    }
    entries.forEach(([key, value]) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      row.textContent = `${key}: ${String(value)}`;
      container.appendChild(row);
    });
  }

  function renderStrategyContext(data) {
    strategyContextSummary.replaceChildren();
    const analysis = data && data.structured_analysis ? data.structured_analysis : {};
    const currentState = data && data.current_state ? data.current_state : {};
    const summary = document.createElement('div');
    const state = document.createElement('div');
    const decision = document.createElement('div');
    summary.textContent = `Analysis summary: ${analysis.summary || '(none)'}`;
    state.textContent = `Current state: ${currentState.status || '(unknown)'} / ${currentState.stage || '(unknown)'}`;
    const decisionInputs = data && data.decision_inputs ? data.decision_inputs : {};
    decision.textContent = `Selection status: ${decisionInputs.selection_status || '(unknown)'}`;
    strategyContextSummary.append(summary, state, decision);

    strategyCandidateList.replaceChildren();
    const candidates = data && Array.isArray(data.candidates) ? data.candidates : [];
    if (candidates.length === 0) {
      strategyCandidateList.textContent = 'No strategy candidates returned.';
    } else {
      candidates.forEach((candidate) => {
        const row = document.createElement('div');
        row.className = 'session-row';
        const title = document.createElement('div');
        const detail = document.createElement('div');
        title.textContent = candidate.recommendation || candidate.action || candidate.id || 'Strategy candidate';
        detail.textContent = `candidate_id=${candidate.id || '(none)'} · evidence=${(candidate.evidence_source_ids || []).join(', ') || '(none)'}`;
        row.append(title, detail);
        strategyCandidateList.appendChild(row);
      });
    }
    appendConstraintRows(strategyConstraintList, data ? data.strategy_constraints : null);
  }

  function renderRecommendationContext(data) {
    recommendationList.replaceChildren();
    const items = data && Array.isArray(data.recommendations) ? data.recommendations : [];
    if (items.length === 0) {
      recommendationList.textContent = 'No evidence-backed recommendations returned.';
    } else {
      items.forEach((item) => {
        const row = document.createElement('div');
        row.className = 'session-row';
        const title = document.createElement('div');
        const evidence = document.createElement('div');
        const action = document.createElement('div');
        const reply = document.createElement('div');
        const provenance = document.createElement('div');
        title.textContent = item.recommendation;
        evidence.textContent = `Evidence: ${(item.evidence_source_ids || []).join(', ') || '(none)'}`;
        action.textContent = `Action: ${item.action || '(none)'} · priority: ${item.priority || '(none)'} · horizon: ${item.time_horizon || '(none)'}`;
        reply.textContent = `Reply: ${item.reply || '(none)'}`;
        provenance.textContent = `Provenance: ${item.provenance && item.provenance.source ? item.provenance.source : '(unspecified)'}`;
        row.append(title, evidence, action, reply, provenance);
        recommendationList.appendChild(row);
      });
    }
    appendConstraintRows(
      recommendationConstraintList,
      data ? data.recommendation_constraints : null,
    );
  }

  async function loadStrategyContext() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    strategyContextStatus.textContent = 'Loading strategy context...';
    const data = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/strategy/context`
    );
    renderStrategyContext(data);
    strategyContextStatus.textContent = 'Strategy context loaded. No candidate was auto-selected.';
  }

  async function loadRecommendationContext() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    recommendationContextStatus.textContent = 'Loading recommendation context...';
    const data = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/recommendation/context`
    );
    renderRecommendationContext(data);
    const count = Array.isArray(data.recommendations) ? data.recommendations.length : 0;
    recommendationContextStatus.textContent = `${count} evidence-backed recommendation(s) loaded. Nothing was auto-selected or executed.`;
  }

  const baseResetWorkspaceForStrategyRecommendation = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForStrategyRecommendation(message);
    resetStrategyRecommendation();
  };

  bind('load-strategy-context', loadStrategyContext, strategyContextStatus);
  bind('load-recommendation-context', loadRecommendationContext, recommendationContextStatus);

  byId('conversation-select').addEventListener('change', () => {
    resetStrategyRecommendation(
      selectedConversationId
        ? 'Conversation changed. Load explicitly when you want to call the analysis pipeline.'
        : 'Select a conversation first.'
    );
  });

  byId('person-select').addEventListener('change', () => {
    resetStrategyRecommendation();
  });
'''
