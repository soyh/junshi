STREAMLINED_LIFECYCLE_STYLE = r'''
    /* TEST-162: compact settings, one-primary-conversation UX, and bounded drawers. */
    #guided-settings-content {
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
      align-items: start !important;
      gap: 10px !important;
    }

    #guided-settings-content > fieldset {
      grid-column: auto !important;
      margin: 0 !important;
      align-self: start !important;
      min-width: 0 !important;
      padding: 12px !important;
    }

    #guided-settings-content #account-security {
      grid-column: 1 / -1 !important;
    }

    #guided-settings-content #account-security .workspace-grid {
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)) !important;
      align-items: start !important;
      gap: 10px !important;
    }

    .streamlined-setting-fields {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 8px 10px;
      margin-top: 6px;
    }

    .streamlined-setting-field label {
      margin-top: 0 !important;
    }

    .streamlined-setting-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 8px;
    }

    .streamlined-setting-actions button {
      margin: 0 !important;
    }

    .streamlined-hidden {
      display: none !important;
    }

    .streamlined-auto-status {
      margin: 0 0 10px !important;
      border: 1px solid rgba(25, 167, 232, .22);
      background: rgba(236, 249, 255, .86) !important;
    }

    .streamlined-primary-button {
      font-weight: 750;
    }

    .streamlined-review-details {
      margin-top: 12px;
      padding: 10px 12px;
      border: 1px dashed rgba(25, 167, 232, .28);
      border-radius: 12px;
    }

    .streamlined-review-details > summary {
      cursor: pointer;
      font-weight: 700;
    }

    /* A drawer must remain usable without expanding the whole page. */
    .user-long-content:not(.is-expanded) {
      max-height: 11rem !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      mask-image: none !important;
      padding-right: 6px;
      scrollbar-gutter: stable;
    }

    .user-long-content.is-expanded {
      max-height: min(68vh, 620px) !important;
      overflow-y: auto !important;
      overflow-x: hidden !important;
      mask-image: none !important;
      padding-right: 6px;
      scrollbar-gutter: stable;
    }

    .user-long-content::-webkit-scrollbar {
      width: 8px;
    }

    .user-long-content::-webkit-scrollbar-thumb {
      background: rgba(25, 167, 232, .34);
      border-radius: 999px;
    }

    @media (max-width: 760px) {
      #guided-settings-content {
        grid-template-columns: 1fr !important;
      }
      #guided-settings-content #account-security {
        grid-column: auto !important;
      }
    }
'''


STREAMLINED_LIFECYCLE_SCRIPT = r'''
  const streamlinedAutoStatus = document.createElement('div');
  streamlinedAutoStatus.id = 'streamlined-auto-status';
  streamlinedAutoStatus.className = 'status streamlined-auto-status';
  streamlinedAutoStatus.textContent = '更新主对话后，系统会自动刷新 AI 回复、行动计划和后续跟进状态。';

  const streamlinedReviewStatus = document.createElement('div');
  streamlinedReviewStatus.id = 'streamlined-review-status';
  streamlinedReviewStatus.className = 'status streamlined-auto-status';
  streamlinedReviewStatus.textContent = '记录真实行动结果后，系统会自动完成反馈、学习记忆和复盘。';

  let streamlinedEvidencePipelineRunning = false;
  let streamlinedOutcomePipelineRunning = false;
  let streamlinedLastObservedOutcomeStatus = '';
  let streamlinedLastObservedDecisionStatus = '';
  let streamlinedLastObservedExecutionStatus = '';

  function streamlinedHide(id) {
    const node = byId(id);
    if (node) node.classList.add('streamlined-hidden');
  }

  function streamlinedSetHeading(stepId, title, copy) {
    const step = byId(stepId);
    if (!step) return;
    const titleNode = step.querySelector('.guided-step-header h2');
    const copyNode = step.querySelector('.guided-step-header p');
    if (titleNode) titleNode.textContent = title;
    if (copyNode) copyNode.textContent = copy;
  }

  function streamlinedCompactFieldset(fieldsetId, fieldIds) {
    const fieldset = byId(fieldsetId);
    if (!fieldset || fieldset.querySelector(':scope > .streamlined-setting-fields')) return;
    const grid = document.createElement('div');
    grid.className = 'streamlined-setting-fields';
    let insertionPoint = null;
    fieldIds.forEach((id) => {
      const control = byId(id);
      const label = document.querySelector(`label[for="${id}"]`);
      if (!control || !label || control.closest('fieldset') !== fieldset) return;
      if (!insertionPoint) insertionPoint = label;
      const wrapper = document.createElement('div');
      wrapper.className = 'streamlined-setting-field';
      wrapper.append(label, control);
      grid.appendChild(wrapper);
    });
    if (insertionPoint && grid.children.length) fieldset.insertBefore(grid, insertionPoint);

    const actionButtons = Array.from(fieldset.querySelectorAll(':scope > button, :scope > div > button'));
    if (actionButtons.length) {
      const actions = document.createElement('div');
      actions.className = 'streamlined-setting-actions';
      actionButtons.forEach((button) => actions.appendChild(button));
      const status = fieldset.querySelector(':scope > .status');
      if (status) fieldset.insertBefore(actions, status);
      else fieldset.appendChild(actions);
    }
  }

  function streamlinedCompactSettings() {
    const settings = byId('guided-settings');
    const content = byId('guided-settings-content');
    const account = byId('account');
    if (!settings || !content) return;

    if (account && account.parentElement !== content) content.prepend(account);

    const accountLegend = account ? account.querySelector(':scope > legend') : null;
    if (accountLegend) accountLegend.textContent = '账号登录';

    const securityLegend = byId('account-security')?.querySelector(':scope > legend');
    if (securityLegend) securityLegend.textContent = '密码与设备安全';

    const providerLegend = byId('provider')?.querySelector(':scope > legend');
    if (providerLegend) providerLegend.textContent = '模型设置';

    Array.from(content.children).forEach((node) => {
      if (node instanceof HTMLElement) node.classList.remove('wide');
    });

    streamlinedCompactFieldset('account', ['username', 'password']);
    streamlinedCompactFieldset('provider', ['provider-name', 'base-url', 'model', 'api-key', 'timeout']);

    const securityGrid = byId('account-security')?.querySelector('.workspace-grid');
    if (securityGrid) securityGrid.classList.add('streamlined-settings-security-grid');

    document.querySelectorAll('a[href="#account"]').forEach((link) => {
      link.addEventListener('click', () => { settings.open = true; });
    });
  }

  function streamlinedReorganizeMainFlow() {
    const nav = document.querySelector('#guided-workflow .guided-step-nav');
    if (nav) {
      const anchors = Array.from(nav.querySelectorAll('a'));
      const labels = [
        '1 选择人物',
        '2 编辑关系',
        '3 更新主对话',
        '4 AI 回复与行动建议',
        '5 更新行动与结果',
      ];
      anchors.forEach((anchor, index) => {
        if (index < labels.length) anchor.textContent = labels[index];
        else anchor.classList.add('streamlined-hidden');
      });
    }

    streamlinedSetHeading(
      'guided-step-2',
      '编辑当前关系',
      '自动载入这个人物上次保存的关系状态；修改后直接保存更新。'
    );
    streamlinedSetHeading(
      'guided-step-3',
      '更新这个人物的主对话',
      '每个人物在日常模式只使用一个主对话。新增消息或批量导入都会追加到同一个主对话。'
    );
    streamlinedSetHeading(
      'guided-step-4',
      'AI 回复与行动建议',
      '主对话更新后自动分析并生成回复，同时刷新行动计划；这里只需要查看和编辑结果。'
    );
    streamlinedSetHeading(
      'guided-step-5',
      '更新行动与真实结果',
      '确认你准备执行的行动，并在真实发生后记录执行与结果；随后系统自动完成学习和复盘。'
    );

    const step4 = byId('guided-step-4');
    if (step4 && !byId('streamlined-auto-status')) {
      const header = step4.querySelector('.guided-step-header');
      if (header) header.insertAdjacentElement('afterend', streamlinedAutoStatus);
    }

    const actionPrimary = byId('guided-action-primary');
    const learningPrimary = byId('guided-learning-primary');
    const step5 = byId('guided-step-5');
    const step6 = byId('guided-step-6');

    const outcome = byId('action-outcome-workspace');
    if (actionPrimary && outcome) actionPrimary.appendChild(outcome);

    if (step5 && learningPrimary) {
      let details = byId('streamlined-review-details');
      if (!details) {
        details = document.createElement('details');
        details.id = 'streamlined-review-details';
        details.className = 'streamlined-review-details';
        const summary = document.createElement('summary');
        summary.textContent = '自动反馈、学习与复盘详情';
        details.append(summary, streamlinedReviewStatus, learningPrimary);
        step5.appendChild(details);
      }
    }
    if (step6) step6.classList.add('streamlined-hidden');

    streamlinedHide('guided-generate-action-plan');
    streamlinedHide('guided-action-plan-status');
    streamlinedHide('guided-load-feedback-learning');
    streamlinedHide('guided-run-reanalysis');
    streamlinedHide('guided-learning-status');

    const conversationCard = byId('conversation-heading')?.closest('.workspace-card');
    if (conversationCard) conversationCard.classList.add('streamlined-hidden');

    ['load-relationships', 'create-relationship', 'relationship-select'].forEach(streamlinedHide);
    document.querySelectorAll('label[for="relationship-select"]').forEach((node) => node.classList.add('streamlined-hidden'));

    streamlinedHide('load-messages');
    streamlinedHide('import-text');
    streamlinedHide('create-message');
    streamlinedHide('text-import-title');
    document.querySelectorAll('label[for="text-import-title"]').forEach((node) => node.classList.add('streamlined-hidden'));

    const messageButton = document.createElement('button');
    messageButton.id = 'streamlined-add-message';
    messageButton.type = 'button';
    messageButton.className = 'requires-auth streamlined-primary-button';
    messageButton.textContent = '添加到主对话并自动分析';
    byId('create-message')?.insertAdjacentElement('afterend', messageButton);

    const importButton = document.createElement('button');
    importButton.id = 'streamlined-import-text';
    importButton.type = 'button';
    importButton.className = 'requires-auth streamlined-primary-button';
    importButton.textContent = '批量追加到主对话并自动分析';
    byId('import-text')?.insertAdjacentElement('afterend', importButton);

    const relationshipButton = document.createElement('button');
    relationshipButton.id = 'streamlined-save-relationship';
    relationshipButton.type = 'button';
    relationshipButton.className = 'requires-auth streamlined-primary-button';
    relationshipButton.textContent = '保存关系';
    byId('create-relationship')?.insertAdjacentElement('afterend', relationshipButton);
  }

  const streamlinedBaseLoadRelationships = loadRelationships;
  loadRelationships = async function() {
    await streamlinedBaseLoadRelationships();
    if (!selectedPersonId) return;
    const allItems = await api('/api/v1/relationships');
    const items = allItems
      .filter((item) => item.person_id === selectedPersonId)
      .sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')));
    const item = items[0] || null;
    selectedRelationshipId = item ? item.id : null;
    byId('relationship-select').value = selectedRelationshipId || '';
    byId('relationship-state').value = item ? item.status : 'unknown';
    byId('relationship-stage').value = item ? item.stage : 'unknown';
    byId('relationship-long-term-goal').value = item?.long_term_goal || '';
    byId('relationship-current-goal').value = item?.current_goal || '';
    byId('relationship-notes').value = item?.notes || '';
    relationshipStatus.textContent = item
      ? '已载入上次保存的关系状态。修改后点击“保存关系”即可更新。'
      : '当前人物还没有关系记录。填写后点击“保存关系”创建。';
  };

  const streamlinedBaseLoadConversations = loadConversations;
  loadConversations = async function() {
    await streamlinedBaseLoadConversations();
    if (!selectedPersonId) return;
    const items = await api(`/api/v1/conversations?person_id=${encodeURIComponent(selectedPersonId)}`);
    const ordered = [...items].sort((a, b) => String(b.updated_at || '').localeCompare(String(a.updated_at || '')));
    const primary = ordered[0] || null;
    selectedConversationId = primary ? primary.id : null;
    byId('conversation-select').value = selectedConversationId || '';
    byId('conversation-id').value = selectedConversationId || '';
    conversationStatus.textContent = primary
      ? '已自动使用这个人物最近的主对话。'
      : '首次添加消息时会自动创建这个人物的主对话。';
  };

  async function streamlinedSaveRelationship() {
    if (!selectedPersonId) throw new Error('请先选择人物');
    const payload = {
      status: byId('relationship-state').value.trim() || 'unknown',
      stage: byId('relationship-stage').value.trim() || 'unknown',
      long_term_goal: nullableText('relationship-long-term-goal'),
      current_goal: nullableText('relationship-current-goal'),
      notes: nullableText('relationship-notes'),
    };
    if (selectedRelationshipId) {
      await api(`/api/v1/relationships/${encodeURIComponent(selectedRelationshipId)}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      });
    } else {
      const created = await api('/api/v1/relationships', {
        method: 'POST',
        body: JSON.stringify({person_id: selectedPersonId, ...payload}),
      });
      selectedRelationshipId = created.id;
    }
    await loadRelationships();
    if (selectedConversationId) {
      await api(`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}`, {
        method: 'PATCH',
        body: JSON.stringify({relationship_id: selectedRelationshipId}),
      });
      await loadConversations();
    }
    relationshipStatus.textContent = '关系已保存，后续主对话和 AI 分析会使用最新关系状态。';
  }

  async function streamlinedEnsurePrimaryConversation() {
    if (!selectedPersonId) throw new Error('请先选择人物');
    await loadConversations();
    if (selectedConversationId) return selectedConversationId;
    const created = await api('/api/v1/conversations', {
      method: 'POST',
      body: JSON.stringify({
        person_id: selectedPersonId,
        relationship_id: selectedRelationshipId || null,
        title: '主对话',
        status: 'active',
      }),
    });
    selectedConversationId = created.id;
    byId('conversation-id').value = created.id;
    await loadConversations();
    return selectedConversationId;
  }

  async function streamlinedRunEvidencePipeline() {
    if (streamlinedEvidencePipelineRunning || !selectedConversationId) return;
    streamlinedEvidencePipelineRunning = true;
    const completed = [];
    const failures = [];
    streamlinedAutoStatus.textContent = '正在自动分析主对话、生成回复并更新行动计划…';
    const steps = [
      ['AI 回复', loadStrategicReply],
      ['行动计划', generateActionPlan],
      ['已保存计划', loadSavedActionPlan],
      ['待确认行动', loadActionDecisionContext],
      ['执行状态', loadActionExecutionContext],
      ['结果状态', loadActionOutcomeContext],
    ];
    try {
      for (const [label, fn] of steps) {
        try {
          await fn();
          completed.push(label);
        } catch (error) {
          failures.push(`${label}: ${error instanceof Error ? error.message : String(error)}`);
        }
      }
      if (failures.length) {
        streamlinedAutoStatus.textContent = `自动流程已完成部分步骤：${completed.join('、') || '无'}。需要处理：${failures.join('；')}`;
      } else {
        streamlinedAutoStatus.textContent = '主对话已完成自动分析：回复建议、行动计划、待确认项和执行状态均已更新。真实行动仍由你确认和记录。';
      }
    } finally {
      streamlinedEvidencePipelineRunning = false;
    }
  }

  async function streamlinedAddMessage() {
    const conversationId = await streamlinedEnsurePrimaryConversation();
    const content = byId('message-content').value.trim();
    if (!content) throw new Error('消息内容不能为空');
    const payload = {
      conversation_id: conversationId,
      sender_type: byId('message-sender').value,
      content,
    };
    const sentAt = byId('message-sent-at').value.trim();
    if (sentAt) payload.sent_at = sentAt;
    await api('/api/v1/messages', {method: 'POST', body: JSON.stringify(payload)});
    byId('message-content').value = '';
    byId('message-sent-at').value = '';
    await loadMessages();
    try { await loadTimeline(); } catch (_) {}
    messagesStatus.textContent = '消息已加入主对话，正在自动更新 AI 回复和行动计划。';
    await streamlinedRunEvidencePipeline();
  }

  async function streamlinedImportText() {
    const conversationId = await streamlinedEnsurePrimaryConversation();
    const text = byId('text-import-body').value;
    if (!text.trim()) throw new Error('批量文本不能为空');
    textImportStatus.textContent = '正在按时间整理并追加到主对话…';
    const data = await api('/api/v1/text-imports', {
      method: 'POST',
      body: JSON.stringify({
        person_id: selectedPersonId,
        conversation_id: conversationId,
        text,
        auto_sort_by_sent_at: true,
      }),
    });
    byId('text-import-body').value = '';
    selectedConversationId = data.conversation_id;
    byId('conversation-id').value = data.conversation_id;
    await loadConversations();
    await loadMessages();
    try { await loadTimeline(); } catch (_) {}
    textImportStatus.textContent = `已向主对话追加 ${data.imported_count} 条消息，正在自动更新 AI 回复和行动计划。`;
    await streamlinedRunEvidencePipeline();
  }

  async function streamlinedPersistAllLearningCandidates() {
    const candidates = Array.isArray(actionLearningCandidates) ? [...actionLearningCandidates] : [];
    let persisted = 0;
    for (const item of candidates) {
      const candidateId = item && item.source_candidate_id;
      if (!candidateId) continue;
      try {
        await api(
          `/api/v1/persons/${encodeURIComponent(selectedPersonId)}/memory-updates/${encodeURIComponent(candidateId)}/persist`,
          {method: 'POST'},
        );
        persisted += 1;
      } catch (error) {
        if (!(error && error.status === 409)) throw error;
      }
    }
    return persisted;
  }

  async function streamlinedRunOutcomeLearningReview() {
    if (streamlinedOutcomePipelineRunning || !selectedPersonId) return;
    streamlinedOutcomePipelineRunning = true;
    streamlinedReviewStatus.textContent = '已记录真实结果，正在自动进行反馈、学习和复盘…';
    try {
      await loadActionFeedback();
      await loadActionLearning();
      const persisted = await streamlinedPersistAllLearningCandidates();
      await loadPersistedActionLearning();
      if (selectedConversationId) {
        await loadActionReanalysisInputs();
        await runActionReanalysis();
        await generateActionPlan();
        await loadSavedActionPlan();
        await loadActionDecisionContext();
        await loadActionExecutionContext();
      }
      streamlinedReviewStatus.textContent = `自动复盘完成；本轮新增保存 ${persisted} 条学习记忆，并已刷新下一轮分析与行动计划。`;
    } catch (error) {
      streamlinedReviewStatus.textContent = `自动复盘未全部完成：${error instanceof Error ? error.message : String(error)}`;
    } finally {
      streamlinedOutcomePipelineRunning = false;
    }
  }

  function streamlinedObserveLifecycleStatus() {
    const decisionStatus = byId('action-decision-status');
    const executionStatus = byId('action-execution-status');
    const outcomeStatus = byId('action-outcome-status');

    if (decisionStatus) {
      new MutationObserver(async () => {
        const text = decisionStatus.textContent || '';
        if (text === streamlinedLastObservedDecisionStatus) return;
        streamlinedLastObservedDecisionStatus = text;
        if (/^Recorded confirmed Action Decision/.test(text)) {
          try { await loadActionExecutionContext(); } catch (_) {}
        }
      }).observe(decisionStatus, {childList: true, characterData: true, subtree: true});
    }

    if (executionStatus) {
      new MutationObserver(async () => {
        const text = executionStatus.textContent || '';
        if (text === streamlinedLastObservedExecutionStatus) return;
        streamlinedLastObservedExecutionStatus = text;
        if (/^Recorded Action Execution/.test(text)) {
          try { await loadActionOutcomeContext(); } catch (_) {}
        }
      }).observe(executionStatus, {childList: true, characterData: true, subtree: true});
    }

    if (outcomeStatus) {
      new MutationObserver(async () => {
        const text = outcomeStatus.textContent || '';
        if (text === streamlinedLastObservedOutcomeStatus) return;
        streamlinedLastObservedOutcomeStatus = text;
        if (/^Recorded Outcome/.test(text)) await streamlinedRunOutcomeLearningReview();
      }).observe(outcomeStatus, {childList: true, characterData: true, subtree: true});
    }
  }

  streamlinedCompactSettings();
  streamlinedReorganizeMainFlow();
  streamlinedObserveLifecycleStatus();

  bind('streamlined-save-relationship', streamlinedSaveRelationship, relationshipStatus);
  bind('streamlined-add-message', streamlinedAddMessage, messagesStatus);
  bind('streamlined-import-text', streamlinedImportText, textImportStatus);
'''
