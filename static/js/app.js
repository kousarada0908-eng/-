const { names, sold, dates, daily } = window.dashboardData;

// 📊 商品別売上
new Chart(document.getElementById("productChart"), {
  type: "bar",
  data: {
    labels: names,
    datasets: [{
      label: "売上数",
      data: sold
    }]
  }
});

// 📈 日別売上
new Chart(document.getElementById("dailyChart"), {
  type: "line",
  data: {
    labels: dates,
    datasets: [{
      label: "売上金額",
      data: daily
    }]
  }
});
