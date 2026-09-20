STRATEGIC_REPLY_HTML = r'''
  <fieldset id="strategic-reply-workspace" class="wide">
    <legend>Strategic Reply</legend>
    <p class="note">选择 Conversation 后由你显式生成回复草稿。此操作会调用现有 AnalysisContext → StructuredAnalysis → Strategic Reply 链路；结果属于 derived decision support，不会自动发送、保存成 Message、创建 Action Plan、确认 Decision 或启动 Execution。</p>

    <div class="workspace-grid">
      <section class="workspace-card" aria-labelledby="strategic-reply-heading">
        <h2 id="strategic-reply-heading">Reply Draft</h2>
        <p class="note">切换 Person / Conversation 只会清空当前结果，不会自动调用 LLM/API。生成后可在本地编辑草稿并显式复制；编辑内容不会自动保存到数据库，也不会发送给任何人。</p>
        <button id="load-strategic-reply" class="requires-auth" type="button" disabled>Generate reply draft</button>
        <div id="strategic-reply-status" class="status">Select a conversation first.</div>
        <label for="strategic-reply-draft">Editable reply</label>
        <textarea id="strategic-reply-draft" class="requires-auth" disabled></textarea>
        <button id="copy-strategic-reply" class="requires-auth" type="button" disabled>Copy edited reply</button>
        <button id="restore-strategic-reply" class="requires-auth" type="button" disabled>Restore generated draft</button>
        <button id="prepare-strategic-reply-message" class="requires-auth" type="button" disabled>Prepare sent-message record</button>
        <p class="note">仅在你已经通过外部聊天工具实际发送后使用。此按钮只把当前编辑文本填入现有 Message 表单，不会保存 Message 或发送任何内容；请核对实际发送文本与 Sent at，再单独点击 Add message。</p>
      </section>

      <section class="workspace-card" aria-labelledby="strategic-reply-context-heading">
        <h2 id="strategic-reply-context-heading">Why this reply</h2>
        <div id="strategic-reply-context" class="status">No strategic reply context loaded.</div>
        <div id="strategic-reply-recommendations" class="status">No supporting recommendations loaded.</div>
        <div id="strategic-reply-constraints" class="status">No reply constraints loaded.</div>
        <div id="strategic-reply-learning" class="status">No learning strategy loaded.</div>
      </section>
    </div>
  </fieldset>
'''


STRATEGIC_REPLY_SCRIPT = r'''
  const strategicReplyStatus = byId('strategic-reply-status');
  const strategicReplyDraft = byId('strategic-reply-draft');
  const strategicReplyContext = byId('strategic-reply-context');
  const strategicReplyRecommendations = byId('strategic-reply-recommendations');
  const strategicReplyConstraints = byId('strategic-reply-constraints');
  const strategicReplyLearning = byId('strategic-reply-learning');
  let generatedStrategicReplyDraft = '';

  function resetStrategicReply(message = 'Select a conversation first.') {
    strategicReplyStatus.textContent = message;
    generatedStrategicReplyDraft = '';
    strategicReplyDraft.value = '';
    strategicReplyContext.replaceChildren();
    strategicReplyContext.textContent = 'No strategic reply context loaded.';
    strategicReplyRecommendations.replaceChildren();
    strategicReplyRecommendations.textContent = 'No supporting recommendations loaded.';
    strategicReplyConstraints.replaceChildren();
    strategicReplyConstraints.textContent = 'No reply constraints loaded.';
    strategicReplyLearning.replaceChildren();
    strategicReplyLearning.textContent = 'No learning strategy loaded.';
  }

  function appendStrategicReplyObject(container, value, emptyMessage) {
    container.replaceChildren();
    const entries = value && typeof value === 'object' && !Array.isArray(value)
      ? Object.entries(value)
      : [];
    if (entries.length === 0) {
      container.textContent = emptyMessage;
      return;
    }
    entries.forEach(([key, item]) => {
      const row = document.createElement('div');
      row.className = 'session-row';
      const rendered = item && typeof item === 'object' ? JSON.stringify(item) : String(item);
      row.textContent = `${key}: ${rendered}`;
      container.appendChild(row);
    });
  }

  function renderStrategicReply(data) {
    generatedStrategicReplyDraft = data && data.draft ? String(data.draft) : '';
    strategicReplyDraft.value = generatedStrategicReplyDraft;

    strategicReplyContext.replaceChildren();
    const analysis = data && data.structured_analysis ? data.structured_analysis : {};
    const state = data && data.current_state ? data.current_state : {};
    const summary = document.createElement('div');
    const stateRow = document.createElement('div');
    const evidenceRow = document.createElement('div');
    summary.textContent = `Analysis summary: ${analysis.summary || '(none)'}`;
    stateRow.textContent = `Current state: ${state.status || '(unknown)'} / ${state.stage || '(unknown)'}`;
    const evidence = data && Array.isArray(data.evidence) ? data.evidence : [];
    evidenceRow.textContent = `Evidence items: ${evidence.length}`;
    strategicReplyContext.append(summary, stateRow, evidenceRow);

    strategicReplyRecommendations.replaceChildren();
    const recommendations = data && Array.isArray(data.recommendations) ? data.recommendations : [];
    if (recommendations.length === 0) {
      strategicReplyRecommendations.textContent = 'No supporting recommendations returned.';
    } else {
      recommendations.forEach((item) => {
        const row = document.createElement('div');
        row.className = 'session-row';
        if (item && typeof item === 'object') {
          row.textContent = item.recommendation || item.reply || item.action || JSON.stringify(item);
        } else {
          row.textContent = String(item);
        }
        strategicReplyRecommendations.appendChild(row);
      });
    }

    appendStrategicReplyObject(
      strategicReplyConstraints,
      data ? data.reply_constraints : null,
      'No reply constraints returned.',
    );
    appendStrategicReplyObject(
      strategicReplyLearning,
      data ? data.learning_strategy : null,
      'No learning strategy returned.',
    );
  }

  async function loadStrategicReply() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    strategicReplyStatus.textContent = 'Generating strategic reply draft...';
    const data = await api(
      `/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/strategic-reply/context`
    );
    renderStrategicReply(data);
    strategicReplyStatus.textContent = 'Reply draft generated. Review or edit it before copying. Nothing was sent, saved as a message, confirmed, or executed.';
  }

  async function copyStrategicReply() {
    const draft = strategicReplyDraft.value;
    if (!draft.trim()) throw new Error('Generate or enter a reply draft before copying');
    if (!navigator.clipboard || typeof navigator.clipboard.writeText !== 'function') {
      throw new Error('Clipboard access is unavailable in this browser context; copy the editable draft manually.');
    }
    await navigator.clipboard.writeText(draft);
    strategicReplyStatus.textContent = 'Edited reply copied to clipboard. It was not saved or sent.';
  }

  function restoreStrategicReply() {
    if (!generatedStrategicReplyDraft) throw new Error('Generate a reply draft before restoring it');
    strategicReplyDraft.value = generatedStrategicReplyDraft;
    strategicReplyStatus.textContent = 'Generated draft restored locally. Nothing was saved or sent.';
  }

  function prepareStrategicReplyMessageRecord() {
    if (!selectedConversationId) throw new Error('Select a conversation first');
    const draft = strategicReplyDraft.value.trim();
    if (!draft) throw new Error('Generate or enter the actual sent reply before preparing a message record');
    byId('message-sender').value = 'user';
    byId('message-content').value = draft;
    byId('message-sent-at').value = '';
    byId('messages-status').textContent = 'Strategic Reply text prepared in the Message form only. Verify the exact text actually sent and Sent at, then click Add message. Nothing has been saved or sent yet.';
    byId('message-content').focus();
    strategicReplyStatus.textContent = 'Prepared the existing Message composer only. Add message remains a separate explicit action; nothing has been saved or sent.';
  }

  const baseResetWorkspaceForStrategicReply = resetWorkspace;
  resetWorkspace = function(message = 'Login to load persons.') {
    baseResetWorkspaceForStrategicReply(message);
    resetStrategicReply();
  };

  bind('load-strategic-reply', loadStrategicReply, strategicReplyStatus);
  bind('copy-strategic-reply', copyStrategicReply, strategicReplyStatus);
  bind('restore-strategic-reply', restoreStrategicReply, strategicReplyStatus);
  bind('prepare-strategic-reply-message', prepareStrategicReplyMessageRecord, strategicReplyStatus);

  strategicReplyDraft.addEventListener('input', () => {
    if (strategicReplyDraft.value !== generatedStrategicReplyDraft) {
      strategicReplyStatus.textContent = 'Draft edited locally. Changes are not saved or sent.';
    }
  });

  byId('conversation-select').addEventListener('change', () => {
    resetStrategicReply(
      selectedConversationId
        ? 'Conversation changed. Generate explicitly when you want to call the analysis pipeline.'
        : 'Select a conversation first.'
    );
  });

  byId('person-select').addEventListener('change', () => {
    resetStrategicReply();
  });
'''
