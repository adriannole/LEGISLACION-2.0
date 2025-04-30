// filepath: c:\Users\Adrian Nole\Documents\Github2\LEGISLACION-2.0\static\js\charts.js
const ctx = document.getElementById('graficoComparacion').getContext('2d');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Claridad', 'Aplicación ISO', 'Profundidad Técnica', 'Viabilidad'],
        datasets: [
            {
                label: 'Usuario',
                data: evaluacionUsuario, // Ahora es un array válido
                backgroundColor: 'rgba(54, 162, 235, 0.7)'
            },
            {
                label: 'IA',
                data: evaluacionIA, // Ahora es un array válido
                backgroundColor: 'rgba(255, 99, 132, 0.7)'
            }
        ]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                max: 10
            }
        }
    }
});