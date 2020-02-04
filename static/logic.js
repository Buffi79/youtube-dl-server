function load() {
   document.querySelectorAll('[data-selected]').forEach(e => {
     e.value = e.dataset.selected
   });
}
window.onload = load;

function replayButton() {     
    document.youdlfrom.submit();
} 
