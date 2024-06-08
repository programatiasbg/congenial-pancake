const btnGenerator = document.getElementById('btn-generator-blog')

if (btnGenerator) {
    btnGenerator.addEventListener('click', async () => {
        const youtubeLink = document.getElementById('link-youtube').value;
        const blogContent = document.getElementById('blog-content');
        const loadingIndicator = document.getElementById('loading-circle');

        if (youtubeLink) {
            loadingIndicator.classList.add("d-block");
            loadingIndicator.classList.remove("hidden");
            blogContent.innerHTML = ""; // Clear previous content

            const endpointUrl = 'generate-blog';

            try {
                const response = await fetch(endpointUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ link: youtubeLink })
                });

                const data = await response.json();

                blogContent.innerHTML = data.content;

            } catch (error) {
                console.error("Error occurred:", error);
                alert("Something went wrong. Please try again later.");
            }
            document.getElementById('loading-circle').classList.add("hidden");
        } else {
            alert("Please enter a youtube link.");
        }
    })
}
