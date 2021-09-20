// job one: Retrieve all ontology terms found in a single KEEP collection
const singleCollKeepForm = document.getElementById("single-coll-keep-form");
const singleCollKeepDropdown = document.getElementById("single-coll-keep-dropdown");
const singleCollKeepRun = document.getElementById("single-coll-keep-run");
const singleCollKeepRunLoading = document.getElementById("single-coll-keep-run-loading");
const singleCollKeepError = document.getElementById("single-coll-keep-error");
// job two: Retrieve all ontology terms found in a single PRISM collection
const singleCollPrismForm = document.getElementById("single-coll-prism-form");
const singleCollPrismDropdown = document.getElementById("single-coll-prism-dropdown");
const singleCollPrismRun = document.getElementById("single-coll-prism-run");
const singleCollPrismLoading = document.getElementById("single-coll-prism-run-loading");
const singleCollPrismError = document.getElementById("single-coll-prism-error");

// jobs one and two: change button attribs
let dropDownChangers = [{"dd": singleCollKeepDropdown, "button": singleCollKeepRun}, {"dd": singleCollPrismDropdown, "button": singleCollPrismRun}];

dropDownChangers.forEach(item => {
  (item.dd).addEventListener('change', (event) => {
    (item.button).setAttribute('data-col_id', event.target.value);
  })
})

// function to run for both jobs one and two
function singleCollection(event, error_div, runButton, runButtonLoading) {
  event.preventDefault();

  if (error_div.style.display = "block") {
    error_div.style.display = "none";
  };

  let repo_name = runButton.getAttribute('data-type');
  let col_id = runButton.getAttribute('data-col_id');
  let username = runButton.getAttribute('data-user');
  let job_name = runButton.getAttribute('data-job_name');

  if (col_id === "none") {
    error_div.innerHTML = "<strong>You need to choose a collection.</strong>";
    error_div.style.display = "block";
  }
  else {
    runButton.style.display = "none";
    runButtonLoading.style.display = "block";

    let xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.timeout = 5000;
    xhr.open("POST", "https://harmonizer.lib.asu.edu/subspace/coll-metadata");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");

    xhr.onload = function() {
      if (xhr.status === 200) {
        data = xhr.response;
        if (data.status === "empty") {
          runButton.style.display = "block";
          runButtonLoading.style.display = "none";
          error_div.innerHTML = `<strong>No taxonomy metadata returned from Solr for this collection!</strong>`
        }
        else {
          window.location.href = 'https://harmonizer.lib.asu.edu/my-jobs';
        }
      } else {
        // request error
        error_div.innerHTML = `<strong>There was an error while running your new job.</strong>`;
        runButton.style.display = "block";
        runButtonLoading.style.display = "none";
        error_div.style.display = "block";
        console.log('HTTP error:', xhr.status, xhr.statusText);
      }
    };
    xhr.onerror = function() {
      console.log("Request failed");
      error_div.innerHTML = "<strong>Your request failed!</strong>";
      runButton.style.display = "block";
      runButtonLoading.style.display = "none";
      error_div.style.display = "block";
    };
    let payload = {
        "repo_name": repo_name,
        "col_id": col_id,
        "username": username,
        "job_name": job_name
    };
    xhr.send(JSON.stringify(payload));
  }
}

// run job one
singleCollKeepRun.addEventListener("click", (event) => {
  singleCollection(event, singleCollKeepError, singleCollKeepRun, singleCollKeepRunLoading);
})
singleCollKeepForm.addEventListener("submit", ()=> {
  singleCollection(event, singleCollKeepError, singleCollKeepRun, singleCollKeepRunLoading);
});
// run job two
singleCollPrismRun.addEventListener("click", (event) => {
  singleCollection(event, singleCollPrismError, singleCollPrismRun, singleCollPrismLoading);
})
singleCollPrismForm.addEventListener("submit", ()=> {
  singleCollection(event, singleCollPrismError, singleCollPrismRun, singleCollPrismLoading);
});

// job three -- Retrieve all ontology terms found in a single record
const singleItemForm = document.getElementById("single-item-form");
const singleItemError = document.getElementById("single-item-error");
const singleItemRun = document.getElementById("single-item-run");
const singleItemRunLoading = document.getElementById("single-item-run-loading");
const singleItemInput = document.getElementById("single-item-input");
const singleItemRadioKeep = document.getElementById("single-item-radio-keep");
const singleItemRadioPrism = document.getElementById("single-item-radio-prism");

// change radio attribs
let radioChangers = [singleItemRadioKeep, singleItemRadioPrism];

radioChangers.forEach(item => {
  (item).addEventListener('change', (event) => {
    singleItemRun.setAttribute('data-type', event.target.value);
  })
})

//function to run job three
function singleItemk(event, error_div, runButton, runButtonLoading) {
  event.preventDefault();

  if (error_div.style.display = "block") {
    error_div.style.display = "none";
  };

  let item_id = (singleItemInput.value).trim();
  let repo_name = runButton.getAttribute('data-type');
  let username = runButton.getAttribute('data-user');
  let job_name = runButton.getAttribute('data-job_name');

  if (item_id === "") {
    error_div.innerHTML = "<strong>You need to choose an item.</strong>";
    error_div.style.display = "block";
  }
  else {
    runButton.style.display = "none";
    runButtonLoading.style.display = "block";

    let xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.timeout = 5000;
    xhr.open("POST", "https://harmonizer.lib.asu.edu/subspace/item-metadata");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");

    xhr.onload = function() {
      if (xhr.status === 200) {
        data = xhr.response;
        if (data.status === "success") {
          window.location.href = 'https://harmonizer.lib.asu.edu/my-jobs';
        }
        else {
          runButton.style.display = "block";
          runButtonLoading.style.display = "none";
          error_div.innerHTML = `<strong>${data.status}</strong>`
        }
      } else {
        // request error
        error_div.innerHTML = `<strong>There was an error while running your new job.</strong>`;
        runButton.style.display = "block";
        runButtonLoading.style.display = "none";
        error_div.style.display = "block";
        console.log('HTTP error:', xhr.status, xhr.statusText);
      }
    };
    xhr.onerror = function() {
      console.log("Request failed");
      error_div.innerHTML = "<strong>Your request failed!</strong>";
      runButton.style.display = "block";
      runButtonLoading.style.display = "none";
      error_div.style.display = "block";
    };
    let payload = {
        "repo_name": repo_name,
        "item_id": item_id,
        "username": username,
        "job_name": job_name
    };
    xhr.send(JSON.stringify(payload));
  }
}
