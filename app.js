const GROUPS = ['Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps', 'Legs', 'Glutes', 'Core'];

const $ = (id) => document.getElementById(id);
const state = { workouts: [], group: 'All', query: '' };

function el(tag, props = {}, children = []) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

function renderGroups() {
  const chips = ['All', ...GROUPS].map((group) => {
    const total = group === 'All'
      ? state.workouts.length
      : state.workouts.filter((w) => w.group === group).length;
    const chip = el('button', { className: 'chip', type: 'button', textContent: `${group} ${total}` });
    chip.setAttribute('aria-pressed', String(group === state.group));
    chip.addEventListener('click', () => {
      state.group = group;
      renderGroups();
      renderGrid();
    });
    return chip;
  });
  $('groups').replaceChildren(...chips);
}

function renderGrid() {
  const query = state.query.trim().toLowerCase();
  const shown = state.workouts.filter((w) =>
    (state.group === 'All' || w.group === state.group) &&
    [w.name, w.group, w.equipment, w.secondary].join(' ').toLowerCase().includes(query));

  $('count').textContent = shown.length
    ? `${shown.length} ${shown.length === 1 ? 'workout' : 'workouts'}`
    : 'No workouts match. Try another search.';

  $('grid').replaceChildren(...shown.map((w) => {
    const card = el('button', { className: 'card', type: 'button' }, [
      el('img', {
        src: `https://i.ytimg.com/vi/${w.videoId}/mqdefault.jpg`,
        alt: '',
        loading: 'lazy',
      }),
      el('div', { className: 'card-body' }, [
        el('p', { className: 'card-name', textContent: w.name }),
        el('div', { className: 'tags' }, [
          el('span', { className: 'tag', textContent: w.group }),
          el('span', { className: 'tag', textContent: w.equipment }),
        ]),
      ]),
    ]);
    card.addEventListener('click', () => openDetail(w));
    return card;
  }));
}

function openDetail(w) {
  $('detail-name').textContent = w.name;
  $('detail-video').src = `https://www.youtube-nocookie.com/embed/${w.videoId}`;
  $('detail-facts').replaceChildren(...[
    ['Primary muscle', w.group],
    ['Also works', w.secondary],
    ['Equipment', w.equipment],
    ['Level', w.level],
  ].map(([label, value]) => el('div', {}, [
    el('dt', { textContent: label }),
    el('dd', { textContent: value }),
  ])));
  $('detail-credit').textContent = `Video by ${w.channel}.`;
  $('detail-link').href = `https://www.youtube.com/watch?v=${w.videoId}`;
  $('detail').showModal();
}

$('detail-close').addEventListener('click', () => $('detail').close());
$('detail').addEventListener('click', (event) => {
  if (event.target === $('detail')) $('detail').close();
});
// Clearing the src stops playback once the dialog is dismissed.
$('detail').addEventListener('close', () => { $('detail-video').src = ''; });

$('search').addEventListener('input', (event) => {
  state.query = event.target.value;
  renderGrid();
});

fetch('data/workouts.json')
  .then((response) => {
    if (!response.ok) throw new Error(response.statusText);
    return response.json();
  })
  .then((workouts) => {
    state.workouts = workouts;
    renderGroups();
    renderGrid();
  })
  .catch(() => {
    $('count').textContent = "Couldn't load the workouts. Refresh to try again.";
  });
