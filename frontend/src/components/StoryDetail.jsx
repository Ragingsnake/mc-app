import React, { useState } from 'react';
import { playClick } from '../audio';

export default function StoryDetail({ setView, story }) {
    const [name, setName] = useState('');
    const [commentText, setCommentText] = useState('');
    const [rating, setRating] = useState(5);
    const [isSubmitting, setIsSubmitting] = useState(false);
    
    // Create a local copy to append comments optimistically
    const [localComments, setLocalComments] = useState(story ? story.comments : []);

    if (!story) return null;

    const formatText = (text) => text.split('\n').map((str, idx) => <React.Fragment key={idx}>{str}<br/></React.Fragment>);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!name || !commentText) return;
        playClick();
        setIsSubmitting(true);

        const commentPayload = { user: name, text: commentText, rating: parseInt(rating) };

        if (window.APP_ENV === 'dev') {
            setLocalComments([...localComments, commentPayload]);
            setName('');
            setCommentText('');
            setRating(5);
            setIsSubmitting(false);
            return;
        }

        // We fire both endpoints simultaneously since rate updates average and comment saves text
        Promise.all([
            fetch(`/api/stories/${story.id}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(commentPayload)
            }),
            fetch(`/api/stories/${story.id}/rate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rating: parseInt(rating) })
            })
        ]).then(() => {
            setLocalComments([...localComments, commentPayload]);
            setName('');
            setCommentText('');
            setRating(5);
            setIsSubmitting(false);
        }).catch(err => {
            console.error(err);
            setIsSubmitting(false);
        });
    };

    return (
        <React.Fragment>
            <div className="story-box" style={{marginTop:'10px', fontSize: '1.1rem', minHeight: '300px', maxHeight: '50vh', overflowY: 'auto', padding: '15px'}}>
                <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #555', paddingBottom: '5px', marginBottom: '10px'}}>
                    <span style={{color: '#ffff55'}}>By: {story.author}</span>
                    <span style={{color: '#ffff55'}}><span style={{position: 'relative', top: '-13px', fontSize: '0.9em'}}>★</span> {story.avg_rating}</span>
                </div>
                <div>{formatText(story.content)}</div>
            </div>
            
            <div style={{width: '75%', maxWidth: '750px', background: 'rgba(0,0,0,0.8)', border: '2px solid #3b3b3b', padding: '15px', marginBottom: '15px', display: 'flex', flexDirection: 'column'}}>
                <h3 style={{margin: '0 0 10px 0', fontSize: '1.3rem', color: '#ffffa0', borderBottom: '2px solid #555', paddingBottom: '5px'}}>Comments</h3>
                
                <div style={{fontSize: '0.9rem', maxHeight: '25vh', overflowY: 'auto', marginBottom: '10px'}}>
                    {localComments.length > 0 ? localComments.map((c, i) => (
                        <div key={i} style={{borderBottom: '1px solid #444', padding: '8px 0', display: 'flex', alignItems: 'center', gap: '5px'}}>
                            <strong style={{color: '#ffff55'}}>{c.user}</strong> <span style={{fontSize: '0.8em', color: '#aaa'}}>(<span style={{position: 'relative', top: '-10px'}}>★</span> {c.rating || 5})</span>: <span>{c.text}</span>
                        </div>
                    )) : <div style={{color: '#aaa', fontStyle: 'italic'}}>No comments yet.</div>}
                </div>

                <form onSubmit={handleSubmit} style={{display: 'flex', flexDirection: 'column', gap: '10px', borderTop: '2px solid #555', paddingTop: '10px'}}>
                    <div style={{display: 'flex', gap: '10px', alignItems: 'stretch'}}>
                        <input type="text" className="mc-input" placeholder="Your Name" value={name} onChange={e => setName(e.target.value)} style={{flex: 1, padding: '8px', margin: 0, fontSize: '0.9rem'}} />
                        <select className="mc-input" value={rating} onChange={e => setRating(e.target.value)} style={{width: '100px', padding: '8px', margin: 0, fontSize: '0.9rem'}}>
                            <option value="5">5</option>
                            <option value="4">4</option>
                            <option value="3">3</option>
                            <option value="2">2</option>
                            <option value="1">1</option>
                        </select>
                    </div>
                    <div style={{display: 'flex', gap: '10px', alignItems: 'stretch'}}>
                        <input type="text" className="mc-input" placeholder="Write a comment..." value={commentText} onChange={e => setCommentText(e.target.value)} style={{flex: 1, padding: '8px', margin: 0, fontSize: '0.9rem'}} />
                        <button type="submit" className="mc-button" disabled={isSubmitting} style={{width: '120px', margin: 0, padding: '8px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{isSubmitting ? '...' : 'Comment'}</button>
                    </div>
                </form>
            </div>

            <button className="mc-button" style={{width: '75%', maxWidth: '750px', margin: '0'}} onClick={() => { playClick(); setView('list'); }}>Back to List</button>
        </React.Fragment>
    );
}
