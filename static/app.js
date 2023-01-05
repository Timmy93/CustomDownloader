function stopDownload(event){
    const parentNode = event.currentTarget.parentNode
    let url = parentNode.dataset.url;
    parentNode.classList.add("removing")
    console.log("Deleting url: " + url)
    let response = fetch('/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8'
        },
        body: JSON.stringify(url)}
    )
    response.then(res => {
        //Parse response
        res.json().then( resp => {
            console.log(resp)
            if(resp.success) {
                parentNode.remove()
            } else {
                console.log("Cannot delete the requested element")
                parentNode.classList.remove("removing")
            }

        })
    })
}

window.addEventListener('load', (event) => {
    // Add event listener to all elements
    const lines = document.getElementsByClassName("stop_download");
    for (const line of lines) {
        console.log("Adding event listener");
        line.addEventListener("click", stopDownload, false);
    }
    if (!lines) {
        console.error("No lines found");
    }
});

