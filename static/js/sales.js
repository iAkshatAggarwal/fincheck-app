function editRow(button) {
        // Get the table row element
        let row = button.closest("tr");
        // Hide the "Edit" button and show the "Save" button
        row.querySelector(".btn-outline-primary").classList.add("d-none");
        row.querySelector(".btn-outline-success").classList.remove("d-none");
        // Make all the table cells in the row (except Actions) editable
        row.querySelectorAll("td:not(:last-child)").forEach((cell) => {
          cell.setAttribute("contenteditable", "true");
          cell.setAttribute("data-old-value", cell.textContent);
        });
        event.preventDefault(); // prevent scrolling up
}

function saveRow(button) {
    // Get the table row element
    let row = button.closest("tr");
  
    // Get the updated values of each cell
    let id = row.cells[0].textContent;
    let date = row.cells[2].textContent;
    let product = row.cells[3].textContent;
    let sale_qty = row.cells[4].textContent;
    let sale_price = row.cells[5].textContent;
    let sale_amt = row.cells[6].textContent;
    let sale_profit = row.cells[7].textContent;
    let customer = row.cells[8].textContent;
    let status = row.cells[9].textContent;
  
    // Send an AJAX request to update the product
    let xhr = new XMLHttpRequest();
    xhr.open("POST", "/sales/update");
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.onreadystatechange = function() {
      if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
          // Update successful, hide the "Save" button and show the "Update" button again
          row.querySelector(".btn-outline-success").classList.add("d-none");
          row.querySelector(".btn-outline-primary").classList.remove("d-none");
          // Make all the table cells in the row non-editable
          row.querySelectorAll("td").forEach((cell) => {
            cell.setAttribute("contenteditable", "false");
            cell.removeAttribute("data-old-value");
          });
        } else {
          // Error occurred
          console.error(xhr.responseText);
        }
      }
    };
  xhr.send(`id=${id}&date=${date}&product=${product}&sale_qty=${sale_qty}&sale_price=${sale_price}&sale_amt=${sale_amt}&sale_profit=${sale_profit}&customer=${customer}&status=${status}`);
}

function deleteRow(button) {
  const saleId = button.dataset.saleId;
  const product = button.dataset.product;
  const saleQty = button.dataset.saleQty;
  const saleDate = button.dataset.saleDate;
  const confirmed = confirm(`Are you sure you want to delete the sale on ${saleDate} for ${saleQty} pcs of ${product}  ?`);
  if (confirmed) {
    window.location.href = `/sales/${saleId}/delete?product=${encodeURIComponent(product)}&sale_qty=${encodeURIComponent(saleQty)}`;
  }
}
