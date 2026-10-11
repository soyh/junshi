ACTION_FEEDBACK_HTML = r'''
  <fieldset id="action-feedback-workspace" class="wide">
    <legend>Feedback</legend>
    <p class="note">TEST-144 直接展示现有 canonical Action Feedback read model。Feedback 由 Action Decision 与可选 Outcome 确定性合成，不新增 Feedback 写入接口，不推断未知结果、关系影响或 recommendation quality，也不会触发 Learning / Re-analysis。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="action-feedback-context-heading">
        <h2 id="action-feedback-context-heading">Decision / Outcome Feedback</h2>
        <p class="note">只有显式点击 Load feedback 才读取当前 Person 的 canonical Feedback 视图。缺少 Outcome 时保持 outcome_unknown，而不是推断成功或失败。</p>
        <button id="load-action-feedback" class="requires-auth" type="button" disabled>Load feedback</button>
        <div id="action-feedback-status" class="status">Select a person, then load feedback.</div>
        <div id="action-feedback-items" class="status">No Feedback loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-feedback-summary-heading">
        <h2 id="action-feedback-summary-heading">Feedback Summary</h2>
        <div id="action-feedback-summary" class="status">No Feedback summary loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-feedback-trend-heading">
        <h2 id="action-feedback-trend-heading">Feedback Trend</h2>
        <div id="action-feedback-trend" class="status">No Feedback trend loaded.</div>
      </section>

      <section class="workspace-card" aria-labelledby="action-feedback-signals-heading">
        <h2 id="action-feedback-signals-heading">Recommendation Signals</h2>
        <p class="note">Signals 只按 recommendation identity 聚合已观察数据，不评价 recommendation quality。</p>
        <div id="action-feedback-signals" class="status">No Feedback signals loaded.</div>
      </section>
    </div>
  </fieldset>
'''


ACTION_FEEDBACK_SCRIPT = r'''
  const actionFeedbackStatus = byId('action-feedback-status');
  const actionFeedbackItems = byId('action-feedback-items');
  const actionFeedbackSummary = byId('action-feedback-summary');
  const actionFeedbackTrend = byId('action-feedback-trend');
  const actionFeedbackSignals = byId('action-feedback-signals');

  function resetActionFeedbackWorkspace() {
    actionFeedbackItems.replaceChildren();
    actionFeedbackItems.textContent = 'No Feedback loaded.';
    actionFeedbackSummary.replaceChildren();
    actionFeedbackSummary.textContent = 'No Feedback summary loaded.';
    actionFeedbackTrend.replaceChildren();
    actionFeedbackTrend.textContent = 'No Feedback trend loaded.';
    actionFeedbackSignals.replaceChildren();
    actionFeedbackSignals.textContent = 'No Feedback signals loaded.';
    actionFeedbackStatus.textContent = selectedPersonId
      ? 'Click Load feedback to read the canonical Decision / Outcome feedback views.'
      : 'Select a person, then load feedback.';
  }

  function appendFeedbackField(parent, label, value) {
    const line = document.createElement('div');
    line.textContent = `${label}=${value === null || value === undefined || value === '' ? '(none)' : value}`;
    parent.appendChild(line);
  }

  function renderActionFeedbackContext(body) {
    actionFeedbackItems.replaceChildren();
    const feedback = body && Array.isArray(body.feedback) ? body.feedback : [];
    const synthesis = body && Array.isArray(body.feedback_synthesis) ? body.feedback_synthesis : [];
    const synthesisByDecision = new Map(synthesis.map((item) => [item.decision_id, item]));

    if (feedback.length === 0) {
      actionFeedbackItems.textContent = 'No Action Decision feedback exists for this person.';
      return;
    }

    feedback.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      appendFeedbackField(row, 'decision', item.decision);
      appendFeedbackField(row, 'decision_id', item.decision_id);
      appendFeedbackField(row, 'recommendation_id', item.recommendation_id);
      appendFeedbackField(row, 'outcome', item.outcome || 'unknown');
      appendFeedbackField(row, 'outcome_id', item.outcome_id);
      const derived = synthesisByDecision.get(item.decision_id);
      appendFeedbackField(row, 'feedback_status', derived ? derived.feedback_status : 'unknown');
      appendFeedbackField(row, 'unknowns', derived && Array.isArray(derived.unknowns) ? derived.unknowns.join(', ') : 'unknown');
      actionFeedbackItems.appendChild(row);
    });
  }

  function renderActionFeedbackSummary(body) {
    actionFeedbackSummary.replaceChildren();
    const summary = body && body.summary ? body.summary : null;
    if (!summary) {
      actionFeedbackSummary.textContent = 'No Feedback summary available.';
      return;
    }
    appendFeedbackField(actionFeedbackSummary, 'total_decisions', summary.total_decisions);
    appendFeedbackField(actionFeedbackSummary, 'confirmed', summary.decision_counts && summary.decision_counts.confirmed);
    appendFeedbackField(actionFeedbackSummary, 'rejected', summary.decision_counts && summary.decision_counts.rejected);
    appendFeedbackField(actionFeedbackSummary, 'outcome_observed', summary.outcome_observed_count);
    appendFeedbackField(actionFeedbackSummary, 'outcome_unknown', summary.outcome_unknown_count);
    appendFeedbackField(actionFeedbackSummary, 'completed', summary.outcome_counts && summary.outcome_counts.completed);
    appendFeedbackField(actionFeedbackSummary, 'skipped', summary.outcome_counts && summary.outcome_counts.skipped);
    appendFeedbackField(actionFeedbackSummary, 'failed', summary.outcome_counts && summary.outcome_counts.failed);
  }

  function renderActionFeedbackTrend(body) {
    actionFeedbackTrend.replaceChildren();
    const observations = body && Array.isArray(body.observations) ? body.observations : [];
    if (observations.length === 0) {
      actionFeedbackTrend.textContent = 'No Feedback trend observations available.';
      return;
    }
    observations.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      appendFeedbackField(row, 'event_at', item.event_at);
      appendFeedbackField(row, 'feedback_status', item.feedback_status);
      appendFeedbackField(row, 'decision', item.decision);
      appendFeedbackField(row, 'decision_id', item.decision_id);
      appendFeedbackField(row, 'outcome', item.outcome);
      appendFeedbackField(row, 'outcome_id', item.outcome_id);
      actionFeedbackTrend.appendChild(row);
    });
  }

  function renderActionFeedbackSignals(body) {
    actionFeedbackSignals.replaceChildren();
    const signals = body && Array.isArray(body.signals) ? body.signals : [];
    if (signals.length === 0) {
      actionFeedbackSignals.textContent = 'No recommendation-linked Feedback signals available.';
      return;
    }
    signals.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      appendFeedbackField(row, 'recommendation_id', item.recommendation_id);
      appendFeedbackField(row, 'decision_count', item.decision_count);
      appendFeedbackField(row, 'outcome_observed', item.outcome_observed_count);
      appendFeedbackField(row, 'outcome_unknown', item.outcome_unknown_count);
      appendFeedbackField(row, 'completed', item.outcome_counts && item.outcome_counts.completed);
      appendFeedbackField(row, 'skipped', item.outcome_counts && item.outcome_counts.skipped);
      appendFeedbackField(row, 'failed', item.outcome_counts && item.outcome_counts.failed);
      actionFeedbackSignals.appendChild(row);
    });
  }

  async function loadActionFeedback() {
    if (!selectedPersonId) throw new Error('Select a person first');
    actionFeedbackStatus.textContent = 'Loading canonical Feedback views...';
    const personPath = `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/action-plan/feedback`;
    const [context, summary, trend, signals] = await Promise.all([
      api(`${personPath}/context`),
      api(`${personPath}/summary`),
      api(`${personPath}/trend`),
      api(`${personPath}/signals`),
    ]);
    renderActionFeedbackContext(context);
    renderActionFeedbackSummary(summary);
    renderActionFeedbackTrend(trend);
    renderActionFeedbackSignals(signals);
    const feedbackCount = Array.isArray(context.feedback) ? context.feedback.length : 0;
    const observedCount = summary && summary.summary ? summary.summary.outcome_observed_count : 0;
    const unknownCount = summary && summary.summary ? summary.summary.outcome_unknown_count : 0;
    actionFeedbackStatus.textContent = `${feedbackCount} decision feedback item(s) · ${observedCount} observed Outcome(s) · ${unknownCount} unknown Outcome(s). Read-only; no Learning or Re-analysis was started.`;
  }

  const baseResetWorkspaceForActionFeedback = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForActionFeedback(message);
    resetActionFeedbackWorkspace();
  };

  bind('load-action-feedback', loadActionFeedback, actionFeedbackStatus);

  byId('person-select').addEventListener('change', () => {
    resetActionFeedbackWorkspace();
  });
'''
