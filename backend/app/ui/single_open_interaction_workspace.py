SINGLE_OPEN_INTERACTION_STYLE = r'''
    button:not(:disabled),
    details > summary,
    .client-card-front {
      transition:
        transform .16s ease,
        box-shadow .16s ease,
        filter .16s ease,
        border-color .16s ease,
        background-color .16s ease;
    }

    button:not(:disabled) {
      cursor: pointer;
    }

    button:not(:disabled):hover,
    details > summary:hover,
    .client-card-front:hover {
      transform: translateY(-1px);
      filter: brightness(1.035);
      box-shadow: 0 9px 22px rgba(49, 78, 118, .16);
    }

    button:not(:disabled):active,
    details > summary:active,
    .client-card-front:active {
      transform: translateY(0) scale(.99);
    }

    button:focus-visible,
    details > summary:focus-visible,
    .client-card-front:focus-visible {
      outline: 3px solid rgba(25, 167, 232, .28);
      outline-offset: 3px;
    }

    button:disabled {
      cursor: not-allowed;
    }
'''


SINGLE_OPEN_INTERACTION_SCRIPT = r'''
  const singleOpenSurfaceMarker = 'test173-single-open-surfaces';

  function singleOpenCloseDetails(activeDetails = null) {
    document.querySelectorAll('details[open]').forEach((details) => {
      if (details !== activeDetails) details.open = false;
    });
  }

  function singleOpenClosePersonCards(activeCard = null) {
    document.querySelectorAll('.client-person-card.is-flipped').forEach((card) => {
      if (card !== activeCard) card.classList.remove('is-flipped');
    });
  }

  function singleOpenActivateDetails(details) {
    singleOpenCloseDetails(details);
    singleOpenClosePersonCards();
  }

  function singleOpenActivatePersonCard(card) {
    singleOpenCloseDetails();
    singleOpenClosePersonCards(card);
  }

  document.documentElement.dataset.singleOpenSurface = singleOpenSurfaceMarker;

  // Native <details> remains click-to-open / click-again-to-close. Before a
  // different summary opens, close every other expandable surface.
  document.addEventListener('click', (event) => {
    const summary = event.target instanceof Element
      ? event.target.closest('summary')
      : null;
    const details = summary ? summary.parentElement : null;
    if (details instanceof HTMLDetailsElement) {
      singleOpenActivateDetails(details);
      return;
    }

    const cardFront = event.target instanceof Element
      ? event.target.closest('.client-card-front')
      : null;
    const card = cardFront ? cardFront.closest('.client-person-card') : null;
    if (card) singleOpenActivatePersonCard(card);
  }, true);

  // Also enforce the contract when a verified workflow opens a details panel
  // programmatically (for example the reality-confirmation surface).
  document.addEventListener('toggle', (event) => {
    const details = event.target;
    if (!(details instanceof HTMLDetailsElement) || !details.open) return;
    singleOpenActivateDetails(details);
  }, true);
'''
