// Dashboard charts. Data comes from the "chart-data" JSON block.
(function () {
  var data = JSON.parse(document.getElementById('chart-data').textContent);
  var accent = '#1f6f4a';
  Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
  Chart.defaults.color = '#5f6b7a';

  new Chart(document.getElementById('salesChart'), {
    type: 'bar',
    data: {
      labels: data.sale_labels,
      datasets: [{ label: 'Sales', data: data.sale_values, backgroundColor: accent, borderRadius: 3, maxBarThickness: 18 }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
        y: { beginAtZero: true, grid: { color: '#eef0f3' } }
      }
    }
  });

  var catCanvas = document.getElementById('categoryChart');
  if (catCanvas) {
    new Chart(catCanvas, {
      type: 'doughnut',
      data: {
        labels: data.categories,
        datasets: [{
          data: data.category_counts,
          backgroundColor: ['#1f6f4a', '#3b8f68', '#5fae88', '#8ccaa9', '#b9e2cc', '#2f5d7c', '#4f7fa0', '#7aa3c0', '#a7c5da', '#c9a227', '#d9b95b', '#e8d398'],
          borderWidth: 0
        }]
      },
      options: { cutout: '62%', plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } } }
    });
  }
})();
