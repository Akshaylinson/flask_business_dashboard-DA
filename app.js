async function loadSummary() {
  const res = await fetch('/api/summary');
  const s = await res.json();
  document.getElementById('kpi-total').innerText = s.total_records.toLocaleString();
  document.getElementById('kpi-states').innerText = s.unique_states.toLocaleString();
  document.getElementById('kpi-cities').innerText = s.unique_cities.toLocaleString();
  document.getElementById('kpi-owners').innerText = s.unique_owners.toLocaleString();
  document.getElementById('kpi-phones').innerText =
    `${s.phones_present.toLocaleString()} (${Math.round(100 * s.phones_present / s.total_records)}%)`;
  document.getElementById('kpi-dupes').innerText = s.potential_duplicates.toLocaleString();
}

async function loadTopStates() {
  const res = await fetch('/api/top-states?limit=12');
  const data = await res.json();
  const x = data.map(d => d.State);
  const y = data.map(d => d.count);
  Plotly.newPlot('chart-states', [{ type: 'bar', x, y }], {
    margin: { t: 10, l: 40, r: 10, b: 80 },
    xaxis: { tickangle: -45 },
    yaxis: { title: 'Count' }
  }, { displayModeBar: false, responsive: true });
}

async function loadTopCities() {
  const res = await fetch('/api/top-cities?limit=20');
  const data = await res.json();
  const x = data.map(d => `${d.City} (${d.State})`);
  const y = data.map(d => d.count);
  Plotly.newPlot('chart-cities', [{ type: 'bar', x, y }], {
    margin: { t: 10, l: 40, r: 10, b: 140 },
    xaxis: { tickangle: -60 },
    yaxis: { title: 'Count' }
  }, { displayModeBar: false, responsive: true });
}

function initTable() {
  new DataTable('#records', {
    serverSide: true,
    processing: true,
    lengthMenu: [10, 25, 50, 100],
    ajax: { url: '/api/table', type: 'GET', data: d => d },
    columns: [
      { data: 'Business Name' },
      { data: 'Owner Name' },
      { data: 'City' },
      { data: 'State' },
      { data: 'Mobile Number' }
    ],
    order: []
  });
}

document.addEventListener('DOMContentLoaded', () => {
  loadSummary();
  loadTopStates();
  loadTopCities();
  initTable();
});
