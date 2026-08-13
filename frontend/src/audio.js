export function playClick() {
    const snd = document.getElementById('snd-click');
    if(snd) {
        snd.currentTime = 0;
        snd.play().catch(e => {}); 
    }
}

export function playBGM() {
    const snd = document.getElementById('snd-bgm');
    if(snd) {
        snd.volume = 0.1;
        snd.play().catch(e => {});
    }
}

export function initAudio() {
    const bgm = document.getElementById('snd-bgm');
    if (bgm) bgm.volume = 0.1;
}
