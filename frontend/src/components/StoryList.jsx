import React, { useState, useEffect } from 'react';
import { playClick } from '../audio';
import { MOCK_STORIES } from '../data';

export default function StoryList({ setView, setCurrentStory }) {
    const [stories, setStories] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (window.APP_ENV === 'dev') {
            setStories(MOCK_STORIES);
            setLoading(false);
            return;
        }
        fetch('/api/stories')
            .then(res => res.json())
            .then(data => {
                setStories(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    return (
        <div className="list-container" style={{padding: '25px'}}>
            <h2 style={{textAlign: 'center', color: 'white', margin: '0 0 10px 0'}}>Community Stories</h2>
            <button className="mc-button" style={{width: '80%', maxWidth: '800px', margin: '0 auto 20px', display: 'block'}} onClick={() => { playClick(); setView('home'); }}>Back</button>
            <div style={{maxHeight: '400px', overflowY: 'auto', paddingRight: '10px'}}>
                {loading ? <div style={{textAlign:'center', color:'white'}}>Loading...</div> : stories.length === 0 ? <div style={{textAlign:'center', color:'white'}}>No stories yet.</div> : stories.map(story => {
                    const preview = story.content.replace(/\n/g, ' ').substring(0, 80) + "...";
                    return (
                        <div key={story.id} className="list-item" style={{padding: '5px 0'}} onClick={() => { playClick(); setCurrentStory(story); setView('detail'); }}>
                            <div className="list-item-title" style={{fontSize: '1.1rem', display: 'flex', justifyContent: 'space-between'}}>
                                <span>{story.author}</span>
                                <span><span style={{position: 'relative', top: '-13px', fontSize: '0.9em'}}>★</span> {story.avg_rating || 0}</span>
                            </div>
                            <div className="list-item-preview" style={{fontSize: '0.9rem'}}>{preview}</div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
