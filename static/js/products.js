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
          let pid = row.cells[0].textContent;
          let pname = row.cells[2].textContent;
          let pqty = row.cells[3].textContent;
          let pcp = row.cells[4].textContent;
          let psp = row.cells[5].textContent;
        
          // Send an AJAX request to update the product
          let xhr = new XMLHttpRequest();
          xhr.open("POST", "/products/update");
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
        xhr.send(`pid=${pid}&pname=${pname}&pqty=${pqty}&pcp=${pcp}&psp=${psp}`);
}

function editVariant(button) {
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

      function saveVariant(button) {
          // Get the table row element
          let row = button.closest("tr");
        
          // Get the updated values of each cell
          let vid = row.cells[0].textContent;
          let vname = row.cells[2].textContent;
          let vqty = row.cells[3].textContent;
        
          // Send an AJAX request to update the product
          let xhr = new XMLHttpRequest();
          xhr.open("POST", "/variants/update");
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
        xhr.send(`vid=${vid}&vname=${vname}&vqty=${vqty}`);
}

