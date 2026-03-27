const data = window.dashboardData;

const productCanvas = document.getElementById("productChart");
const dailyCanvas = document.getElementById("dailyChart");

if (!data || !productCanvas || !dailyCanvas) {
  console.error("データまたはHTML要素が不足しています");
} else {

  // 📊 商品別売上
  new Chart(productCanvas, {
    type: "bar",
    data: {
      labels: data.names,
      datasets: [{
        label: "売上数",
        data: data.sold
      }]
    }
  });

  // 📈 日別売上
  new Chart(dailyCanvas, {
    type: "line",
    data: {
      labels: data.dates,
      datasets: [{
        label: "売上金額",
        data: data.daily
      }]
    }
  });

}
