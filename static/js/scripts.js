function openTab(tabId, element) {
    // Get all elements with class="tab-content" and hide them
    const tabContents = document.getElementsByClassName('tab-content');
    for (let i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
        tabContents[i].classList.remove('active');
    }

    // Get all elements with class="tab-button" and remove the class "active"
    const tabButtons = document.getElementsByClassName('tab-button');
    for (let i = 0; i < tabButtons.length; i++) {
        tabButtons[i].classList.remove('active');
    }

    // Show the current tab, and add an "active" class to the button that opened the tab
    document.getElementById(tabId).style.display = "block";
    document.getElementById(tabId).classList.add('active');
    element.classList.add('active');
}

// Initialize the first tab as active
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('offline-tab').style.display = "block";
});

// const form = document.getElementById('realtime-tab');

// form.addEventListener('submit', (event) => {
//   event.preventDefault(); // Prevent default form submission behavior

//   const text1 = document.getElementById('midiin').value;
//   const text2 = document.getElementById('midiout').value;

//   // Prepare the data to send (can be JSON or form data)
//   const data = { text1, text2 }; // Example using an object

//   fetch('/realtime', { // Replace '/submit' with your actual route
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json' // Set content type for JSON data
//     },
//     body: JSON.stringify(data) // Convert data to JSON string
//   })
//   .then(response => response.json()) // Parse response as JSON
//   .then(data => {
//     console.log('Success:', data); // Handle successful response
//   })
//   .catch(error => {
//     console.error('Error:', error); // Handle errors
//   });
// });