function createPost(url, postValues) {
    let post = fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json;charset=utf-8'
            },
            body: JSON.stringify(postValues)
        }
    );
    return post.then(res => res.json());
}

function stopDownload(event){
    const parentNode = event.currentTarget.parentNode
    let url = parentNode.dataset.url;
    parentNode.classList.add("removing")
    console.log("Deleting url: " + url)
    createPost('/delete', url)
        .then(resp => {
            console.log(resp)
            if(resp.success) {
                parentNode.remove()
            } else {
                console.log("Cannot delete the requested element")
                parentNode.classList.remove("removing")
            }

        });
}

function restartDownload(event) {
    const parentNode = event.currentTarget.parentNode
    let url = parentNode.dataset.url;
    parentNode.classList.add("new");
    console.log("Restoring url: " + url)
    createPost('/restore', url)
        .then(resp => {
            console.log(resp)
            if(resp.success) {
                parentNode.remove()
            } else {
                console.log("Cannot re-add the requested element")
                parentNode.classList.remove("new")
            }
        });
}

/**
 *
 * @param {HTMLElement} parentElement Creates the button to restart a download
 */
function restartDownloadListener(parentElement) {
    let queue = parentElement.dataset.queue;
    if (queue && queue === "downloadFailed") {
        //Create button
        let button = document.createElement("i");
        button.append(document.createTextNode("🔄"));
        button.classList.add("action_button", "restart_download")
        //Add listener
        button.addEventListener("click", restartDownload, false);
        //Insert in DOM
        parentElement.insertBefore(button, parentElement.children[1])
    }
}

window.addEventListener('load', (event) => {
    // Add event listener to all elements
    const lines = document.getElementsByClassName("stop_download");
    for (const line of lines) {
        console.log("Adding event listener to stop download");
        line.addEventListener("click", stopDownload, false);
        restartDownloadListener(line.parentElement);
    }
    if (!lines) {
        console.error("No lines found");
    }
});

