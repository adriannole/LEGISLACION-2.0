const ctx = document.getElementById('graficoComparacion').getContext('2d');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Claridad', 'Coherencia', 'Cumplimiento ISO', 'Redacción técnica'],
        datasets: [
            {
                label: 'Usuario',
                data: [6, 7, 5, 4],
                backgroundColor: 'rgba(255, 99, 132, 0.6)'
            },
            {
                label: 'IA ISO 9001',
                data: [5, 5, 5, 4],
                backgroundColor: 'rgba(54, 162, 235, 0.6)'
            }
        ]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                max: 5
            }
        }
    }
});
