const deleters = document.querySelectorAll(".deleter");

deleters.forEach(item => {
  item.addEventListener('click', event => {
    let user = item.getAttribute('data-user');
    let job_id = item.getAttribute('data-job_id');

    let xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.timeout = 5000;
    xhr.open("POST", "https://harmonizer.lib.asu.edu/subspace/delete_job");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    xhr.onload = function() {
      if (xhr.status === 200) {
        window.location.href = 'https://harmonizer.lib.asu.edu/my-jobs';
      }
      else {
        // request error
        window.alert("This is awkward, but your delete request failed.");
        console.log('HTTP error:', xhr.status, xhr.statusText);
      }
    };
    xhr.onerror = function() {
      window.alert("This is awkward, but your delete request failed.");
      console.log('HTTP error:', xhr.status, xhr.statusText);
    };
    let payload = {
        "user": user,
        "job_id": job_id
    };
    xhr.send(JSON.stringify(payload));
  })
})
