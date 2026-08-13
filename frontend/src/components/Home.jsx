import React, { useMemo } from 'react';
import { splashTexts } from '../data';
import { playClick, playBGM } from '../audio';

export default function Home({ setView }) {
    const randomSplash = useMemo(() => splashTexts[Math.floor(Math.random() * splashTexts.length)], []);

    return (
        <React.Fragment>
            <div className="logo-container">
                <img src="/minecraft_logo.png" alt="Minecraft" className="mc-logo" />
                <div className="splash-text">{randomSplash}</div>
            </div>
            <div className="button-group">
                <button className="mc-button" onClick={() => { playClick(); playBGM(); setView('play'); }}>Play</button>
                <button className="mc-button" onClick={() => { playClick(); setView('list'); }}>View Others Story</button>
            </div>
        </React.Fragment>
    );
}
