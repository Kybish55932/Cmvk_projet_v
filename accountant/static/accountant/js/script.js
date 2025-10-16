document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.querySelector("#violationsTable tbody");
  const fDateFrom = document.getElementById("dateFrom");
  const fDateTo = document.getElementById("dateTo");
  const applyBtn = document.getElementById("applyFiltersBtn");
  const resetBtn = document.getElementById("resetFiltersBtn");
  const exportBtn = document.getElementById("exportExcelBtn");

  const today = new Date().toISOString().slice(0, 10);
  fDateFrom.value = today;
  fDateTo.value = today;

  let data = [];

  function loadData() {
    fetch("/accountant/api/list/")
      .then(r => r.json())
      .then(d => {
        data = d.items || [];
        render();
      });
  }

  function render() {
    tbody.innerHTML = "";
    getFilteredData().forEach(v => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${v.date || ""}</td>
        <td>${v.airport || ""}</td>
        <td>${v.service || ""}</td>
        <td>${v.offender || ""}</td>
        <td>${v.measures || ""}</td>`;
      tbody.appendChild(tr);
    });
  }

  function getFilteredData() {
    const d1 = fDateFrom.value;
    const d2 = fDateTo.value;
    return data.filter(v => {
      if (d1 && v.date < d1) return false;
      if (d2 && v.date > d2) return false;
      return true;
    });
  }

  if (applyBtn) applyBtn.addEventListener("click", render);
  if (resetBtn) resetBtn.addEventListener("click", () => {
    fDateFrom.value = today;
    fDateTo.value = today;
    render();
  });

  if (exportBtn) exportBtn.addEventListener("click", () => {
    if (!window.XLSX) return alert("Библиотека XLSX не загружена");
    const rows = [["Дата","Аэропорт","Служба","Кто нарушил","Принятые меры"]];
    getFilteredData().forEach(v => rows.push([
      v.date, v.airport, v.service, v.offender, v.measures
    ]));
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(rows);
    XLSX.utils.book_append_sheet(wb, ws, "Отчёт");
    XLSX.writeFile(wb, `Отчёт_${today}.xlsx`);
  });

  loadData();
});
