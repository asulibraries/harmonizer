const formDiv = document.getElementById("form-div");
const form = document.getElementById("the-form");
const termSearchButton = document.getElementById("term-search");
const termSearchLoading = document.getElementById("term-search-loading");
const termInputBox = document.getElementById("term-input");
const err = document.getElementById("error");
const jumbo = document.getElementById("response");
const respContainer = document.getElementById("resp-data-container");
const respInfo = document.getElementById("resp-data");
const respName = document.getElementById("jumbo-name")
const newSearch = document.getElementById("jumbo-new");
// LC search
const lcNames = document.getElementById("lc-names");
const lcNamesLoading = document.getElementById("lc-names-loading");
const accordionLCnames = document.getElementById("accordionLCnames");
const noLCfound = document.getElementById("no-lc-found");
const lcContainer = document.getElementById("lcContainer");
// MESH search
const meshNames = document.getElementById("mesh-names");
const meshLoading = document.getElementById("mesh-loading");
const meshContainer = document.getElementById("meshContainer");
const accordionMeshNames = document.getElementById("accordionMeshNames");
const noMesh = document.getElementById("noMesh");
// modal
const pushModal = document.getElementById('pushModal');
const sendPutRequest = document.getElementById('push');
const pushLoading = document.getElementById('push-loading');
const modalNewSearch = document.getElementById('modal-new-search');
const closeModal = document.getElementById('close-modal');

var tempArray = []
var search = "";
var inputURI = "";

let base_url = ((window.location.origin).endsWith('/')) ? window.location.origin : (window.location.origin + '/');


function objNotThere(obj, list) {
  for (var i = 0; i < list.length; i++) {
      if (list[i] === obj) {
          return false;
      }
  }
  return true;
}


function refresh() {
  window.location.reload();
  return false;
}


function searchFunc(event) {
  event.preventDefault();

  if (err.style.display = "block") {
    err.style.display = "none";
  };

  termSearchButton.style.display = "none";
  termSearchLoading.style.display = "block";

  let xhr = new XMLHttpRequest()
  xhr.responseType = 'json';
  xhr.timeout = 2000;
  xhr.onload = function() {
    if (xhr.status === 200) {
      data = xhr.response;
      termSearchLoading.style.display = "none";
      respName.innerHTML = `${data.name[0].value}`;
      if ("field_authority_link" in data) {
        let connected_ids = data.field_authority_link;
        if (connected_ids.length > 0) {
          respInfo.innerHTML = `${data.name[0].value} has the following connected authority record URIs: ${connected_ids.join(', ')}`;
        } else {
          respInfo.innerHTML = `No connected authority URIs in this term record.`
        }
      }
      else {
        respInfo.innerHTML = `No connected authority URIs in this term record.`
      }
      let respType = respInfo.getAttribute('data-type');
      if (respType === "keep") {
        respInfo.innerHTML += `<br /><br /><a href="https://keep.lib.asu.edu/search?search_api_fulltext=&f%5B0%5D=linked_agents%3A${data.name[0].value}" class="btn btn-secondary" target="_blank" role="button">See Linked Items in KEEP (Opens New Tab)</a>`
      }
      else if (respType === "prism") {
        respInfo.innerHTML += `<br /><br /><a href="https://prism.lib.asu.edu/search?search_api_fulltext=&f%5B0%5D=linked_agents%3A${data.name[0].value}" class="btn btn-secondary" target="_blank" role="button">See Linked Items in PRISM (Opens New Tab)</a>`
      }
      form.style.display = "none";
      jumbo.style.display = "block";
      respContainer.style.display = "block";
      search = data.name[0].value;
     } else {
       // request error
       err.innerHTML = "Your request failed!";
       termSearchButton.style.display = "block";
       err.style.display = "block";
       console.log('HTTP error:', xhr.status, xhr.statusText);
     }
    };

  xhr.onerror = function() {
    console.log("Request failed");
    err.innerHTML = "Your request failed!";
    termSearchButton.style.display = "block";
    err.style.display = "block";
  };

  if (termInputBox.value.startsWith("http")) {
    if (termInputBox.value.endsWith("?_format=json")){
      searchURL = termInputBox.value;
      inputURI = (termInputBox.value).replace("?_format=json", "");
    }
    else {
      searchURL = (termInputBox.value + "?_format=json")
      inputURI = termInputBox.value;
    }
      xhr.open("GET", searchURL)
      xhr.send()
    } else {
      xhr.abort()
      err.innerHTML = "You didn't enter a URL/URI!";
      err.style.display = "block";
    };
}

termSearchButton.addEventListener("click", ()=>{
  searchFunc(event);
});

form.addEventListener("submit", ()=>{
  searchFunc(event);
});

newSearch.addEventListener("click", ()=>{
  refresh()
});

modalNewSearch.addEventListener("click", ()=>{
  refresh()
});


lcNames.addEventListener("click", ()=>{
  lcNames.style.display = "none";
  lcNamesLoading.style.display = "block";
  fetch(`${base_url}subspace/lc/` + encodeURIComponent(search)).then(response => {
    if (response.status !== 200) {
      console.log('Looks like there was a problem. Status Code: ' +
        response.status);
      return;
    }
    lcNamesLoading.style.display = "none";
    // Examine the text in the response
    response.json().then(data => {
      if (data.status === "success") {
        let lcCounter = 0;
        (data.results).forEach(function (arrayItem) {
          if ((arrayItem.citations).length > 0) {
            lcCounter += 1;
            lcContainer.style.display = "block";
            if (noLCfound.style.display === "block") {
              noLCfound.style.display = "none";
            }
            let ul_list_number = "lc-ulList-" + lcCounter.toString();
            let newAccItem = document.createElement("div");
            newAccItem.classList.add("accordion-item");
            let ariaExpanded = (lcCounter === 1) ? "true" : "false";
            let collapsedButtonClass = (lcCounter === 1) ? "accordion-button" : "accordion-button collapsed";
            let collapsedDivClass = (lcCounter === 1) ? "accordion-collapse collapse show" : "accordion-collapse collapse";
            newAccItem.innerHTML = `<h2 class="accordion-header" id="lc-heading-${lcCounter}">
                                      <button class="${collapsedButtonClass}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-lc-${lcCounter}" aria-expanded="${ariaExpanded}" aria-controls="collapse-lc-${lcCounter}">${arrayItem.heading} (${arrayItem.type})</button>
                                    </h2>
                                    <div id="collapse-lc-${lcCounter}" class="${collapsedDivClass}" aria-labelledby="lc-heading-${lcCounter}" data-bs-parent="#accordionLCnames">
                                      <div class="accordion-body">
                                        <p>LC URI: <a href="${arrayItem.uri}" target="_blank">${arrayItem.uri}</a></p>
                                        <p>Sources consulted on LC record:</p>
                                        <ul id="${ul_list_number}"></ul>
                                        <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#pushModal" data-bs-uri="${arrayItem.uri}" data-bs-heading="${arrayItem.heading}">This is My Match</button>
                                      </div>
                                    </div>`
            accordionLCnames.appendChild(newAccItem);
            let ul_list = "";
            for (i = 0; i < (arrayItem.citations).length; i++) {
              ul_list += "<li>" + (arrayItem.citations)[i] + "</li>"
            }
            let listHTML = document.getElementById(ul_list_number);
            listHTML.innerHTML = `${ul_list}`;
          }
        })
      }
      else {
        lcContainer.style.display = "block";
        noLCfound.style.display = "block";
      }
    });
  }).catch(function(err) {
    console.log('Fetch Error :-S', err);
  });
});

meshNames.addEventListener("click", ()=>{
  meshNames.style.display = "none";
  meshLoading.style.display = "block";
  meshContainer.style.display = "block";

  let xhr = new XMLHttpRequest()
  xhr.responseType = 'json';
  xhr.timeout = 2000;

  xhr.onload = function() {
    if (xhr.status === 200) {
      let meshCounter = 0;
      let mesh = xhr.response;
      if (mesh.length > 0) {
        if (noMesh.style.display === "block") {
          noMesh.style.display = "none";
        }
        let tempArray = [];
        mesh.forEach(function (meshItem) {
          let uri = meshItem.resource.replace("http://", "https://")
          tempArray.push({"heading": meshItem.label, "uri": uri})
        });
        tempArray.forEach(function (arrayItem) {
          fetch(arrayItem.uri + ".json-ld").then(
            function(response) {
              if (response.status === 200) {
                // Examine the text in the response
                response.json().then(function(data) {
                  meshCounter += 1;
                  let ul_list_number = "mesh-ulList-" + meshCounter.toString();
                  let newAccItem = document.createElement("div");
                  newAccItem.classList.add("accordion-item");
                  let ariaExpanded = (meshCounter === 1) ? "true" : "false";
                  let collapsedButtonClass = (meshCounter === 1) ? "accordion-button" : "accordion-button collapsed";
                  let collapsedDivClass = (meshCounter === 1) ? "accordion-collapse collapse show" : "accordion-collapse collapse";
                  newAccItem.innerHTML = `<h2 class="accordion-header" id="mesh-heading-${meshCounter}">
                                            <button class="${collapsedButtonClass}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-mesh-${meshCounter}" aria-expanded="${ariaExpanded}" aria-controls="collapse-mesh-${meshCounter}">${arrayItem.heading}</button>
                                          </h2>
                                          <div id="collapse-mesh-${meshCounter}" class="${collapsedDivClass}" aria-labelledby="mesh-heading-${meshCounter}" data-bs-parent="#accordionMeshNames">
                                            <div class="accordion-body">
                                              <p>MESH URI: <a href="${arrayItem.uri}">${arrayItem.uri}</a></p>
                                              <p>Alternative labels:</p>
                                              <ul id="${ul_list_number}"></ul>
                                              <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#pushModal" data-bs-uri="${arrayItem.uri}" data-bs-heading="${arrayItem.heading}">This is My Match</button>
                                            </div>
                                          </div>`
                  accordionMeshNames.appendChild(newAccItem);
                  if (("altLabel" in data) && (data.altLabel.length > 0)) {
                    let ul_list = "";
                    data.altLabel.forEach(function (altLabelItem) {
                      ul_list += "<li>" + altLabelItem["@value"] + "</li>";
                    });
                    let listHTML = document.getElementById(ul_list_number);
                    listHTML.innerHTML = `${ul_list}`;
                  }
                  else {
                    let listHTML = document.getElementById(ul_list_number);
                    listHTML.innerHTML = `<li>None</li>`;
                  }
                });
              }
            }
          ).catch(function(err) {
            console.log('Fetch Error:', err);
          });
        });
      } else {
        noMesh.style.display = "block";
      }
    }
    else {
      // request error
      console.log('HTTP error:', xhr.status, xhr.statusText);
    }
  };

  xhr.onerror = function() {
    console.log("Request failed");
  };

  let url = "https://id.nlm.nih.gov/mesh/lookup/term?label=" + encodeURIComponent(search) + "&match=exact&limit=10";
  xhr.open("GET", url);
  xhr.send();
  meshLoading.style.display = "none";
})

pushModal.addEventListener('show.bs.modal', function (event) {
  // Button that triggered the modal
  let button = event.relatedTarget
  // Extract info from data-bs-* attributes
  let uri = button.getAttribute('data-bs-uri');
  let heading = button.getAttribute('data-bs-heading');

  let modalChangesText = pushModal.querySelector("#changes");

  modalChangesText.innerHTML = `You are about to change the taxonomy record for <strong>"${search}" (${inputURI})</strong> by connecting it with the URI of external authority entity <strong>"${heading}" (${uri})</strong>. Are you sure you want to do this?`
})

sendPutRequest.addEventListener("click", function (event) {
  var url = "https://httpbin.org/post";

  var xhr = new XMLHttpRequest();
  xhr.open("POST", url);

  xhr.setRequestHeader("Accept", "application/json");
  xhr.setRequestHeader("Content-Type", "application/json");

  xhr.onreadystatechange = function () {
    if (xhr.readyState !== 4) {
      sendPutRequest.style.display = "none";
      pushLoading.style.display = "block";
    }
    else if (xhr.readyState === 4) {
      pushLoading.style.display = "none";
      let modalChangesText = pushModal.querySelector("#changes");
      if (xhr.status === 200) {
        modalChangesText.innerHTML += `<br /><br /><strong>It worked!</strong>`
        closeModal.style.display = "none";
        modalNewSearch.style.display = "block";
        console.log(xhr.status);
        console.log(xhr.responseText);
      }
      else {
        modalChangesText.innerHTML += `<br /><br /><strong>It failed!</strong> Check log!`
        closeModal.style.display = "none";
        modalNewSearch.style.display = "block";
        console.log(xhr.status);
        console.log(xhr.responseText);
      }
    }};

  var data = `{
       "text": "HARMONIZER Debug",
       "blocks": [
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "HARMONIZER"}]},
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": "SUCCESS"}}
       ]
    }`;

  xhr.send(data);
})
