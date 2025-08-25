(function () {
    var el = document.getElementById('sparkline-data');
    if (!el) return;
    var dates = JSON.parse(el.getAttribute('data-dates'));
    var stocks = JSON.parse(el.getAttribute('data-stocks'));
    var ctx = document.getElementById('sparkline').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                data: stocks,
                borderColor: '#2b7cff',
                borderWidth: 1,
                pointRadius: 0,
                fill: false,
                tension: 0.3
            }]
        },
        options: {
            plugins: { legend: { display: false }, tooltip: { enabled: false } },
            scales: {
                x: {
                    display: true,
                    title: { display: true, text: 'Date' },
                    ticks: { autoSkip: true, maxTicksLimit: 10 }
                },
                y: {
                    display: true,
                    title: { display: true, text: 'Stock' },
                    beginAtZero: true
                }
            },
            elements: { line: { borderWidth: 1 }, point: { radius: 0 } }
        }
    });
})();
