ACTION_REANALYSIS_HTML = r'''
  <fieldset id="action-reanalysis-workspace" class="wide">
    <legend>Re-analysis</legend>
    <p class="note">TEST-146 复用现有 canonical AnalysisContext → StructuredAnalysis → StrategyRecommendationCandidate → Recommendation 链。读取 inputs 不调用 LLM；只有显式 Run re-analysis 才会调用当前用户配置的 provider。结果属于 derived decision support，不是 canonical truth，也不会自动选择、创建 Action Plan、执行、发送消息或修改 Relationship。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-reanalysis-input-heading">
        <h2 id="action-reanalysis-input-heading">Re-analysis Inputs</h2>
        <p class="note">Load re-analysis inputs 只读取当前 Conversation 的 deterministic AnalysisContext，并展示其中 source-backed Learning Strategy。该步骤明确 must_not_call_llm；缺少 Outcome 的 learning item 继续保持 outcome_unknown，不会伪装成 observed success。</p>
        <button id="load-action-reanalysis-inputs" class="requires-auth" type="button" disabled>Load re-analysis inputs</button>
        <div id="action-reanalysis-input-status" class="status">Select a conversation, then load re-analysis inputs.</div>
        <div id="action-reanalysis-learning" class="status">No re-analysis inputs loaded.</div>
        <div id="action-reanalysis-constraints" class="status">No learning constraints loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-reanalysis-run-heading">
        <h2 id="action-reanalysis-run-heading">Fresh Analysis & Recommendations</h2>
        <p class="note">Run re-analysis 是独立显式动作，可能调用 LLM/provider。它不会自动发生在 Outcome、Feedback、Learning load 或 memory persist 之后。</p>
        <button id="run-action-reanalysis" class="requires-auth" type="button" disabled>Run re-analysis</button>
        <div id="action-reanalysis-run-status" class="status">Select a conversation before running re-analysis.</div>
        <div id="action-reanalysis-analysis" class="status">No fresh Structured Analysis loaded.</div>
        <div id="action-reanalysis-recommendations" class="status">No fresh recommendations loaded.</div>
        <div id="action-reanalysis-recommendation-constraints" class="status">No recommendation constraints loaded.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_REANALYSIS_SCRIPT = r'''
  const actionReanalysisInputStatus = byId('action-reanalysis-input-status');
  const actionReanalysisLearning = byId('action-reanalysis-learning');
  const actionReanalysisConstraints = byId('action-reanalysis-constraints');
  const actionReanalysisRunStatus = byId('action-reanalysis-run-status');
  const actionReanalysisAnalysis = byId('action-reanalysis-analysis');
  const actionReanalysisRecommendations = byId('action-reanalysis-recommendations');
  const actionReanalysisRecommendationConstraints = byId('action-reanalysis-recommendation-constraints');

  function resetActionReanalysisWorkspace() {
    actionReanalysisLearning.replaceChildren();
    actionReanalysisLearning.textContent = 'No re-analysis inputs loaded.';
    actionReanalysisConstraints.replaceChildren();
    actionReanalysisConstraints.textContent = 'No learning constraints loaded.';
    actionReanalysisAnalysis.replaceChildren();
    actionReanalysisAnalysis.textContent = 'No fresh Structured Analysis loaded.';
    actionReanalysisRecommendations.replaceChildren();
    actionReanalysisRecommendations.textContent = 'No fresh recommendations loaded.';
    actionReanalysisRecommendationConstraints.replaceChildren();
    actionReanalysisRecommendationConstraints.textContent = 'No recommendation constraints loaded.';
    actionReanalysisInputStatus.textContent = selectedConversationId
      ? 'Click Load re-analysis inputs to inspect deterministic source-backed learning context. No LLM call will be made.'
      : 'Select a conversation, then load re-analysis inputs.';
    actionReanalysisRunStatus.textContent = selectedConversationId
      ? 'Run re-analysis only when you explicitly want a fresh provider/LLM analysis.'
      : 'Select a conversation before running re-analysis.';
  }

  function appendReanalysisField(parent, label, value) {
    const line = document.createElement('div');
    line.textContent = `${label}=${value === null || value === undefined || value === '' ? '(none)' : value}`;
    parent.appendChild(line);
  }

  function renderReanalysisConstraints(container, constraints) {
    container.replaceChildren();
    const entries = constraints && typeof constraints === 'object' ? Object.entries(constraints) : [];
    if (entries.length === 0) {
      container.textContent = 'No constraints returned.';
      return;
    }
    entries.forEach(([key, value]) => {
      appendReanalysisField(container, key, String(value));
    });
  }

  function renderReanalysisInputs(body) {
    actionReanalysisLearning.replaceChildren();
    const learning = body && body.learning_strategy ? body.learning_strategy : {};
    const inputs = learning.learning_inputs || {};
    const feedback = Array.isArray(inputs.action_feedback) ? inputs.action_feedback : [];
    const memoryUpdates = Array.isArray(inputs.memory_updates) ? inputs.memory_updates : [];
    const strategyDecision = inputs.strategy_decision || {};
    const decisionItems = Array.isArray(strategyDecision.items) ? strategyDecision.items : [];

    appendReanalysisField(actionReanalysisLearning, 'conversation_id', body && body.conversation && body.conversation.id);
    appendReanalysisField(actionReanalysisLearning, 'person_id', body && body.person && body.person.id);
    appendReanalysisField(actionReanalysisLearning, 'feedback_learning_count', feedback.length);
    appendReanalysisField(actionReanalysisLearning, 'memory_learning_update_count', memoryUpdates.length);
    appendReanalysisField(actionReanalysisLearning, 'strategy_decision_learning_count', decisionItems.length);

    feedback.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      appendReanalysisField(row, 'recommendation_id', item.recommendation_id);
      appendReanalysisField(row, 'learning_status', item.learning_status);
      appendReanalysisField(row, 'observed_outcome_count', item.observed_outcome_count);
      appendReanalysisField(row, 'outcome_unknown_count', item.outcome_unknown_count);
      appendReanalysisField(row, 'unknowns', Array.isArray(item.unknowns) ? item.unknowns.join(', ') : 'unknown');
      const source = item.source || {};
      appendReanalysisField(row, 'source_observed_outcomes', source.observed_outcomes);
      appendReanalysisField(row, 'source_unknown_outcomes', source.unknown_outcomes);
      actionReanalysisLearning.appendChild(row);
    });

    renderReanalysisConstraints(actionReanalysisConstraints, learning.strategy_constraints);
  }

  function renderFreshReanalysis(body) {
    actionReanalysisAnalysis.replaceChildren();
    const analysis = body && body.structured_analysis ? body.structured_analysis : {};
    appendReanalysisField(actionReanalysisAnalysis, 'summary', analysis.summary);
    appendReanalysisField(actionReanalysisAnalysis, 'observed_facts', Array.isArray(analysis.observed_facts) ? analysis.observed_facts.length : 0);
    appendReanalysisField(actionReanalysisAnalysis, 'inferences', Array.isArray(analysis.inferences) ? analysis.inferences.length : 0);
    appendReanalysisField(actionReanalysisAnalysis, 'unknowns', Array.isArray(analysis.unknowns) ? analysis.unknowns.length : 0);
    appendReanalysisField(actionReanalysisAnalysis, 'hypotheses', Array.isArray(analysis.hypotheses) ? analysis.hypotheses.length : 0);

    actionReanalysisRecommendations.replaceChildren();
    const recommendations = body && Array.isArray(body.recommendations) ? body.recommendations : [];
    if (recommendations.length === 0) {
      actionReanalysisRecommendations.textContent = 'No fresh recommendation returned.';
    } else {
      recommendations.forEach((item) => {
        const row = document.createElement('div');
        row.className = 'session-row';
        appendReanalysisField(row, 'recommendation', item.recommendation);
        appendReanalysisField(row, 'evidence_source_ids', Array.isArray(item.evidence_source_ids) ? item.evidence_source_ids.join(', ') : '(none)');
        appendReanalysisField(row, 'action', item.action);
        appendReanalysisField(row, 'reply', item.reply);
        appendReanalysisField(row, 'provenance', item.provenance && item.provenance.source);
        actionReanalysisRecommendations.appendChild(row);
      });
    }
    renderReanalysisConstraints(
      actionReanalysisRecommendationConstraints,
      body ? body.recommendation_constraints : null,
    );
  }

  async function loadActionReanalysisInputs() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    actionReanalysisInputStatus.textContent = 'Loading deterministic re-analysis inputs without LLM...';
    const body = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/analysis/context`
    );
    renderReanalysisInputs(body);
    const learning = body && body.learning_strategy ? body.learning_strategy : {};
    const inputs = learning.learning_inputs || {};
    const feedbackCount = Array.isArray(inputs.action_feedback) ? inputs.action_feedback.length : 0;
    actionReanalysisInputStatus.textContent = `${feedbackCount} source-backed feedback learning item(s) loaded. Unknown Outcome remains unknown. No LLM/provider call was made.`;
  }

  async function runActionReanalysis() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    actionReanalysisRunStatus.textContent = 'Running explicit fresh Re-analysis through the configured provider/LLM...';
    const body = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/recommendation/context`
    );
    renderFreshReanalysis(body);
    const count = body && Array.isArray(body.recommendations) ? body.recommendations.length : 0;
    actionReanalysisRunStatus.textContent = `Fresh derived analysis completed with ${count} recommendation(s). Nothing was auto-selected, planned, executed, sent, or applied to Relationship.`;
  }

  const baseResetWorkspaceForActionReanalysis = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionReanalysis(message);
    resetActionReanalysisWorkspace();
  };

  bind('load-action-reanalysis-inputs', loadActionReanalysisInputs, actionReanalysisInputStatus);
  bind('run-action-reanalysis', runActionReanalysis, actionReanalysisRunStatus);

  byId('conversation-select').addEventListener('change', () => {
    resetActionReanalysisWorkspace();
  });

  byId('person-select').addEventListener('change', () => {
    resetActionReanalysisWorkspace();
  });
'''
