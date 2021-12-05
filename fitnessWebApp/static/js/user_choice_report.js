const btns = document.querySelectorAll('button');

var activity = 'calories';

btns.forEach(btn => {
    btn.addEventListener('click', e => {
        activity = e.target.dataset.macro

        btns.forEach(btn => btn.classList.remove('active'))
        e.target.classList.add('active');

        update(array_data);
    })
})