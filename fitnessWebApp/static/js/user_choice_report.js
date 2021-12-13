const btns = document.querySelectorAll('button');

//default report is calories
var activity = 'calories';

btns.forEach(btn => {
    //make the button an event that changes the activity on press
    btn.addEventListener('click', e => {
        activity = e.target.dataset.macro

        btns.forEach(btn => btn.classList.remove('active'))
        e.target.classList.add('active');

        //update the graph when button was pressed in graph report
        update(all_macros_calories);
    })
})