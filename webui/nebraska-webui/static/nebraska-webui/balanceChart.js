window.onload = function() {
    const ctx = document.getElementById('balance-chart').getContext("2d");
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ["0"],
            datasets: [{
                "data": [0]
            }]
        },
        options: {
            legend: {
                display: false
            },
            layout: {
                padding: {
                    left: 20,
                    right: 20,
                    top: 20,
                    bottom: 20
                }
            },
            responsive: false,
            elements: {
                point: {
                    radius: 0
                }
            },
            scales: {
                xAxes: [{
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 20,
                        callback: function(value) {
                            return new Date(value).toLocaleDateString('en', {month:'short', year:'numeric'});
                        }
                    }
                }]
            }
        }
    });

    $.getJSON('/account-balances.json',
        function (data) {
            chart.data.labels = data.dates;
            chart.data.datasets = [];
            if (data.hasOwnProperty("balances")) {
                for (let account in data["balances"]) {
                    if (data["balances"].hasOwnProperty(account)) {
                        chart.data.datasets.push({
                            "data": data["balances"][account],
                            "label": account
                        });
                    }
                }
            }
            chart.update();
            console.log(chart.data);
        }
    );
}
