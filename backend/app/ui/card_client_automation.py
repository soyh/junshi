CARD_CLIENT_AUTOMATION_SCRIPT = r'''
  /* TEST-167: after a real Outcome, continue from automatic review into the
     next proposed action plan without crossing user decision/execution bounds. */
  const clientBaseLifecycleAfterOutcomeRecorded = lifecycleAfterOutcomeRecorded;

  lifecycleAfterOutcomeRecorded = async function() {
    await clientBaseLifecycleAfterOutcomeRecorded();
    if (!selectedConversationId) return;

    const status = byId('client-automation-status') || lifecycleAutomationStatus;
    status.textContent = '复盘已刷新，正在根据最新证据生成下一轮行动建议…';
    try {
      await generateActionPlan();
      await loadSavedActionPlan();
      await loadActionDecisionContext();
      status.textContent = '自动更新完成：回复建议、复盘和下一步行动均已刷新。新的行动仍需你确认，系统不会自动执行。';
      clientRefreshRealityPrompt();
    } catch (error) {
      status.textContent = `复盘已完成，但下一轮行动更新未完全完成：${error instanceof Error ? error.message : String(error)}`;
    }
  };
'''
