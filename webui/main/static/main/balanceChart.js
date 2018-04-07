window.onload = function() {
    const ctx = document.getElementById('balanceChart').getContext("2d");
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ["0"],
            datasets: [{"data": [0]}]
        },
        options: {
            layout: {
                padding: {
                    left: 20,
                    right: 20,
                    top: 20,
                    bottom: 20
                }
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
