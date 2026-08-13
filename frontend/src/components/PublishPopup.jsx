import React, { useState } from 'react';
import { playClick } from '../audio';

export default function PublishPopup({ setView, onClose, story }) {
    const [status, setStatus] = useState('idle');
    const [authorName, setAuthorName] = useState('');

    const handlePublish = () => {
        playClick();
        setStatus('publishing');
        
        if (window.APP_ENV === 'dev') {
            setTimeout(() => setStatus('success'), 500);
            return;
        }
        
        fetch('/api/stories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                author: authorName || 'Anonymous',
                content: story.content
            })
        }).then(res => {
            if(res.ok) setStatus('success');
            else setStatus('error');
        }).catch(() => setStatus('error'));
    };

    return (
        <div className="mc-popup">
            {status === 'idle' || status === 'publishing' ? (
                <React.Fragment>
                    <h2>Publish Story</h2>
                    <input type="text" className="mc-input" placeholder="Your Name" value={authorName} onChange={e => setAuthorName(e.target.value)} />
                    <br/>
                    <button className="mc-button" style={{width: '80%', margin: '10px auto'}} disabled={status==='publishing'} onClick={handlePublish}>
                        {status === 'publishing' ? "Publishing..." : "Publish"}
                    </button>
                    <button className="mc-button" style={{width: '80%', margin: '10px auto'}} disabled={status==='publishing'} onClick={onClose}>Cancel</button>
                </React.Fragment>
            ) : status === 'success' ? (
                <React.Fragment>
                    <h2>Success!</h2>
                    <p>Your story has been uploaded.</p>
                    <button className="mc-button" style={{width: '80%', margin: '10px auto'}} onClick={() => { playClick(); setView('home'); }}>Awesome</button>
                </React.Fragment>
            ) : (
                <React.Fragment>
                    <h2>Error</h2>
                    <p>Failed to publish.</p>
                    <button className="mc-button" style={{width: '80%', margin: '10px auto'}} onClick={onClose}>Close</button>
                </React.Fragment>
            )}
        </div>
    );
}
