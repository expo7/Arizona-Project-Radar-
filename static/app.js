let permits = [];
const PAGE_SIZE = 25;
let page = 1;
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const stages = {unverified:'Unverified',to_be_bid:'TO BE BID · verified',gc_named:'GC named',progressed:'Trade work progressed',closed:'Closed / stale'};
const investigationFields = [['plan_number','Plan number'],['parcel','Parcel'],['owner','Owner'],['named_gc','Named GC'],['related_permits','Later permits / trades'],['next_contact','Suggested first contact']];
const message = text => { $('message').textContent = text; $('message').hidden = !text; };
async function request(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}
async function load() {
  permits = (await request('/api/permits')).permits;
  $('total').textContent = permits.length;
  $('qualified').textContent = permits.filter(p => p.status === 'qualified').length;
  $('new').textContent = permits.filter(p => p.status === 'new').length;
  const selected = $('county').value;
  const counties = [...new Set(permits.map(p => p.county).filter(Boolean))].sort();
  $('county').replaceChildren(new Option('All counties', ''), ...counties.map(c => new Option(c, c)));
  $('county').value = selected;
  render();
}
function render() {
  const query = $('search').value.trim().toLowerCase();
  const filtered = permits.filter(p => (!query || [p.description,p.address,p.city,p.county,p.permit_id,p.permit_type].some(v => v.toLowerCase().includes(query))) && (!$('status').value || p.status === $('status').value) && (!$('county').value || p.county === $('county').value) && (!$('stage').value || p.opportunity_stage === $('stage').value));
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  page = Math.min(page, pages);
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  $('results').innerHTML = filtered.length ? visible.map(p => `<article class="record"><div><h2>${escapeHtml(p.description)}</h2><div class="meta"><b>${escapeHtml([p.city,p.county].filter(Boolean).join(' · ') || 'Arizona')}</b> · ${escapeHtml(p.address || 'Address unavailable')}<br>${escapeHtml(p.source)} · ${escapeHtml(p.permit_id)} · ${escapeHtml(p.issued_date || 'Date unavailable')} · ${escapeHtml(p.permit_type || 'Type unspecified')}${p.value ? ` · ${escapeHtml(p.value)}` : ''}</div></div><span class="badge">${escapeHtml(p.status)}${p.opportunity_stage && p.opportunity_stage !== 'unverified' ? ` · ${escapeHtml(stages[p.opportunity_stage] || p.opportunity_stage)}` : ''}</span><div class="record-actions">${p.source_url ? `<a href="${escapeHtml(p.source_url)}" target="_blank" rel="noopener noreferrer">View source ↗</a>` : '<span class="meta">No source URL provided</span>'}<button type="button" data-edit="${p.id}">Review / notes</button></div><div class="detail" id="detail-${p.id}" hidden><label>Status<select id="status-${p.id}">${['new','reviewing','qualified','dismissed'].map(s => `<option value="${s}" ${p.status === s ? 'selected' : ''}>${s[0].toUpperCase()+s.slice(1)}</option>`).join('')}</select></label><label>Opportunity stage<select id="stage-${p.id}">${Object.entries(stages).map(([value,label]) => `<option value="${value}" ${p.opportunity_stage === value ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('')}</select></label>${investigationFields.map(([key,label]) => `<label>${label}<input id="${key}-${p.id}" maxlength="500" value="${escapeHtml(p[key])}"></label>`).join('')}<p class="review-hint">TO BE BID is a manual finding, not inferred from missing GC data. Check the Phoenix plan and later permits first; record the link or evidence in notes.</p><label>Notes / evidence<textarea id="notes-${p.id}" maxlength="2000">${escapeHtml(p.notes)}</textarea></label><button type="button" data-save="${p.id}">Save review</button></div></article>`).join('') : `<div class="empty"><strong>${permits.length ? 'No permits match these filters' : 'No permits imported yet'}</strong>${permits.length ? 'Try a different search or status.' : 'Import a CSV from a public permit source to start reviewing projects.'}</div>`;
  $('range').textContent = filtered.length ? `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, filtered.length)} of ${filtered.length} matching permits` : '0 matching permits';
  $('page').textContent = `Page ${page} of ${pages}`;
  $('previous').disabled = page === 1;
  $('next').disabled = page === pages;
  $('pagination').hidden = filtered.length === 0;
}
for (const [id, event] of [['search', 'input'], ['status', 'change'], ['county', 'change'], ['stage', 'change']]) {
  $(id).addEventListener(event, () => { page = 1; render(); });
}
for (const [id, direction] of [['previous', -1], ['next', 1]]) {
  $(id).addEventListener('click', () => {
    page += direction;
    render();
    $('results').scrollIntoView({behavior: 'smooth', block: 'start'});
  });
}
$('results').addEventListener('click', async event => {
  const edit = event.target.closest('[data-edit]');
  if (edit) { const panel = $('detail-' + edit.dataset.edit); panel.hidden = !panel.hidden; return; }
  const save = event.target.closest('[data-save]');
  if (!save) return;
  try {
    await request('/api/permits/' + save.dataset.save, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:$('status-' + save.dataset.save).value,notes:$('notes-' + save.dataset.save).value,opportunity_stage:$('stage-' + save.dataset.save).value,...Object.fromEntries(investigationFields.map(([key]) => [key,$(key + '-' + save.dataset.save).value]))})});
    message('Review saved.'); await load();
  } catch (error) { message(error.message); }
});
$('file').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const result = await request('/api/import', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({csv:await file.text()})});
    message(`${result.added} records imported; ${result.skipped} duplicates skipped.`); await load();
  } catch (error) { message(error.message); }
  event.target.value = '';
});
$('template').addEventListener('click', event => {
  event.preventDefault();
  const header = 'source,permit_id,description,address,city,county,issued_date,permit_type,value,source_url\n';
  const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([header],{type:'text/csv'})); link.download = 'permit-import-template.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
load().catch(error => message('Could not load permits: ' + error.message));
