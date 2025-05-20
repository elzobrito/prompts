document.addEventListener('DOMContentLoaded', () => {
    const promptFiles = [
        "F22_Raptor_fighter.json",
        "alice.json",
        "analise_imagem.json",
        "angel.json",
        "aquiles.json",
        "blonde_woman.json",
        "bluble.json",
        "desenho_infantil.json",
        "digital_artwork_featuring_an_Asian.json",
        "iguana.json",
        "jasmine.json",
        "luminous_rose.json",
        "ninja.json",
        "openai_meta.json",
        "portrait_of_a_woman.json",
        "professsorMinerva.json",
        "serenebeach.json",
        "smallfair.json",
        "snow.json",
        "supergirl.json",
        "supergirl2.json",
        "velma.json",
        "vermelho.json",
        "vocabulario.json",
        "warrior_art.json",
        "warrior_female.json",
        "warrior_male.json",
        "woman_rose.json"
    ];

    function populatePromptList() {
        const promptListContainer = document.getElementById('prompt-list-container');
        
        // Clear any existing list items (e.g., the h2 and placeholder comment)
        // We want to replace them with the list itself.
        // A more robust way would be to have a dedicated <ul> element.
        // For now, let's clear and append directly to the container.
        const heading = promptListContainer.querySelector('h2');
        promptListContainer.innerHTML = ''; // Clear existing content
        if (heading) {
            promptListContainer.appendChild(heading); // Re-add the heading
        }

        const ul = document.createElement('ul');
        ul.className = 'space-y-2'; // Add some spacing between list items

        promptFiles.forEach(filename => {
            const li = document.createElement('li');
            li.textContent = filename;
            li.className = 'p-2 hover:bg-gray-200 rounded cursor-pointer'; // Basic styling for items

            li.addEventListener('click', async () => {
                const promptContentContainer = document.getElementById('prompt-content-container');
                // Clear previous content (keeping the H2 heading)
                const heading = promptContentContainer.querySelector('h2');
                promptContentContainer.innerHTML = '';
                if (heading) {
                    promptContentContainer.appendChild(heading);
                }

                try {
                    const response = await fetch(`./${filename}`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const data = await response.json();
                    const prettifiedJson = JSON.stringify(data, null, 2);

                    const pre = document.createElement('pre');
                    pre.textContent = prettifiedJson;
                    // Optional: Add some styling to the pre tag if needed, e.g., for scrolling
                    pre.className = 'bg-gray-50 p-3 rounded text-sm overflow-auto'; 
                    promptContentContainer.appendChild(pre);

                } catch (error) {
                    console.error('Error loading or parsing prompt file:', error);
                    const errorP = document.createElement('p');
                    errorP.textContent = `Error loading ${filename}: ${error.message}`;
                    errorP.className = 'text-red-500';
                    promptContentContainer.appendChild(errorP);
                }
            });
            ul.appendChild(li);
        });
        promptListContainer.appendChild(ul);
    }

    populatePromptList();
});
