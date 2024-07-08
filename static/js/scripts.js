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

    for (let i = 0; i < tabButtons.length; i++) {
        console.log("xtab buttons",tabButtons[i]);
    }

}

// Initialize the first tab as active
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('offline-tab').style.display = "block";

    const startButton = document.getElementById('start-btn');
    const stopButton = document.getElementById('stop-btn');
    const messageElement = document.getElementById('message');
  

    function startRealTime() {
        console.log("startRealTime starting")
        const midiIn = document.getElementById('midiin').value;
        const midiOut = document.getElementById('midiout').value;
    
        fetch('/realtime', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ action:'Start' , midiin: midiIn, midiout: midiOut }),
        })
          .then((response) => {
            if (response.ok) {
              messageElement.innerText = 'Real-time processing started successfully!';
              messageElement.style.display = 'block';
              toggleButtons();
            } else {
              throw new Error('Failed to start real-time processing');
            }
          })
          .catch((error) => {
            console.error('Error:', error);
          });
      }
    
    function stopRealTime() {
        fetch('/realtime', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            },
            body: JSON.stringify({ action:'Stop' }),
        })
        .then((response) => {
            if (response.ok) {
                messageElement.innerText = 'Real-time processing stopped!';
                messageElement.style.display = 'block';
                toggleButtons();
            } else {
                throw new Error('Failed to stop real-time processing');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
        
        toggleButtons();
    }

    function toggleButtons() {
        console.log('buttons will toggle. now:',startButton.disabled,stopButton.disabled)
        startButton.disabled = !startButton.disabled;
        stopButton.disabled = !stopButton.disabled;
    }

    startButton.addEventListener('click', startRealTime);
    stopButton.addEventListener('click', stopRealTime);
    console.log("start stop situation",startButton.disabled,stopButton.disabled)
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



// document.getElementById('realtime-form').addEventListener('submit', function (event) {
//     event.preventDefault();

//     const formData = new FormData(event.target);
//     const action = formData.get('submit');
//     console.log("action",action);
//     fetch('/realtime', {    
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({ action: action })
//     })
//     .then(response => response.json())
//     .then(data => {
//         console.log("received data",data)
//         if (data.status === 'success') {
//             document.getElementById('stop-button').disabled = false;
//             document.querySelector('input[name="submit"]').disabled = true;
//             openTab('realtime-tab', document.querySelector('.tab-button.active'));
//         }
//     })
//     .catch(error => console.error('Error:', error));
// });